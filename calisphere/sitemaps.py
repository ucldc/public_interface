from builtins import object
import re
import time
import math

from django.contrib.sitemaps import Sitemap
from django.apps import apps
from django.urls import reverse
from django.conf import settings

from exhibits.models import *

from calisphere.collection_data import CollectionManager

from .cache_retry import SOLR_select_nocache

app = apps.get_app_config('calisphere')


class HttpsSitemap(Sitemap):
    protocol = 'https'


class StaticSitemap(HttpsSitemap):
    def items(self):
        return [
            'calisphere:collectionsDirectory',
            'calisphere:about',
            'calisphere:help',
            'calisphere:termsOfUse',
            'calisphere:privacyStatement',
            'calisphere:outreach',
            'calisphere:contribute',
        ]

    def location(self, item):
        return reverse(item)


class InstitutionSitemap(HttpsSitemap):
    def items(self):
        return list(app.registry.repository_data.keys())

    def location(self, item):
        return reverse(
            'calisphere:repositoryCollections',
            kwargs={
                'repository_id': item,
            })


class CollectionSitemap(HttpsSitemap):
    def items(self):
        return CollectionManager().parsed

    def location(self, item):
        return reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': item.id})


class ItemSitemap(object):
    '''
        class for generating Calisphere item sitemaps in conjunction with
        calisphere.sitemap_generator, which is a subclass of django-static-sitemaps
        (https://github.com/xaralis/django-static-sitemaps)

        Note that this is not a subclass of django.contrib.sitemaps.Sitemap

        Use a generator of solr results rather than a list, which is too memory intensive.
    '''

    def __init__(self, collection_url):
        self.limit = 15000  # 50,000 is google limit on urls per sitemap file
        self.collection_filter = 'collection_url: "' + collection_url + '"'
        self.solr_total = SOLR_select_nocache(q='', fq=[self.collection_filter]).numFound
        self.num_pages = math.ceil(self.solr_total / self.limit)

    def items(self):
        ''' returns a generator containing data for all items in solr '''
        # https://github.com/ucldc/extent_stats/blob/master/calisphere_arks.py
        base_query = {
            'q': '',
            'fl': 'id,reference_image_md5,timestamp',  # fl = field list
            'fq': [self.collection_filter],
            'rows': 1000,
            'sort': 'score desc,id desc',
        }

        data_iter = self.get_iter(base_query)

        return data_iter

    def location(self, item):
        return reverse('calisphere:itemView', kwargs={'item_id': item})

    def get_iter(self, params):
        nextCursorMark = '*'
        while True:
            solr_page = self.get_solr_page(params, nextCursorMark)

            if len(solr_page.results) == 0:
                break
            for item in solr_page.results:
                yield {
                    'id': item.get('id'),
                    'reference_image_md5': item.get('reference_image_md5'),
                    'timestamp': item.get('timestamp')
                }

            nextCursorMark = solr_page.nextCursorMark

    def get_solr_page(self, params, cursor='*', sleepiness=1):
        params.update({'cursorMark': cursor})
        t1 = time.time()
        solr_search = SOLR_select_nocache(**params)
        nap = (time.time() - t1) * sleepiness
        time.sleep(nap)
        return solr_search


class ExhibitSitemap(HttpsSitemap):
    def items(self):
        return Exhibit.objects.filter(publish=True).order_by('title')


class HistoricalEssaySitemap(HttpsSitemap):
    def items(self):
        return HistoricalEssay.objects.filter(publish=True).order_by('title')


class LessonPlanSitemap(HttpsSitemap):
    def items(self):
        return LessonPlan.objects.filter(publish=True).order_by('title')


class ThemeSitemap(HttpsSitemap):
    def items(self):
        return Theme.objects.filter(publish=True).order_by('title')

