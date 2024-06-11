from builtins import object
import re
import time
import math
import json

from django.contrib.sitemaps import Sitemap
from django.apps import apps
from django.urls import reverse
from django.conf import settings
from elasticsearch import Elasticsearch

from exhibits.models import *

from calisphere.collection_data import CollectionManager

from .cache_retry import SOLR_select_nocache

app = apps.get_app_config('calisphere')

if settings.ES_HOST and settings.ES_USER and settings.ES_PASS:
    elastic_client = Elasticsearch(
        hosts=[settings.ES_HOST],
        http_auth=(settings.ES_USER, settings.ES_PASS))

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
        if settings.ES_HOST:
            return CollectionManager("es").parsed
        else:
            return CollectionManager("solr").parsed

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

    def __init__(self, collection_id):
        self.limit = 15000  # 50,000 is google limit on urls per sitemap file

        if settings.ES_HOST:
            self.collection_id = collection_id
            self.collection_filter = {"match": {"collection_id": collection_id}}
            self.indexed_item_count = elastic_client.count(
                index=settings.ES_ALIAS,
                body=json.dumps({"query": self.collection_filter})
            )['count']
            self.query_context = {
                "query": self.collection_filter,
                "_source": ["thumbnail"],
                "track_total_hits": True,
                "size": 1000,
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"_id": {"order": "desc"}}
                ]
            }
        else:
            self.collection_filter = 'collection_url: "' + collection_id + '"'
            self.indexed_item_count = SOLR_select_nocache(q='', fq=[self.collection_filter]).numFound
            self.query_context = {
                'q': '',
                'fl': 'id,reference_image_md5,timestamp',  # fl = field list
                'fq': [self.collection_filter],
                'rows': 1000,
                'sort': 'score desc,id desc',
            }

        self.num_pages = math.ceil(self.indexed_item_count / self.limit)

    def items(self):
        ''' returns a generator containing data for all items in solr '''
        # https://github.com/ucldc/extent_stats/blob/master/calisphere_arks.py
        if settings.ES_HOST:
            return self.scroll_opensearch(self.query_context)
        else:
            return self.paginate_solr(self.query_context)

    def location(self, item):
        return reverse('calisphere:itemView', kwargs={'item_id': item})

    def scroll_opensearch(self, body):
        resp = elastic_client.search(
            index=settings.ES_ALIAS,
            body=json.dumps(body),
            params={"scroll": "1m"}
        )

        scroll_id = resp['_scroll_id']
        hits = resp['hits']['hits']

        total_hits = resp['hits']['total']['value']
        progress = len(hits)

        while len(hits):
            for hit in hits:
                thumb_path = hit['_source'].get('thumbnail', {}).get('path', '')
                thumb_path = thumb_path.split('/thumbnails/')[-1]
                index_date = hit['_index'].split('-')[-1]
                index_date = re.sub(
                    r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})',
                    r'\1-\2-\3T\4:\5:\6',
                    index_date
                )

                yield {
                    'id': hit['_id'],
                    'reference_image_md5': thumb_path,
                    'timestamp': index_date
                }

            print(f"[{self.collection_id}]: {progress}/{total_hits} [requesting {scroll_id}]")
            resp = elastic_client.scroll(scroll_id=scroll_id, scroll='1m')
            scroll_id = resp['_scroll_id']
            hits = resp['hits']['hits']
            progress += len(hits)

    def paginate_solr(self, params):
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

