from future import standard_library
from functools import reduce
standard_library.install_aliases()
from builtins import range
from django.apps import apps
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import Http404, JsonResponse, HttpResponse, QueryDict
from calisphere.collection_data import CollectionManager
from .constants import *
from .facet_filter_type import getCollectionData, getRepositoryData, FacetFilterType
from .cache_retry import SOLR_select, SOLR_raw, json_loads_url
from static_sitemaps.util import _lazy_load
from static_sitemaps import conf
from requests.exceptions import HTTPError
from django.core.exceptions import ObjectDoesNotExist
from exhibits.models import ExhibitItem, Exhibit
from django.template.defaultfilters import pluralize
from .views import solr_escape, searchDefaults, solrEncode, facetQuery, getCollectionMosaic


import os
import operator
import math
import re
import copy
import simplejson as json
import string
import urllib.parse

def collectionsDirectory(request):
    solr_collections = CollectionManager(settings.SOLR_URL,
                                         settings.SOLR_API_KEY)
    collections = []

    page = int(request.GET['page']) if 'page' in request.GET else 1

    for collection_link in solr_collections.shuffled[(page - 1) * 10:page *
                                                     10]:
        collections.append(getCollectionMosaic(collection_link.url))

    context = {
        'meta_robots': None,
        'collections': collections,
        'random': True,
        'pages': int(
            math.ceil(len(solr_collections.shuffled) / 10))
    }

    if page * 10 < len(solr_collections.shuffled):
        context['next_page'] = page + 1
    if page - 1 > 0:
        context['prev_page'] = page - 1

    return render(request, 'calisphere/collections/collectionsRandomExplore.html', context)


def collectionsAZ(request, collection_letter):
    solr_collections = CollectionManager(settings.SOLR_URL,
                                         settings.SOLR_API_KEY)
    collections_list = solr_collections.split[collection_letter.lower()]

    page = int(request.GET['page']) if 'page' in request.GET else 1
    pages = int(math.ceil(len(collections_list) / 10))

    collections = []
    for collection_link in collections_list[(page - 1) * 10:page * 10]:
        collections.append(getCollectionMosaic(collection_link.url))

    alphabet = list((character, True if character.lower() not in
                     solr_collections.no_collections else False)
                    for character in list(string.ascii_uppercase))

    context = {
        'collections': collections,
        'alphabet': alphabet,
        'collection_letter': collection_letter,
        'page': page,
        'pages': pages,
        'random': None,
    }

    if page * 10 < len(collections_list):
        context['next_page'] = page + 1
    if page - 1 > 0:
        context['prev_page'] = page - 1

    return render(request, 'calisphere/collections/collectionsAZ.html', context)


def collectionsTitles(request):
    '''create JSON/data for the collections search page'''

    def djangoize(uri):
        '''turn registry URI into URL on django site'''
        collection_id = uri.split(
            'https://registry.cdlib.org/api/v1/collection/', 1)[1][:-1]
        return reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id})

    collections = CollectionManager(settings.SOLR_URL, settings.SOLR_API_KEY)
    data = [{
        'uri': djangoize(uri),
        'title': title
    } for (uri, title) in collections.parsed]
    return JsonResponse(data, safe=False)


def collectionsSearch(request):
    return render(request, 'calisphere/collections/collectionsTitleSearch.html', {
        'collections': [],
        'collection_q': True
    })


class Collection(object):

    def __init__(self, collection_id):
        self.id = collection_id
        self.url = f"https://registry.cdlib.org/api/v1/collection/{collection_id}/"
        self.details = json_loads_url(f"{self.url}?format=json")
        if not self.details:
            raise Http404(f"{collection_id} does not exist.")

        for repo in self.details.get('repository'):
            repo['resource_id'] = repo.get('resource_uri').split('/')[-2]

    def get_custom_facets(self):
        if hasattr(self, 'custom_facets'):
            return self.custom_facets
        else:
            self.custom_facets = []
            if self.details.get('custom_facet'):
                for custom_facet in self.details.get('custom_facet'):
                    self.custom_facets.append(
                        FacetFilterType(
                            custom_facet['facet_field'],
                            custom_facet['label'],
                            custom_facet['facet_field'],
                            custom_facet.get('sort_by', 'count')
                        )
                    )
            return self.custom_facets

    def get_summary_data(self):
        if hasattr(self, 'summary'):
            return self.summary

        summary_url = os.path.join(
            settings.UCLDC_METADATA_SUMMARY,
            '{}.json'.format(self.id),
        )
        self.summary = json_loads_url(summary_url)
        if not self.summary:
            raise Http404(f"{self.id} does not exist")

        self.item_count = self.summary['item_count']
        return self.summary

    def get_item_count(self):
        if hasattr(self, 'item_count'):
            return self.item_count

        self.get_summary_data()
        return self.item_count

    def _field_non_unique(self, k,v):
        if k == 'item_count' or k == 'collection_url':
            return False
        if k == 'description' or k == 'transcription':
            return False
        if v['percent'] == 0:
            return False
        if v['uniq_percent'] == 100:
            return False
        return True

    def get_facet_sets(self):
        if hasattr(self, 'summary'):
            summary_data = self.summary
        else:
            summary_data = self.get_summary_data()

        non_unique_fields = [ dict({'field': k}, **v) 
            for k,v in summary_data.items() 
            if self._field_non_unique(k,v) ]
        non_unique_fields.sort(key=lambda x: x['uniq_percent'], reverse=True)

        facet_sets = [self.get_facets(field['field']) 
            for field in non_unique_fields]

        # double check non-uniqueness based on solr data, rather than summary_data
        # here's an example of why this is necessary:
        # http://calisphere-test.cdlib.org/collections/10318/metadata/ look at 'type' and 'rights'
        non_unique_facet_sets = [facet_set for facet_set in facet_sets 
            if (facet_set and len(facet_set['values']) > 1)]
        facet_sets = non_unique_facet_sets

        return facet_sets

    def get_facets(self, facet_field):
        # facet=true&facet.query=*&rows=0&facet.field=title_ss&facet.pivot=title_ss,collection_data"
        solrParams = {
            'facet': 'true',
            'rows': 0,
            'facet_field': '{}_ss'.format(facet_field),
            'fq': 'collection_url:"{}"'.format(self.url),
            'facet_limit': '-1',
            'facet_mincount': 1,
            'facet_sort': 'count',
        }
        solr_search = SOLR_select(**solrParams)

        values = solr_search.facet_counts.get('facet_fields').get('{}_ss'.format(facet_field))
        if not values:
            return None

        unique = len(values)
        records = sum(values.values())

        values = [{'label': k, 'count': v, 'uri': reverse(
            'calisphere:collectionFacetValue',
            kwargs={
                'collection_id': self.id,
                'cluster': facet_field,
                'cluster_value': urllib.parse.quote_plus(k),
            })} for k,v in values.items()]

        return {
            'facet_field': facet_field,
            'records': records,
            'unique': unique,
            'values': values
        }


def collectionSearch(request, collection_id):
    collection = Collection(collection_id)

    params = request.GET.copy()
    context = searchDefaults(params)

    # Collection Views don't allow filtering or faceting by collection_data or repository_data
    facet_filter_types = [
        facet_filter_type for facet_filter_type in FACET_FILTER_TYPES
        if facet_filter_type['facet'] != 'collection_data'
        and facet_filter_type['facet'] != 'repository_data'
    ]
    # Add Custom Facet Filter Types
    facet_filter_types = facet_filter_types + collection.get_custom_facets()
    # If relation_ss is not already defined as a custom facet, and is included 
    # in search parameters, add the relation_ss facet implicitly
    if not collection.get_custom_facets():
        if params.get('relation_ss'):
            facet_filter_types.append(
                FacetFilterType(
                    'relation_ss',
                    'Relation',
                    'relation_ss',
                    'value',
                    faceting_allowed = False
                )
            )

    extra_filter = 'collection_url: "' + collection.url + '"'

    # perform the search
    solrParams = solrEncode(params, facet_filter_types)
    solrParams['fq'].append(extra_filter)
    solr_search = SOLR_select(**solrParams)
    context['search_results'] = solr_search.results
    context['numFound'] = solr_search.numFound
    total_items = SOLR_select(**{**solrParams, **{
        'q': '',
        'fq': [extra_filter],
        'rows': 0,
        'facet': 'false'
    }})

    context['pages'] = int(
        math.ceil(solr_search.numFound / int(context['rows'])))

    context['facets'] = facetQuery(facet_filter_types, params, solr_search,
                                   extra_filter)

    context['filters'] = {}
    for filter_type in facet_filter_types:
        param_name = filter_type['facet']
        display_name = filter_type['filter']
        filter_transform = filter_type['filter_display']

        if len(params.getlist(param_name)) > 0:
            context['filters'][display_name] = list(
                map(filter_transform, params.getlist(param_name)))

    context.update({
        'browse': collection.get_facet_sets(),
        'meta_robots': None,
        'totalNumItems':
        total_items.numFound,
        'FACET_FILTER_TYPES':
        facet_filter_types,
        'collection':
        collection.details,
        'collection_id':
        collection_id,
        'form_action':
        reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    })

    return render(request, 'calisphere/collections/collectionView.html', context)


def collectionFacet(request, collection_id, facet):
    collection = Collection(collection_id)
    if not facet in UCLDC_SCHEMA_FACETS:
        raise Http404("{} does not exist".format(facet))

    params = request.GET.copy()
    context = searchDefaults(params)
    if not params.get('view_format'):
        context['view_format'] = 'list'

    context.update({'facet': facet,})
    facets = collection.get_facets(facet)
    values = facets['values']
    if not values:
        raise Http404("{0} has no values".format(facet))

    if params.get('sort') == 'smallestFirst':
        values.reverse()
    if params.get('sort') == 'az':
        values.sort(key=lambda v: v['label'])
    if params.get('sort') == 'za':
        values.sort(key=lambda v: v['label'], reverse=True)

    if context.get('view_format') == 'grid':
        values = values[0:25]
        for value in values:
            escaped_cluster_value = solr_escape(value['label'])
            thumbParams = {
                'facet': 'false',
                'rows': 4,
                'fl': 'reference_image_md5',
                'fq':
                    [f'collection_url: "{collection.url}"', f'{facet}_ss: "{escaped_cluster_value}"']
            }
            solr_thumbs = SOLR_select(**thumbParams)
            value['thumbnails'] = [result['reference_image_md5'] for result in solr_thumbs.results]

    context.update({
        'values': values, 
        'unique': facets['unique'], 
        'records': facets['records'], 
        'ratio': round((facets['unique'] / facets['records']) * 100, 2)
    })

    context.update({
        'title': f"{facet.capitalize()}{pluralize(values)} Used in {collection.details['name']}",
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection.details,
        'collection_id': collection_id,
        'form_action': reverse(
            'calisphere:collectionFacet',
            kwargs={'collection_id': collection_id, 'facet': facet}),
    })

    context.update({
        'item_count': collection.get_item_count(), 
        'clusters': collection.get_facet_sets()
    })

    return render(request, 'calisphere/collections/collectionFacet.html', context )

def collectionFacetJson(request, collection_id, facet):
    if not facet in UCLDC_SCHEMA_FACETS:
        raise Http404("{} does not exist".format(facet))

    collection = Collection(collection_id)
    facets = collection.get_facets(facet)
    if not facets:
        raise Http404("{0} has no values".format(facet))

    return JsonResponse(facets['values'], safe=False)


def collectionFacetValue(request, collection_id, cluster, cluster_value):
    collection = Collection(collection_id)

    if not cluster in UCLDC_SCHEMA_FACETS:
        raise Http404("{} does not exist".format(cluster))

    params = request.GET.copy()

    parsed_cluster_value = urllib.parse.unquote_plus(cluster_value)
    escaped_cluster_value = solr_escape(parsed_cluster_value)
    params.update({'fq': f"{cluster}_ss:\"{escaped_cluster_value}\""})

    context = searchDefaults(params)

    # Collection Views don't allow filtering or faceting by collection_data or repository_data
    facet_filter_types = [
        facet_filter_type for facet_filter_type in FACET_FILTER_TYPES
        if facet_filter_type['facet'] != 'collection_data'
        and facet_filter_type['facet'] != 'repository_data'
    ]

    extra_filter = 'collection_url: "' + collection.url + '"'

    # perform the search
    solrParams = solrEncode(params, facet_filter_types)
    solrParams['fq'].append(extra_filter)
    solr_search = SOLR_select(**solrParams)
    context['search_results'] = solr_search.results
    context['numFound'] = solr_search.numFound
    total_items = SOLR_select(**{**solrParams, **{
        'q': '',
        'fq': [extra_filter],
        'rows': 0,
        'facet': 'false'
    }})

    context['pages'] = int(
        math.ceil(solr_search.numFound / int(context['rows'])))

    context['facets'] = facetQuery(facet_filter_types, params, solr_search,
                                  extra_filter)

    context['filters'] = {}
    for filter_type in facet_filter_types:
        param_name = filter_type['facet']
        display_name = filter_type['filter']
        filter_transform = filter_type['filter_display']

        if len(params.getlist(param_name)) > 0:
            context['filters'][display_name] = list(
                map(filter_transform, params.getlist(param_name)))

    collection_name = collection.details.get('name')
    context.update({'cluster': cluster,})
    context.update({'cluster_value': parsed_cluster_value,})
    context.update({
        'meta_robots': "noindex,nofollow",
        'totalNumItems': total_items.numFound,
        'FACET_FILTER_TYPES': facet_filter_types,
        'collection': collection.details,
        'collection_id': collection_id,
        'title': f"{cluster}: {parsed_cluster_value} ({solr_search.numFound} items) from: {collection_name}",
        'description': None,
        'solrParams': solrParams,
        'form_action': reverse(
            'calisphere:collectionFacetValue',
            kwargs={
              'collection_id': collection_id,
              'cluster': cluster,
              'cluster_value': cluster_value,
            }),
    })

    return render(request, 'calisphere/collections/collectionFacetValue.html', context )


def collectionMetadata(request, collection_id):
    collection = Collection(collection_id)
    summary_data = collection.get_summary_data()

    params = request.GET.copy()
    context = searchDefaults(params)
    context = {
        'title': f"Metadata report for {collection.details['name']}",
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection.details,
        'collection_id': collection_id,
        'summary_data': summary_data,
        'UCLDC_SCHEMA_FACETS': UCLDC_SCHEMA_FACETS,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(request, 'calisphere/collections/collectionMetadata.html', context)

def getClusterThumbnails(collection_url, facet, facetValue):
    escaped_cluster_value = solr_escape(facetValue)
    thumbParams = {
        'facet': 'false',
        'rows': 4,
        'fl': 'reference_image_md5',
        'fq':
            [f'collection_url: "{collection_url}"', f'{facet}_ss: "{escaped_cluster_value}"']
        }
    solr_thumbs = SOLR_select(**thumbParams)
    thumbnails = [result.get('reference_image_md5') for result in solr_thumbs.results]
    return thumbnails

# average 'best case': http://127.0.0.1:8000/collections/27433/browse/
# long rights statement: http://127.0.0.1:8000/collections/26241/browse/
# questioning grid usefulness: http://127.0.0.1:8000/collections/26935/browse/
# grid is helpful for ireland, building, ruin, stone: http://127.0.0.1:8000/collections/12378/subject/?view_format=grid&sort=largestFirst
# failed browse page: http://127.0.0.1:8000/collections/10318/browse/
# failed browse page: http://127.0.0.1:8000/collections/26666/browse/
# known issue, no thumbnails: http://127.0.0.1:8000/collections/26666/browse/
# less useful thumbnails: http://127.0.0.1:8000/collections/26241/browse/

def collectionBrowse(request, collection_id):
    collection = Collection(collection_id)
    facet_sets = collection.get_facet_sets()

    if len(facet_sets) == 0:
        return redirect('calisphere:collectionView', collection_id)

    for facet_set in facet_sets:
        facet_set['thumbnails'] = getClusterThumbnails(
            collection.url, 
            facet_set['facet_field'], 
            facet_set['values'][0]['label']
        )

    context = {
        'meta_robots': "noindex,nofollow",
        'collection': collection.details,
        'collection_id': collection_id,
        'UCLDC_SCHEMA_FACETS': UCLDC_SCHEMA_FACETS,
        'item_count': collection.get_item_count(),
        'clusters': facet_sets,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(request, 'calisphere/collections/collectionBrowse.html', context)

