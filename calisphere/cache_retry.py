""" logic for cache / retry for solr and JSON from registry
"""

from future import standard_library
standard_library.install_aliases()
from builtins import object
from django.core.cache import cache
from django.conf import settings

from collections import namedtuple
import urllib.request, urllib.error, urllib.parse
from retrying import retry
import requests
import pickle
import hashlib
import json
import itertools
import re
from typing import Dict, List, Tuple

requests.packages.urllib3.disable_warnings()

from aws_xray_sdk.core import patch

if hasattr(settings, 'XRAY_RECORDER'):
    patch(('requests', ))

SOLR_DEFAULTS = {
    'mm': '100%',
    'pf3': 'title',
    'pf': 'text,title',
    'qs': 12,
    'ps': 12,
}
"""
    qf:
        fields and the "boosts" `fieldOne^2.3 fieldTwo fieldThree^0.4`
    mm: (Minimum 'Should' Match)
    qs:
        Query Phrase Slop (in qf fields; affects matching).

    pf: Phrase Fields
	"pf" with the syntax
        field~slop.
        field~slop^boost.
    ps:
	Default amount of slop on phrase queries built with "pf",
	"pf2" and/or "pf3" fields (affects boosting).
    pf2: (Phrase bigram fields)
    ps2: (Phrase bigram slop)
	<!> Solr4.0 As with 'ps' but for 'pf2'. If not specified,
	'ps' will be used.
    pf3 (Phrase trigram fields)
	As with 'pf' but chops the input into tri-grams, e.g. "the
	brown fox jumped" is queried as "the brown fox" "brown fox
	jumped"
    ps3 (Phrase trigram slop)
    tie (Tie breaker)
	Float value to use as tiebreaker in DisjunctionMaxQueries
	(should be something much less than 1)
        Typically a low value (ie: 0.1) is useful.

"""

SolrResults = namedtuple(
    'SolrResults', 'results header numFound facet_counts nextCursorMark')
SolrItem = namedtuple(
    'SolrItem', 'found, item, resp')

col_regex = (r'https://registry\.cdlib\.org/api/v1/collection/'
             r'(?P<id>\d*)/?')
repo_regex = (r'https://registry\.cdlib\.org/api/v1/repository/'
              r'(?P<id>\d*)/?')


def SOLR_get(**kwargs):
    item_search = SOLR_select(**kwargs)
    found = bool(item_search.numFound)
    item = item_search.results[0]

    def get_col_id(url):
        col_id = (re.match(col_regex, url).group('id'))
        return col_id
    def get_repo_id(url):
        repo_id = (re.match(repo_regex, url).group('id'))
        return repo_id

    item['collection_ids'] = [
        get_col_id(url) for url in item.get('collection_url')]
    item['repository_ids'] = [
        get_repo_id(url) for url in item.get('repository_url')]
    
    results = SolrItem(found, item, item_search)
    return results


def SOLR_mlt(item_id):
    res = SOLR_raw(
        q='id:' + item_id,
        fields='id, type_ss, reference_image_md5, title',
        mlt='true',
        mlt_count='24',
        mlt_fl='title,collection_name,subject',
        mlt_mintf=1,
    )
    results = json.loads(res.decode('utf-8'))
    return SolrResults(
        (results['response']['docs'] + 
            results['moreLikeThis'][item_id]['docs']),
        results['responseHeader'],
        results['response']['numFound'],
        None,
        results.get('nextCursorMark')
    )


def SOLR(**params):
    # replacement for edsu's solrpy based stuff
    solr_url = '{}/query/'.format(settings.SOLR_URL)
    solr_auth = {'X-Authentication-Token': settings.SOLR_API_KEY}
    # Clean up optional parameters to match SOLR spec
    query = {}
    for key, value in list(params.items()):
        key = key.replace('_', '.')
        query.update({key: value})
    res = requests.post(solr_url, headers=solr_auth, data=query, verify=False)
    res.raise_for_status()
    results = json.loads(res.content.decode('utf-8'))
    facet_counts = results.get('facet_counts', {})
    for key, value in list(facet_counts.get('facet_fields', {}).items()):
        # Make facet fields match edsu with grouper recipe
        facet_counts['facet_fields'][key] = dict(
            itertools.zip_longest(*[iter(value)] * 2, fillvalue=""))

    return SolrResults(
        results['response']['docs'],
        results['responseHeader'],
        results['response']['numFound'],
        facet_counts,
        results.get('nextCursorMark'),
    )


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


# dummy class for holding cached data
class SolrCache(object):
    pass


# wrapper function for solr queries
@retry(stop_max_delay=3000)  # milliseconds
def SOLR_select(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    # look in the cache
    key = 'SOLR_select_{0}'.format(kwargs_md5(**kwargs))
    sc = cache.get(key)
    if not sc:
        # do the solr look up
        sr = SOLR(**kwargs)
        # copy attributes that can be pickled to new object
        sc = SolrCache()
        sc.results = sr.results
        sc.header = sr.header
        sc.facet_counts = getattr(sr, 'facet_counts', None)
        sc.numFound = sr.numFound
        cache.set(key, sc, settings.DJANGO_CACHE_TIMEOUT)  # seconds
    return sc


@retry(stop_max_delay=3000)
def SOLR_raw(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    # look in the cache
    key = 'SOLR_raw_{0}'.format(kwargs_md5(**kwargs))
    sr = cache.get(key)
    if not sr:
        # do the solr look up
        solr_url = '{}/query/'.format(settings.SOLR_URL)
        solr_auth = {'X-Authentication-Token': settings.SOLR_API_KEY}
        # Clean up optional parameters to match SOLR spec
        query = {}
        for key, value in list(kwargs.items()):
            key = key.replace('_', '.')
            query.update({key: value})
        res = requests.get(
            solr_url, headers=solr_auth, params=query, verify=False)
        res.raise_for_status()
        sr = res.content
        cache.set(key, sr, settings.DJANGO_CACHE_TIMEOUT)  # seconds
    return sr


@retry(stop_max_delay=3000)
def SOLR_select_nocache(**kwargs):
    kwargs.update(SOLR_DEFAULTS)
    sr = SOLR(**kwargs)
    return sr


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
                 facet_sort: str = None):

    solr_params = {}

    if query_string:
        solr_params['q'] = query_string

    solr_filters = []
    if filters:
        for f in filters:
            filters_of_type = []
            for filter_field, values in f.items():
                fq = [f"{filter_field}: \"{v}\"" for v in values]
                filters_of_type.append(fq)

            filters_of_type = " OR ".join(filters_of_type[0])
            solr_filters.append(filters_of_type)

    if exclude:
        for f in exclude:
            eq = [f'(*:* AND -{k}:\"{v[0]}\")'
                  for k, v in f.items()]
            solr_filters.append(eq[0])

    if solr_filters:
        if len(solr_filters) == 1:
            solr_params['fq'] = solr_filters[0]
        else:
            solr_params['fq'] = solr_filters

    if facets:
        exceptions = [
            'repository_url', 
            'sort_collection_data', 
            'repository_data',
            'collection_data',
            'facet_decade']
        solr_facets = [facet if (facet in exceptions
                       or facet[-3:] == '_ss')
                       else f"{facet}_ss" for facet in facets]
        solr_params.update({
            'facet': 'true',
            'facet_field': solr_facets,
            'facet_limit': '-1',
            'facet_mincount': 1})

    if facet_sort:
        solr_params.update({
            'facet_sort': facet_sort
        })

    if result_fields:
        solr_params['fl'] = ", ".join(result_fields)

    if sort:
        solr_params['sort'] = f"{sort[0]} {sort[1]}"
    
    solr_params.update({'rows': rows})

    return solr_params


def search_index(query):
    return SOLR_select(**query_encode(**query))