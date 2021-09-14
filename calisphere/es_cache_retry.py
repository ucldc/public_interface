""" logic for cache / retry for solr and JSON from registry
"""

from future import standard_library
from django.core.cache import cache
from django.conf import settings

from collections import namedtuple
import urllib.request
import urllib.error
from retrying import retry
import requests
import pickle
import hashlib
import json
from typing import Dict, List, Tuple
from aws_xray_sdk.core import patch
from elasticsearch import Elasticsearch

requests.packages.urllib3.disable_warnings()
standard_library.install_aliases()

if hasattr(settings, 'XRAY_RECORDER'):
    patch(('requests', ))

elastic_client = Elasticsearch(
    hosts=[settings.ES_HOST],
    http_auth=(settings.ES_USER, settings.ES_PASS))

ESResults = namedtuple(
    'ESResults', 'results numFound facet_counts')
ESItem = namedtuple(
    'ESItem', 'found, item, resp')


def es_search(body):
    results = elastic_client.search(
        index="calisphere-items", body=body)

    aggs = results.get('aggregations')
    facet_counts = {'facet_fields': {}}
    if aggs:
        for facet_field in aggs:
            buckets = aggs[facet_field].get('buckets')
            facet_values = {b['key']: b['doc_count'] for b in buckets}
            facet_counts['facet_fields'][facet_field] = facet_values
    else:
        facet_counts = {}

    for result in results['hits']['hits']:
        metadata = result.pop('_source')
        metadata['title'] = [metadata.get('title')]
        metadata['type'] = [metadata.get('type')]
        metadata['type_ss'] = [metadata.get('type')]
        result.update(metadata)

    results = ESResults(
        results['hits']['hits'],
        results['hits']['total']['value'],
        facet_counts)

    return results


def es_search_nocache(**kwargs):
    return es_search(kwargs)


def es_get(item_id):
    item_search = elastic_client.get(
        index="calisphere-items", id=item_id)
    found = item_search['found']
    item = item_search['_source']

    # make it look a little more like solr
    item.pop('word_bucket')
    item['title'] = [item['title']]
    item['type'] = [item['type']]
    item['source'] = [item['source']]
    item['location'] = [item['location']]

    results = ESItem(found, item, item_search)
    return results


# create a hash for a cache key
def kwargs_md5(**kwargs):
    m = hashlib.md5()
    m.update(pickle.dumps(kwargs))
    return m.hexdigest()


# wrapper function for json.loads(urllib2.urlopen)
@retry(wait_exponential_multiplier=2, stop_max_delay=10000)  # milliseconds
def json_loads_url(url_or_req):
    key = kwargs_md5(key='json_loads_url', url=url_or_req)
    data = cache.get(key)
    if not data:
        try:
            data = json.loads(
                urllib.request.urlopen(url_or_req).read().decode('utf-8'))
        except urllib.error.HTTPError:
            data = {}
    return data


def es_mlt(item_id):
    first_item = es_get(item_id)
    es_query = {
        "query": {
            "more_like_this": {
                "fields": [
                    "title.keyword",
                    "collection_data",
                    "subject.keyword"
                ],
                "like": [
                    {"_id": item_id}
                ],
                "min_term_freq": 1
            }
        },
        "_source": ["id", "type", "reference_image_md5", "title"],
        "size": 24
    }
    mlt_results = es_search(es_query)
    mlt_results.results.insert(0, first_item.item)
    return mlt_results


FieldName = str
Order = str
FilterValues = list
FilterField = Dict[FieldName, FilterValues]
Filters = List[FilterField]


def query_encode(query_string: str = None, 
                 filters: Filters = None,
                 exclude: Filters = None,
                 sort: Tuple[FieldName, Order] = None,
                 start: int = None,
                 rows: int = 0,
                 result_fields: List[str] = None,
                 facets: List[str] = None,
                 facet_sort: dict = None):

    es_params = {}

    es_query = es_filters = es_exclude = None

    if query_string:
        es_query = [{
            "query_string": {
                "query": query_string
            }
        }]

    if filters:
        es_filters = [{
            'terms': {k: v} for k, v in f.items()
        } for f in filters]

    if exclude:
        es_exclude = [{
            'terms': {k: v} for k, v in e.items()
        } for e in exclude]

    if es_query or es_filters or es_exclude:
        es_params['query'] = {'bool': {}}
        if es_query:
            es_params['query']['bool']['must'] = es_query
        if es_filters:
            es_params['query']['bool']['filter'] = es_filters
        if es_exclude:
            es_params['query']['bool']['must_not'] = es_exclude

        # unsure if this is an unnecessary optimization:
        # https://discuss.elastic.co/t/filter-performance-difference-bool-vs-terms/59928
        if len(es_params['query']['bool']) == 1:
            if 'must' in es_params['query']['bool']:
                es_params['query'] = es_query[0]
            elif ('filter' in es_params['query']['bool'] and 
                  len(es_params['query']['bool']['filter']) == 1):
                es_params['query'] = es_filters[0]

    if facets:
        exceptions = ['collection_ids', 'repository_ids', 'campus_ids']
        aggs = {}
        for facet in facets:
            if facet in exceptions or facet[-8:] == '.keyword':
                field = facet
            else:
                field = f'{facet}.keyword'

            aggs[facet] = {
                "terms": {
                    "field": field,
                    "size": 10000
                }
            }

            if facet_sort:
                aggs[facet]["terms"]["order"] = facet_sort
        # regarding 'size' parameter here and getting back all the facet values
        # please see: https://github.com/elastic/elasticsearch/issues/18838

        es_params.update({"aggs": aggs})

    if result_fields:
        es_params.update({"_source": result_fields})

    # if sort:
    #     es_params.update({
    #         "sort": [{
    #             sort[0]: {"order": sort[1]}
    #         }]
    #     })
    
    es_params.update({'size': rows})
    if start:
        es_params.update({'from': start})
    return es_params


def search_index(query):
    return es_search(query_encode(**query))