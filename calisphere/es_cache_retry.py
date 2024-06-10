""" logic for cache / retry for es (opensearch) and JSON from registry
"""

import json
import urllib3

from collections import namedtuple
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

from aws_xray_sdk.core import patch
from django.core.cache import cache
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError
from elasticsearch.exceptions import RequestError as ESRequestError
from retrying import retry

from calisphere.constants import UCLDC_SCHEMA_TERM_FIELDS
from calisphere.utils import kwargs_md5

urllib3.disable_warnings()

if hasattr(settings, 'XRAY_RECORDER'):
    patch(('requests', ))

if settings.ES_HOST and settings.ES_USER and settings.ES_PASS:
    elastic_client = Elasticsearch(
        hosts=[settings.ES_HOST],
        http_auth=(settings.ES_USER, settings.ES_PASS))

ESResults = namedtuple(
    'ESResults', 'results numFound facet_counts')
ESItem = namedtuple(
    'ESItem', 'found, item, resp')


def shim_record(metadata):
    # TODO replace type_ss with type globally
    metadata['type_ss'] = metadata.get('type')
    metadata['collection_ids'] = metadata.get('collection_url')
    metadata['repository_ids'] = metadata.get('repository_url')

    thumbnail_key = get_thumbnail_key(metadata)
    if thumbnail_key:
        metadata['reference_image_md5'] = thumbnail_key
        metadata['reference_image_dimensions'] = (
            metadata.get('thumbnail', {}).get('dimensions'))

    media_key = get_media_key(metadata)
    if media_key:
        metadata['media']['media_key'] = media_key

    if metadata.get('children'):
        children = metadata.pop('children')
        updated_children = []
        for child in children:
            thumbnail_key = get_thumbnail_key(child)
            if thumbnail_key:
                child['thumbnail_key'] = thumbnail_key
            media_key = get_media_key(child)
            if media_key:
                child['media']['media_key'] = media_key
            updated_children.append(child)
        metadata['children'] = updated_children

    return metadata


@retry(stop_max_delay=3000)  # milliseconds
def es_search(body) -> ESResults:
    cache_key = f"es_search_{kwargs_md5(**body)}"
    cached_results = cache.get(cache_key)
    if cached_results:
        return cached_results

    try:
        results = elastic_client.search(
            index=settings.ES_ALIAS, body=json.dumps(body))
    except ESConnectionError as e:
        raise ConnectionError(
            f"No OpenSearch connection: {settings.ES_HOST}") from e
    except ESRequestError as e:
        raise ValueError(
            f"Bad request: {e}\n{json.dumps(body, indent=2)}") from e

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
        metadata = shim_record(result.pop('_source'))
        result.update(metadata)

    results = ESResults(
        results['hits']['hits'],
        results['hits']['total']['value'],
        facet_counts)

    cache.set(cache_key, results, settings.DJANGO_CACHE_TIMEOUT)  # seconds

    return results

def get_thumbnail_key(metadata):
    if metadata.get('thumbnail'):
        path = metadata['thumbnail'].get('path','')
        if path.startswith('s3://'):
            uri_path = urlparse(path).path
            key_parts = uri_path.split('/')[2:]
            return '/'.join(key_parts)

def get_media_key(metadata):
    if metadata.get('media'):
        path = metadata['media'].get('path','')
        if path.startswith('s3://'):
            uri_path = urlparse(path).path
            key_parts = uri_path.split('/')[2:]
            return '/'.join(key_parts)


# def es_search_nocache(**kwargs):
#     return es_search(kwargs)


@retry(stop_max_delay=3000)  # milliseconds
def es_get(item_id: str) -> Optional[ESItem]:
    # cannot search Elasticsearch with empty string
    if not item_id:
        return None

    cache_key = f"es_get_{item_id}"
    cached_results = cache.get(cache_key)
    if cached_results:
        return cached_results

    # cannot use Elasticsearch.get() for multi-index alias
    body = {'query': {'match': {'_id': item_id}}}
    try:
        item_search = elastic_client.search(
            index=settings.ES_ALIAS, body=json.dumps(body))
    except ESConnectionError as e:
        raise ConnectionError(
            f"No OpenSearch connection: {settings.ES_HOST}") from e
    except ESRequestError as e:
        raise ValueError(
            f"Bad request: {e}\n{json.dumps(body, indent=2)}") from e

    found = item_search['hits']['total']['value']
    if not found:
        return None
    item = shim_record(item_search['hits']['hits'][0]['_source'])

    results = ESItem(found, item, item_search)
    cache.set(cache_key, results, settings.DJANGO_CACHE_TIMEOUT)  # seconds
    return results


def es_get_ids(ids: List[str]) -> ESResults:
    body = {'query': {'ids': {'values': ids}}, 'size': len(ids)}
    return es_search(body)


def es_mlt(item_id):
    first_item = es_get(item_id)
    es_query = {
        "query": {
            "more_like_this": {
                "fields": [
                    "title.raw",
                    "collection_data",
                    "subject.raw",
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
                "query": query_string,
                "fields": [
                    "title^2",
                    "*"
                ],
                "default_operator": "AND",
                "minimum_should_match": "100%"
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
        aggs = {}
        for facet in facets:
            if facet in UCLDC_SCHEMA_TERM_FIELDS or facet[-4:] == '.raw':
                field = facet
            else:
                field = f'{facet}.raw'

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
        if 'reference_image_md5' in result_fields:
            i = result_fields.index('reference_image_md5')
            result_fields[i] = 'thumbnail'
        if 'type_ss' in result_fields:
            i = result_fields.index('type_ss')
            result_fields[i] = 'type'

    if sort:
        if sort[0] == 'score':
            sort_by = '_score'
        else:
            sort_by = sort[0]
        es_params.update({
            "sort": [{
            sort_by: {"order": sort[1]}
        }]
    })
    
    es_params.update({'size': rows})
    if start:
        es_params.update({'from': start})

    es_params.update({'track_total_hits': True})
    return es_params


def search_es(query):
    return es_search(query_encode(**query))
