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

    return render(request, 'calisphere/collectionsRandomExplore.html', context)


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

    return render(request, 'calisphere/collectionsAZ.html', context)


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
    return render(request, 'calisphere/collectionsTitleSearch.html', {
        'collections': [],
        'collection_q': True
    })


def collectionView(request, collection_id):
    collection_url = 'https://registry.cdlib.org/api/v1/collection/' + collection_id + '/'
    collection_details = json_loads_url(collection_url + '?format=json')
    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))

    for repository in collection_details.get('repository'):
        repository['resource_id'] = repository.get('resource_uri').split(
            '/')[-2]

    params = request.GET.copy()
    context = searchDefaults(params)

    # Collection Views don't allow filtering or faceting by collection_data or repository_data
    facet_filter_types = [
        facet_filter_type for facet_filter_type in FACET_FILTER_TYPES
        if facet_filter_type['facet'] != 'collection_data'
        and facet_filter_type['facet'] != 'repository_data'
    ]
    # Add Custom Facet Filter Types
    if collection_details.get('custom_facet'):
        for custom_facet in collection_details.get('custom_facet'):
            facet_filter_types.append(
                FacetFilterType(
                    custom_facet['facet_field'],
                    custom_facet['label'],
                    custom_facet['facet_field'],
                    custom_facet.get('sort_by', 'count')
                )
            )
    else:
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

    extra_filter = 'collection_url: "' + collection_url + '"'

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
        'meta_robots': None,
        'totalNumItems':
        total_items.numFound,
        'FACET_FILTER_TYPES':
        facet_filter_types,
        'collection':
        collection_details,
        'collection_id':
        collection_id,
        'form_action':
        reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    })

    return render(request, 'calisphere/collectionView.html', context)


def collectionFacet(request, collection_id, facet):
    if not facet in UCLDC_SCHEMA_FACETS:
        raise Http404("{} does not exist".format(facet))
    collection_url = 'https://registry.cdlib.org/api/v1/collection/' + collection_id + '/'
    collection_details = json_loads_url(collection_url + '?format=json')
    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))

    for repository in collection_details.get('repository'):
        repository['resource_id'] = repository.get('resource_uri').split(
            '/')[-2]

    params = request.GET.copy()
    context = searchDefaults(params)
    context.update({'facet': facet,})
    # facet=true&facet.query=*&rows=0&facet.field=title_ss&facet.pivot=title_ss,collection_data"
    solrParams = {
        'facet': 'true',
        'rows': 0,
        'facet_field': '{}_ss'.format(facet),
        'fq': 'collection_url:"{}"'.format(collection_url),
        'facet_limit': '-1',
        'facet_mincount': 1,
        'facet_sort': 'count',
    }
    solr_search = SOLR_select(**solrParams)

    values = solr_search.facet_counts.get('facet_fields').get('{}_ss'.format(facet))
    if not values:
        raise Http404("{0} has no values".format(facet))
    unique = len(values)
    records = sum(values.values())
    ratio = unique / records
    context.update({'values': values, 'unique': unique, 'records': records, 'ratio': ratio})

    context.update({
        'title': f"{facet} values from {collection_details['name']}",
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection_details,
        'collection_id': collection_id,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    })

    return render(request, 'calisphere/collectionFacet.html', context )


def collectionFacetValue(request, collection_id, facet, facet_value):
    collection_url = 'https://registry.cdlib.org/api/v1/collection/' + collection_id + '/'
    collection_details = json_loads_url(collection_url + '?format=json')

    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))
    if not facet in UCLDC_SCHEMA_FACETS:
        raise Http404("{} does not exist".format(facet))
    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))

    for repository in collection_details.get('repository'):
        repository['resource_id'] = repository.get('resource_uri').split(
            '/')[-2]

    params = request.GET.copy()

    parsed_facet_value = urllib.parse.unquote_plus(facet_value)
    escaped_facet_value = solr_escape(parsed_facet_value)
    params.update({'fq': f"{facet}_ss:\"{escaped_facet_value}\""})
    if not 'view_format' in params:
        params.update({'view_format': 'list'})
    if not 'rows' in params:
        params.update({'rows': '48'})
    if not 'sort' in params:
        params.update({'sort': 'oldest-end'})

    context = searchDefaults(params)

    # Collection Views don't allow filtering or faceting by collection_data or repository_data
    facet_filter_types = [
        facet_filter_type for facet_filter_type in FACET_FILTER_TYPES
        if facet_filter_type['facet'] != 'collection_data'
        and facet_filter_type['facet'] != 'repository_data'
    ]

    extra_filter = 'collection_url: "' + collection_url + '"'

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

    # context['facets'] = facetQuery(facet_filter_types, params, solr_search,
    #                               extra_filter)

    collection_name = collection_details.get('name')
    context.update({'facet': facet,})
    context.update({'facet_value': parsed_facet_value,})
    context.update({
        'meta_robots': "noindex,nofollow",
        'totalNumItems': total_items.numFound,
        'FACET_FILTER_TYPES': facet_filter_types,
        'collection': collection_details,
        'collection_id': collection_id,
        'title': f"{facet}: {parsed_facet_value} ({solr_search.numFound} items) from: {collection_name}",
        'description': None,
        'solrParams': solrParams,
        'form_action': reverse(
            'calisphere:collectionFacetValue',
            kwargs={
              'collection_id': collection_id,
              'facet': facet,
              'facet_value': facet_value,
            }),
    })

    return render(request, 'calisphere/collectionFacetValue.html', context )


def collectionMetadata(request, collection_id):
    summary_url = os.path.join(
        settings.UCLDC_METADATA_SUMMARY,
        '{}.json'.format(collection_id),
    )
    summary_data = json_loads_url(summary_url)
    if not summary_data:
        raise Http404("{0} does not exist".format(collection_id))

    collection_url = 'https://registry.cdlib.org/api/v1/collection/' + collection_id + '/'
    collection_details = json_loads_url(collection_url + '?format=json')
    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))

    for repository in collection_details.get('repository'):
        repository['resource_id'] = repository.get('resource_uri').split(
            '/')[-2]

    params = request.GET.copy()
    context = searchDefaults(params)
    context = {
        'title': f"Metadata report for {collection_details['name']}",
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection_details,
        'collection_id': collection_id,
        'summary_data': summary_data,
        'UCLDC_SCHEMA_FACETS': UCLDC_SCHEMA_FACETS,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(request, 'calisphere/collectionMetadata.html', context)
