""" logic for cache / retry for es (opensearch) and JSON from registry
"""

from future import standard_library
from django.core.cache import cache
from django.conf import settings

from collections import namedtuple
import urllib.request
import urllib.error
from urllib.parse import urlparse
from retrying import retry
import urllib3
import pickle
import hashlib
import json
from typing import Dict, List, Tuple, Optional
from aws_xray_sdk.core import patch
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError

urllib3.disable_warnings()
standard_library.install_aliases()

if hasattr(settings, 'XRAY_RECORDER'):
    patch(('requests', ))

if not settings.ES_HOST or not settings.ES_USER or not settings.ES_PASS:
    raise ImportError("ES settings not defined")

elastic_client = Elasticsearch(
    hosts=[settings.ES_HOST],
    http_auth=(settings.ES_USER, settings.ES_PASS))

ESResults = namedtuple(
    'ESResults', 'results numFound facet_counts')
ESItem = namedtuple(
    'ESItem', 'found, item, resp')


def es_search(body) -> ESResults:
    try:
        results = elastic_client.search(
            index=settings.ES_ALIAS, body=json.dumps(body))
    except ESConnectionError as e:
        raise ConnectionError(
            f"No OpenSearch connection: {settings.ES_HOST}") from e

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
        # TODO replace type_ss with type globally
        metadata['type_ss'] = metadata.get('type')
        # TODO replace reference_image_md5 globally
        thumbnail_key = get_thumbnail_key(metadata)
        if thumbnail_key:
            metadata['reference_image_md5'] = thumbnail_key
        result.update(metadata)

    results = ESResults(
        results['hits']['hits'],
        results['hits']['total']['value'],
        facet_counts)

    return results

def get_thumbnail_key(metadata):
    if metadata.get('thumbnail'):
        path = metadata['thumbnail'].get('path','')
        if path.startswith('s3://'):
            uri_path = urlparse(path).path
            key_parts = uri_path.split('/')[2:]
            return '/'.join(key_parts)

def es_search_nocache(**kwargs):
    return es_search(kwargs)


def es_get(item_id: str) -> Optional[ESItem]:
    # cannot search Elasticsearch with empty string
    if not item_id:
        return None

    # cannot use Elasticsearch.get() for multi-index alias
    body = {'query': {'match': {'_id': item_id}}}
    try:
        item_search = elastic_client.search(
            index=settings.ES_ALIAS, body=json.dumps(body))
    except ESConnectionError as e:
        raise ConnectionError(
            f"No OpenSearch connection: {settings.ES_HOST}") from e
    found = item_search['hits']['total']['value']
    if not found:
        return None
    item = item_search['hits']['hits'][0]['_source']

    item['collection_ids'] = item.get('collection_url')
    item['repository_ids'] = item.get('repository_url')
    thumbnail_key = get_thumbnail_key(item)
    if thumbnail_key:
        item['reference_image_md5'] = thumbnail_key

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
                    "subject.keyword",
                    "thumbnail"
                ],
                "like": [
                    {"_id": item_id}
                ],
                "min_term_freq": 1
            }
        },
        "_source": ["id", "type", "thumbnail", "title"],
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
        # TODO tidy this up when we settle on a field type for these
        #exceptions = ['repository_url', 'collection_url', 'campus_url']
        exceptions = []
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


def search_es(query):
    return es_search(query_encode(**query))
