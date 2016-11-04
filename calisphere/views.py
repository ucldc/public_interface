from django.apps import apps
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse, HttpResponse
from calisphere.collection_data import CollectionManager
from constants import *
from cache_retry import SOLR_select, SOLR_raw, json_loads_url
from static_sitemaps.util import _lazy_load
from static_sitemaps import conf

import os
import operator
import math
import re
import copy
import simplejson as json
import string
import urlparse

# concat query with 'AND'
def concat_query(q, rq):
    if q == '': return rq
    elif rq == '': return q
    else: return q + ' AND ' + rq

# concat filters with 'OR'
def concat_filters(filters, filter_type):
    # OR-ING FILTERS OF ONE TYPE, YET AND-ING FILTERS OF DIFF TYPES
    fq_contents = filter_type + ': '

    for counter, f in enumerate(filters):
        fq_contents = fq_contents + '"' + f + '"'
        # if not at the last filter term, continue OR-ing together terms
        if counter < len(filters)-1:
            fq_contents = fq_contents + " OR " + filter_type + ': '

    return [fq_contents]

# collect filters into an array
def solrize_filters(filters):
    fq = []
    for filter_type in list(facet_filter_type['filter'] for facet_filter_type in FACET_FILTER_TYPES):
        if len(filters[filter_type]) > 0:
            fq.extend(concat_filters(filters[filter_type], filter_type))

    return fq

def solrize_sort(sort):
    # return 'score desc'
    if sort == 'relevance':
        return 'score desc'
    elif sort == 'a':
        return 'sort_title asc'
    elif sort == 'z':
        return 'sort_title desc'
    elif sort == 'oldest-start':
        return 'sort_date_start asc'
    elif sort == 'oldest-end':
        return 'sort_date_end asc'
    elif sort == 'newest-start':
        return 'sort_date_start desc'
    elif sort == 'newest-end':
        return 'sort_date_end desc'
    else:
        return 'score desc'

def process_sort_collection_data(string):
    '''temporary; should parse sort_collection_data
       with either `:` or `::` dlimiter style
    '''
    if '::' in string:
        return string.split('::', 2)
    else:
        part1, remainder = string.split(':', 1)
        part2, part3 = remainder.rsplit(':https:')
        return [part1, part2, u'https:{}'.format(part3)]

def getMoreCollectionData(collection_data):
    collection = getCollectionData(
        collection_data=collection_data,
        collection_id=None,
    )
    collection_details = json_loads_url(
        "{0}?format=json".format(collection['url'])
    )
    collection['local_id'] = collection_details['local_id']
    collection['slug'] = collection_details['slug']
    return collection

def getCollectionData(collection_data=None, collection_id=None):
    collection = {}
    if collection_data:
        parts = collection_data.split('::')
        collection['url'] = parts[0] if len(parts) >= 1 else ''
        collection['name'] = parts[1] if len(parts) >= 2 else ''
        collection_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/collection/(?P<url>\d*)/?', collection['url'])
        if collection_api_url is None:
            print 'no collection api url:'
            collection['id'] = ''
        else:
            collection['id'] = collection_api_url.group('url')
    elif collection_id:
        solr_collections = CollectionManager(settings.SOLR_URL, settings.SOLR_API_KEY)
        collection['url'] = "https://registry.cdlib.org/api/v1/collection/{0}/".format(collection_id)
        collection['id'] = collection_id
        collection_details = json_loads_url("{0}?format=json".format(collection['url']))
        collection['name'] = solr_collections.names.get(collection['url']) or collection_details['name']
        collection['local_id'] = collection_details['local_id']
        collection['slug'] = collection_details['slug']
    return collection

def getCollectionMosaic(collection_url):
    collection_details = json_loads_url(collection_url + "?format=json")

    collection_repositories = []

    repository_details = collection_details.get('repository')

    # if not (repository_details):
    #     return

    for repository in repository_details:
        if 'campus' in repository and len(repository['campus']) > 0:
            collection_repositories.append(repository['campus'][0]['name'] + ", " + repository['name'])
        else:
            collection_repositories.append(repository['name'])

    collection_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/collection/(?P<url>\d*)/?', collection_url)
    collection_id = collection_api_url.group('url')

    display_items = SOLR_select(
        q='*:*',
        fields='reference_image_md5, url_item, id, title, collection_url, type_ss',
        sort=solrize_sort('a'),
        rows=6,
        start=0,
        fq=['collection_url: \"' + collection_url + '\"', 'type_ss: \"image\"']
    )

    items = display_items.results

    ugly_display_items = SOLR_select(
        q='*:*',
        fields='reference_image_md5, url_item, id, title, collection_url, type_ss',
        sort=solrize_sort('a'),
        rows=6,
        start=0,
        fq=['collection_url: \"' + collection_url + '\"', '(*:* AND -type_ss:\"image\")']
    )

    if len(display_items.results) < 6:
        items = items + ugly_display_items.results

    return {
        'name': collection_details['name'],
        'institutions': collection_repositories,
        'description': collection_details['description'],
        'collection_id': collection_id,
        'numFound': display_items.numFound + ugly_display_items.numFound,
        'display_items': items
    }

def getRepositoryData(repository_data=None, repository_id=None):
    """ supply either `repository_data` from solr or the `repository_id` """
    app = apps.get_app_config('calisphere')
    repository = {}
    repository_details = {}
    if repository_data:
        parts = repository_data.split('::')
        repository['url'] = parts[0] if len(parts) >= 1 else ''
        repository['name'] = parts[1] if len(parts) >= 2 else ''
        repository['campus'] = parts[2] if len(parts) >= 3 else ''

        repository_api_url = re.match(
            r'^https://registry\.cdlib\.org/api/v1/repository/(?P<url>\d*)/',
            repository['url']
        )
        if repository_api_url is None:
            print 'no repository api url'
            repository['id'] = ''
        else:
            repository['id'] = repository_api_url.group('url')
            repository_details = app.registry.repository_data.get(
                int(repository['id']), {}
            )
    elif repository_id:
        repository['url'] = "https://registry.cdlib.org/api/v1/repository/{0}/".format(repository_id)
        repository['id'] = repository_id
        repository_details = app.registry.repository_data.get(int(repository_id), None)
        repository['name'] = repository_details['name']
        if repository_details['campus']:
            repository['campus'] = repository_details['campus'][0]['name']
        else:
            repository['campus'] = ''
    # details needed for stats
    repository['ga_code'] = repository_details.get('google_analytics_tracking_code', None)
    parent = repository_details['campus']
    pslug = u''
    if len(parent):
        pslug = '{0}-'.format(parent[0].get('slug', None))
    repository['slug'] = pslug + repository_details.get('slug', None)
    return repository

def process_facets(facets, filters, facet_type=None):
    display_facets = dict((facet, count) for facet, count in facets.iteritems() if count != 0)
    if facet_type and facet_type == 'facet_decade':
        display_facets = sorted(display_facets.iteritems(), key=operator.itemgetter(0))
    else:
        display_facets = sorted(display_facets.iteritems(), key=operator.itemgetter(1), reverse=True)

    for f in filters:
        if not any(f in facet[0] for facet in display_facets):
            api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/(?P<collection_or_repo>collection|repository)/(?P<url>\d*)/?', f)
            if api_url is not None:
                if api_url.group('collection_or_repo') == 'collection':
                    collection = getCollectionData(collection_id=api_url.group('url'))
                    display_facets.append((collection['url'] + "::" + collection['name'], 0))
                elif api_url.group('collection_or_repo') == 'repository':
                    repository = getRepositoryData(repository_id=api_url.group('url'))
                    display_facets.append((repository['url'] + "::" + repository['name'], 0))
            else:
                display_facets.append((f, 0))

    return display_facets

def filterType(facet_type):
    for facet_filter_type in FACET_FILTER_TYPES:
        if (facet_filter_type['facet'] == facet_type):
            return facet_filter_type['filter']
    return None

def facetQuery(facet_fields, queryParams, solr_search, extra_filter=None):
    facets = {}
    for facet_type in facet_fields:
        # if we've already selected some of the available facets of this given facet type as filters on the search
        # perform the search again as if we had not selected those filters (of this given type) on the search
        # used to obtain counts - since we AND filters of the same type, counts should go UP when more than one facet is selected
        # as a filter, not DOWN (or'ed filters of the same type)
        filter_type = filterType(facet_type)
        if filter_type in queryParams['filters'] and len(queryParams['filters'][filter_type]) > 0:
            # other_filters is all the filters except the ones of the current filter type
            other_filters = {key: value for key, value in queryParams['filters'].items()
                if key != filter_type}
            other_filters[filter_type] = []

            fq = solrize_filters(other_filters)
            if extra_filter:
                fq.append(extra_filter)

            # perform the exact same search, but as though no filters of this type have been selected
            # to obtain the counts for facets for this facet type
            facet_solr_search = SOLR_select(
                q=queryParams['query_terms'],
                rows='0',
                fq=fq,
                facet='true',
                facet_mincount=1,
                facet_limit='-1',
                facet_field=[facet_type]
            )
            facets[facet_type] = process_facets(
                facet_solr_search.facet_counts['facet_fields'][facet_type],
                queryParams['filters'][filter_type],
                facet_type
            )
        else:
            facets[facet_type] = process_facets(
                solr_search.facet_counts['facet_fields'][facet_type],
                queryParams['filters'][filter_type] if filter_type in queryParams['filters'] else [],
                facet_type
            )

    return facets

def processQueryRequest(request):
    # concatenate query terms from refine query and query box, set defaults
    q = request.GET.get('q', '')
    rq = request.GET.getlist('rq')
    query_terms = ''
    if q or rq:
        query_terms = reduce(
            concat_query,
            request.GET.getlist('q') + request.GET.getlist('rq')
        )
    rows = request.GET.get('rows', '24')
    start = request.GET.get('start', '0')
    try:
        int(start)
    except ValueError:
        start = 0
    if 'sort' in request.GET:
        sort = request.GET['sort']
    elif query_terms:
        sort = 'relevance'
    else:
        sort = 'a'
    view_format = request.GET.get('view_format', 'thumbnails')
    rc_page = int(request.GET.get('rc_page', 0))
    campus_slug = request.GET.get('campus_slug', '')

    # for each facet_filter_type
    #    {'facet': 'facet_solr_name', 'display_name': 'Display Name', 'filter': 'filter_solr_name'}
    # in the list FACET_FILTER_TYPES create a dictionary with key filter_solr_name of filter
    # and value list of selected parameters for that filter
    # {'type': ['image', 'audio'], 'repository_name': [...]}
    filters = dict(
        (
            facet_filter_type['filter'],
            request.GET.getlist(facet_filter_type['facet'])
        )
        for facet_filter_type in FACET_FILTER_TYPES
    )
    # use collection_id and repository_id to retrieve collection_data
    # and repository_data filter values
    collection_template = "https://registry.cdlib.org/api/v1/collection/{0}/"
    repository_template = "https://registry.cdlib.org/api/v1/repository/{0}/"
    for i, filter_item in enumerate(filters['collection_url']):
        filters['collection_url'][i] = collection_template.format(filter_item)
    for i, filter_item in enumerate(filters['repository_url']):
        filters['repository_url'][i] = repository_template.format(filter_item)

    return {
        'q': q,
        'rq': rq,
        'query_terms': query_terms,
        'rows': rows,
        'start': start,
        'sort': sort,
        'view_format': view_format,
        'filters': filters,
        'rc_page': rc_page,
        'campus_slug': campus_slug
    }

def home(request):
    return render (request, 'calisphere/home.html', {'q': ''})

def getHostedContentFile(structmap):
    contentFile = ''
    if structmap['format'] == 'image':
        structmap_url = '{}{}/info.json'.format(
            settings.UCLDC_IIIF,
            structmap['id']
        )
        if structmap_url.startswith('//'):
            structmap_url = u''.join(['http:', structmap_url])
        size = json_loads_url(structmap_url)['sizes'][-1]
        if size['height'] > size['width']:
            access_size = {'width': ((size['width'] * 1024) / size['height']), 'height': 1024}
            access_url = json_loads_url(structmap_url)['@id'] + "/full/,1024/0/default.jpg"
        else:
            access_size = {'width': 1024, 'height': ((size['height'] * 1024) / size['width'])}
            access_url = json_loads_url(structmap_url)['@id'] + "/full/1024,/0/default.jpg"

        contentFile = {
            'titleSources': json.dumps(json_loads_url(structmap_url)),
            'format': 'image',
            'size': access_size,
            'url': access_url
        }
    if structmap['format'] == 'file':
        contentFile = {
            'id': structmap['id'],
            'format': 'file',
        }
    if structmap['format'] == 'video':
        access_url = os.path.join(settings.UCLDC_MEDIA, structmap['id'])
        contentFile = {
            'id': structmap['id'],
            'format': 'video',
            'url': access_url
        }
    if structmap['format'] == 'audio':
        access_url = os.path.join(settings.UCLDC_MEDIA, structmap['id'])
        contentFile = {
            'id': structmap['id'],
            'format': 'audio',
            'url': access_url
        }

    return contentFile

def itemView(request, item_id=''):
    item_id_search_term = 'id:"{0}"'.format(item_id)
    item_solr_search = SOLR_select(q=item_id_search_term)
    if not item_solr_search.numFound:
        # second level search
        def _fixid(id):
            return re.sub(r'^(\d*--http:/)(?!/)', r'\1/', id)
        old_id_search = SOLR_select(q='harvest_id_s:*{}'.format(_fixid(item_id)))
        if old_id_search.numFound:
            return redirect('calisphere:itemView', old_id_search.results[0]['id'])
        else:
            raise Http404("{0} does not exist".format(item_id))

    for item in item_solr_search.results:
        if 'structmap_url' in item and len(item['structmap_url']) >= 1:
            item['harvest_type'] = 'hosted'
            structmap_url = string.replace(item['structmap_url'], 's3://static', 'https://s3.amazonaws.com/static');
            structmap_data = json_loads_url(structmap_url)

            if 'structMap' in structmap_data:
                # complex object
                if 'order' in request.GET and 'structMap' in structmap_data:
                    # fetch component object
                    item['selected'] = False
                    order = int(request.GET['order'])
                    component = structmap_data['structMap'][order]
                    component['selected'] = True
                    if 'format' in component:
                        item['contentFile'] = getHostedContentFile(component)
                    # remove emptry strings from list
                    for k,v in component.iteritems():
                        if isinstance(v, list):
                            if isinstance(v[0], unicode):
                                component[k] = filter(lambda name: name.strip(), v)
                    # remove empty lists and empty strings from dict
                    item['selectedComponent'] = dict((k, v) for k, v in component.iteritems() if v)
                else:
                    item['selected'] = True
                    # if parent content file, get it
                    if 'format' in structmap_data and structmap_data['format'] != 'file':
                        item['contentFile'] = getHostedContentFile(structmap_data)
                    # otherwise get first component file
                    else:
                        component = structmap_data['structMap'][0]
                        item['contentFile'] = getHostedContentFile(component)
                item['structMap'] = structmap_data['structMap']
            else:
                # simple object
                if 'format' in structmap_data:
                    item['contentFile'] = getHostedContentFile(structmap_data)
        else:
            item['harvest_type'] = 'harvested'
            if 'url_item' in item:
                if item['url_item'].startswith('http://ark.cdlib.org/ark:'):
                    item['oac'] = True
                    item['url_item'] = string.replace(item['url_item'], 'http://ark.cdlib.org/ark:', 'http://oac.cdlib.org/ark:')
                    item['url_item'] = item['url_item'] + '/?brand=oac4'
                else:
                    item['oac'] = False
            #TODO: error handling 'else'

        item['parsed_collection_data'] = []
        item['parsed_repository_data'] = []
        item['institution_contact'] = []
        for collection_data in item['collection_data']:
            item['parsed_collection_data'].append(getMoreCollectionData(collection_data))
        if 'repository_data' in item:
            for repository_data in item['repository_data']:
                item['parsed_repository_data'].append(getRepositoryData(repository_data=repository_data))

                institution_url = item['parsed_repository_data'][0]['url']
                institution_details = json_loads_url(institution_url + "?format=json")
                if 'ark' in institution_details and institution_details['ark'] != '':
                    contact_information = json_loads_url("http://dsc.cdlib.org/institution-json/" + institution_details['ark'])
                else:
                    contact_information = ''

                item['institution_contact'].append(contact_information)

    meta_image = False
    if item_solr_search.results[0].get('reference_image_md5', False):
        meta_image = urlparse.urljoin(
            settings.UCLDC_FRONT,
            u'/crop/999x999/{0}'.format(item_solr_search.results[0]['reference_image_md5']),
        )

    fromItemPage = request.META.get("HTTP_X_FROM_ITEM_PAGE")
    if fromItemPage:
        return render (request, 'calisphere/itemViewer.html', {
            'q': '',
            'item': item_solr_search.results[0],
            'item_solr_search': item_solr_search,
            'meta_image': meta_image,
        })
    search_results = { 'reference_image_md5': None }
    search_results.update(item_solr_search.results[0])
    return render(request, 'calisphere/itemView.html', {
        'q': '',
        'item': search_results,
        'item_solr_search': item_solr_search,
        'meta_image': meta_image,
        'rc_page': None,
        'related_collections': None,
        'slug': None,
        'title': None,
        'num_related_collections': None,
        'rq': None,
    })


def search(request):
    if request.method == 'GET' and len(request.GET.getlist('q')) > 0:
        queryParams = processQueryRequest(request)

        # define facet fields to retrieve
        facet_fields = list(facet_filter_type['facet'] for facet_filter_type in FACET_FILTER_TYPES)

        solr_search = SOLR_select(
            q=queryParams['query_terms'],
            rows=queryParams['rows'],
            start=queryParams['start'],
            sort=solrize_sort(queryParams['sort']),
            fq=solrize_filters(queryParams['filters']),
            facet='true',
            facet_mincount=1,
            facet_limit='-1',
            facet_field=facet_fields
        )

        # TODO: create a no results found page
        if len(solr_search.results) == 0: print 'no results found'

        # get facet counts
        facets = facetQuery(facet_fields, queryParams, solr_search)

        for i, facet_item in enumerate(facets['collection_data']):
            collection = (getCollectionData(collection_data=facet_item[0]), facet_item[1])
            facets['collection_data'][i] = collection
        for i, facet_item in enumerate(facets['repository_data']):
            repository = (getRepositoryData(repository_data=facet_item[0]), facet_item[1])
            facets['repository_data'][i] = repository

        filter_display = {}
        for filter_type in queryParams['filters']:
            if filter_type == 'collection_url':
                filter_display['collection_url'] = []
                for filter_item in queryParams['filters'][filter_type]:
                    collection_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/collection/(?P<url>\d*)/?', filter_item)
                    if collection_api_url is not None:
                        collection = getCollectionData(collection_id=collection_api_url.group('url'))
                        collection.pop('local_id', None)
                        collection.pop('slug', None)
                        filter_display['collection_url'].append(collection)
            elif filter_type == 'repository_url':
                filter_display['repository_url'] = []
                for filter_item in queryParams['filters'][filter_type]:
                    repository_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/repository/(?P<url>\d*)/', filter_item)
                    if repository_api_url is not None:
                        repository = getRepositoryData(repository_id=repository_api_url.group('url'))
                        repository.pop('local_id', None)
                        filter_display['repository_url'].append(repository)
            else:
                filter_display[filter_type] = copy.copy(queryParams['filters'][filter_type])

        return render(request, 'calisphere/searchResults.html', {
            'q': queryParams['q'],
            'rq': queryParams['rq'],
            'filters': filter_display,
            'rows': queryParams['rows'],
            'start': queryParams['start'],
            'sort': queryParams['sort'],
            'search_results': solr_search.results,
            'facets': facets,
            'FACET_FILTER_TYPES': FACET_FILTER_TYPES,
            'numFound': solr_search.numFound,
            'pages': int(math.ceil(float(solr_search.numFound)/int(queryParams['rows']))),
            'view_format': queryParams['view_format'],
            'related_collections': relatedCollections(request, queryParams),
            'num_related_collections': len(queryParams['filters']['collection_url']) if len(queryParams['filters']['collection_url']) > 0 else len(facets['collection_data']),
            'rc_page': queryParams['rc_page'],
            'form_action': reverse('calisphere:search')
        })

    return redirect('calisphere:home')

def itemViewCarousel(request):
    item_id = request.GET.get('itemId')
    if item_id is None:
        raise Http404("No item id specified")

    referral = request.GET.get('referral')
    linkBackId = ''
    if referral == 'institution':
        linkBackId = request.GET['repository_data']
    elif referral == 'collection':
        linkBackId = request.GET.get('collection_data', None)
    elif referral == 'campus':
        linkBackId = request.GET['campus_slug']

    queryParams = processQueryRequest(request)

    fq = solrize_filters(queryParams['filters'])
    if 'campus_slug' in request.GET:
        campus_id = ''
        for campus in CAMPUS_LIST:
            if request.GET['campus_slug'] == campus['slug']:
                campus_id = campus['id']
        if campus_id == '':
            raise Http404("Campus registry ID not found")

        fq.append('campus_url: "https://registry.cdlib.org/api/v1/campus/' + campus_id + '/"')

    mlt = False
    if queryParams['q'] == '' and len(fq) == 0:
        mlt=True,
        mlt_fl='title,collection_name,subject'

    if mlt:
        carousel_solr_search = SOLR_raw(
            q='id:'+item_id,
            fields='id, type_ss, reference_image_md5, title',
            mlt='true',
            mlt_count='24',
            mlt_fl=mlt_fl,
            mlt_mintf=1,
        )
        if json.loads(carousel_solr_search)['response']['numFound'] == 0:
            raise Http404('No object with id "' + item_id + '" found.')
        search_results = json.loads(carousel_solr_search)['response']['docs'] + json.loads(carousel_solr_search)['moreLikeThis'][item_id]['docs']
        numFound = len(search_results)
        # numFound = json.loads(carousel_solr_search)['moreLikeThis'][item_id]['numFound']
    else:
        carousel_solr_search = SOLR_select(
            q=queryParams['query_terms'],
            fields='id, type_ss, reference_image_md5, title',
            rows=queryParams['rows'],
            start=queryParams['start'],
            sort=solrize_sort(queryParams['sort']),
            fq=fq
        )
        search_results = carousel_solr_search.results
        numFound = carousel_solr_search.numFound

    if 'init' in request.GET:
        filter_display = {}
        for filter_type in queryParams['filters']:
            if filter_type == 'collection_url':
                filter_display['collection_url'] = []
                for filter_item in queryParams['filters'][filter_type]:
                    collection_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/collection/(?P<url>\d*)/?', filter_item)
                    if collection_api_url is not None:
                        collection = getCollectionData(collection_id=collection_api_url.group('url'))
                        collection.pop('local_id', None)
                        filter_display['collection_url'].append(collection)
            elif filter_type == 'repository_url':
                filter_display['repository_url'] = []
                for filter_item in queryParams['filters'][filter_type]:
                    repository_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/repository/(?P<url>\d*)/', filter_item)
                    if repository_api_url is not None:
                        repository = getRepositoryData(repository_id=repository_api_url.group('url'))
                        repository.pop('local_id', None)
                        filter_display['repository_url'].append(repository)
            else:
                filter_display[filter_type] = copy.copy(queryParams['filters'][filter_type])

        return render(request, 'calisphere/carouselContainer.html', {
            'q': queryParams['q'],
            'rq': queryParams['rq'],
            'sort': queryParams['sort'],
            'filters': filter_display,
            'start': queryParams['start'],
            'numFound': numFound,
            'search_results': search_results,
            'item_id': item_id,
            'referral': request.GET.get('referral'),
            'referralName': request.GET.get('referralName'),
            'campus_slug': request.GET.get('campus_slug'),
            'linkBackId': linkBackId
        })
    else:
        return render(request, 'calisphere/carousel.html', {
            'start': queryParams['start'],
            'search_results': search_results,
            'item_id': item_id
        })

def relatedCollections(request, queryParams={}):
    if not queryParams:
        queryParams = processQueryRequest(request)
        ajaxRequest = True
    else:
        ajaxRequest = False

    # #####################
    # get list of related collections
    # uncomment to get list of related collections disregarding any selected collection filters
    # #####################
    # if 'collection_name' in queryParams['filters'] and len(queryParams['filters']['collection_name']) > 0:
    #     related_collections_filters = {key: value for key, value in queryParams['filters'].items()
    #         if key != 'collection_name'}
    #     related_collections_filters['collection_name'] = []
    # else:
    related_collections_filters = queryParams['filters']

    fq = solrize_filters(related_collections_filters)
    if 'campus_slug' in queryParams and queryParams['campus_slug'] != '':
        campus_id = ''
        for campus in CAMPUS_LIST:
            if queryParams['campus_slug'] == campus['slug']:
                campus_id = campus['id']
        if campus_id == '':
            print "Campus registry ID not found"

        fq.append('campus_url: "https://registry.cdlib.org/api/v1/campus/' + campus_id + '/"')

    related_collections_solr_search = SOLR_select(
        q=queryParams['query_terms'],
        rows='0',
        fq=fq,
        facet='true',
        facet_mincount=1,
        facet_limit='-1',
        facet_field=['collection_data']
    )

    # remove collections with a count of 0 and sort by count
    related_collections_counts = process_facets(
        related_collections_solr_search.facet_counts['facet_fields']['collection_data'],
        queryParams['filters']['collection_url'] if 'collection_url' in queryParams['filters'] else []
    )

    # remove 'count'
    related_collections = list(facet for facet, count in related_collections_counts)

    three_related_collections = []
    for i in range(queryParams['rc_page']*3, queryParams['rc_page']*3+3):
        if len(related_collections) > i:
            facet = ["collection_url: \"" + getCollectionData(related_collections[i])['url'] + "\""]
            collection_solr_search = SOLR_select(q=queryParams['query_terms'], rows='3', fq=facet, fields='collection_data, reference_image_md5, url_item, id, title, type_ss')

            collection_items = collection_solr_search.results
            if len(collection_solr_search.results) < 3:
                collection_solr_search_no_query = SOLR_select(q='', rows='3', fq=facet, fields='collection_data, reference_image_md5, url_item, id, title, type_ss')
                #TODO: in some cases this will result in the same object appearing twice in the related collections preview
                collection_items = collection_items + collection_solr_search_no_query.results

            if len(collection_items) > 0 and len(collection_solr_search.results[0]) > 0:
                if 'collection_data' in collection_solr_search.results[0] and len(collection_solr_search.results[0]['collection_data']) > 0:
                    collection = collection_solr_search.results[0]['collection_data'][0]

                    collection_data = {'image_urls': []}
                    for item in collection_items:
                        collection_data['image_urls'].append(item)

                    collection_url = ''.join([
                        collection.rsplit('::')[0],
                        '?format=json'
                    ])
                    collection_details = json_loads_url(collection_url)

                    collection_data['name'] = collection_details['name']
                    collection_data['resource_uri'] = collection_details['resource_uri']
                    col_id = re.match(r'^/api/v1/collection/(?P<collection_id>\d+)/$', collection_details['resource_uri'])
                    collection_data['collection_id'] = col_id.group('collection_id')

                    # TODO: get this from repository_data in solr rather than from the registry API
                    if collection_details['repository'][0]['campus']:
                        collection_data['institution'] = collection_details['repository'][0]['campus'][0]['name'] + ', ' + collection_details['repository'][0]['name']
                    else:
                        collection_data['institution'] = collection_details['repository'][0]['name']

                    three_related_collections.append(collection_data)

    if not ajaxRequest:
        return three_related_collections
    else:
        return render(request, 'calisphere/related-collections.html', {
            'q': queryParams['q'],
            'rq': queryParams['rq'],
            'num_related_collections': len(related_collections),
            'related_collections': three_related_collections,
            'rc_page': queryParams.get('rc_page'),
        })

def collectionsDirectory(request):
    solr_collections = CollectionManager(settings.SOLR_URL, settings.SOLR_API_KEY)
    collections = []

    page = int(request.GET['page']) if 'page' in request.GET else 1

    for collection_link in solr_collections.shuffled[(page-1)*10:page*10]:
        collections.append(getCollectionMosaic(collection_link.url))

    context = {'collections': collections, 'random': True, 'pages': int(math.ceil(float(len(solr_collections.shuffled))/10))}

    if page*10 < len(solr_collections.shuffled):
        context['next_page'] = page+1
    if page-1 > 0:
        context['prev_page'] = page-1

    return render(request, 'calisphere/collectionsRandomExplore.html', context)


def collectionsAZ(request, collection_letter):
    solr_collections = CollectionManager(settings.SOLR_URL, settings.SOLR_API_KEY)
    collections_list = solr_collections.split[collection_letter.lower()]

    page = int(request.GET['page']) if 'page' in request.GET else 1
    pages = int(math.ceil(float(len(collections_list))/10))

    collections = []
    for collection_link in collections_list[(page-1)*10:page*10]:
        collections.append(getCollectionMosaic(collection_link.url))

    alphabet = list((character, True if character.lower() not in solr_collections.no_collections else False) for character in list(string.ascii_uppercase))

    context = {'collections': collections,
        'alphabet': alphabet,
        'collection_letter': collection_letter,
        'page': page,
        'pages': pages,
        'random': None,
    }

    if page*10 < len(collections_list):
        context['next_page'] = page+1
    if page-1 > 0:
        context['prev_page'] = page-1

    return render(request, 'calisphere/collectionsAZ.html', context)


def collectionsTitles(request):
    '''create JSON/data for the collections search page'''


    def djangoize(uri):
        '''turn registry URI into URL on django site'''
        collection_id = uri.split('https://registry.cdlib.org/api/v1/collection/',
                                  1)[1][:-1]
        return reverse('calisphere:collectionView',
                       kwargs={'collection_id': collection_id})


    collections = CollectionManager(settings.SOLR_URL, settings.SOLR_API_KEY)
    data = [{ 'uri': djangoize(uri), 'title': title } for (uri, title) in collections.parsed]
    return JsonResponse(data, safe=False)


def collectionsSearch(request):
    return render(request, 'calisphere/collectionsTitleSearch.html', {'collections': [], 'collection_q': True})

def collectionView(request, collection_id):
    collection_url = 'https://registry.cdlib.org/api/v1/collection/' + collection_id + '/?format=json'
    collection_details = json_loads_url(collection_url)
    for repository in collection_details['repository']:
        repository['resource_id'] = repository['resource_uri'].split('/')[-2]

    # if request.method == 'GET' and len(request.GET.getlist('q')) > 0:
    queryParams = processQueryRequest(request)
    collection = getCollectionData(collection_id=collection_id)
    fq = solrize_filters(queryParams['filters'])
    fq.append('collection_url: "' + collection['url'] + '"')

    # Add Custom Facet Filter Types
    extra_facet_types = []
    if collection_details['custom_facet']:
      for i in range(len(collection_details['custom_facet'])):
        custom_facet = collection_details['custom_facet'][i]
        extra_facet_types.append({'facet': custom_facet['facet_field'], 'display_name': custom_facet['label'], 'filter': custom_facet['facet_field']})

      # Add custom facet only if doesn't already exist.
      [FACET_FILTER_TYPES.append(facet) for facet in extra_facet_types if facet not in FACET_FILTER_TYPES]

    else:
      # If collection_details['custom_facet'] is empty, remove extra facet types from FACET_FILTER_TYPES.
      if len(FACET_FILTER_TYPES) > len(DEFAULT_FACET_FILTER_TYPES):
        [FACET_FILTER_TYPES.remove(facet) for facet in FACET_FILTER_TYPES if facet not in DEFAULT_FACET_FILTER_TYPES]

    facet_fields = list(facet_filter_type['facet'] for facet_filter_type in FACET_FILTER_TYPES if facet_filter_type['facet'] != 'collection_data')

    # perform the search
    solr_search = SOLR_select(
        q=queryParams['query_terms'],
        rows=queryParams['rows'],
        start=queryParams['start'],
        sort=solrize_sort(queryParams['sort']),
        fq=fq,
        facet='true',
        facet_mincount=1,
        facet_limit='-1',
        facet_field=facet_fields
    )

    facets = facetQuery(facet_fields, queryParams, solr_search, 'collection_url: "' + collection['url'] + '"')

    for i, facet_item in enumerate(facets['repository_data']):
        repository = (getRepositoryData(repository_data=facet_item[0]), facet_item[1])
        facets['repository_data'][i] = repository

    filter_display = {}
    for filter_type in queryParams['filters']:
        if filter_type == 'collection_url':
            filter_display['collection_url'] = []
        elif filter_type == 'repository_url':
            filter_display['repository_url'] = []
            for filter_item in queryParams['filters'][filter_type]:
                repository_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/repository/(?P<url>\d*)/', filter_item)
                if repository_api_url is not None:
                    repository = getRepositoryData(repository_id=repository_api_url.group('url'))
                    repository.pop('local_id', None)
                    filter_display['repository_url'].append(repository)
        else:
            filter_display[filter_type] = copy.copy(queryParams['filters'][filter_type])

    return render(request, 'calisphere/collectionView.html', {
        'q': queryParams.get('q'),
        'rq': queryParams.get('rq'),
        'filters': filter_display,
        'rows': queryParams.get('rows'),
        'start': queryParams.get('start'),
        'sort': queryParams.get('sort'),
        'search_results': solr_search.results,
        'facets': facets,
        'FACET_FILTER_TYPES': list(facet_filter_type for facet_filter_type in FACET_FILTER_TYPES if facet_filter_type['facet'] != 'collection_data' and facet_filter_type['facet'] != 'repository_data'),
        'numFound': solr_search.numFound,
        'pages': int(math.ceil(float(solr_search.numFound)/int(queryParams['rows']))),
        'view_format': queryParams.get('view_format'),
        'collection': collection_details,
        'collection_id': collection_id,
        'form_action': reverse('calisphere:collectionView', kwargs={'collection_id': collection_id}),
    })

def campusDirectory(request):
    repositories_solr_query = SOLR_select(q='*:*', rows=0, start=0, facet='true', facet_mincount=1, facet_field=['repository_data'], facet_limit='-1')
    solr_repositories = repositories_solr_query.facet_counts['facet_fields']['repository_data']

    repositories = []
    for repository_data in solr_repositories:
        repository = getRepositoryData(repository_data=repository_data)
        if repository['campus']:
            repositories.append({
                'name': repository['name'],
                'campus': repository['campus'],
                'repository_id': re.match(r'https://registry\.cdlib\.org/api/v1/repository/(?P<repository_id>\d*)/?', repository['url']).group('repository_id')
            })

    repositories = sorted(repositories, key=lambda repository: (repository['campus'], repository['name']))
    # Use hard-coded campus list so UCLA ends up in the correct order
    # campuses = sorted(list(set([repository['campus'] for repository in repositories])))

    return render(
        request,
        'calisphere/campusDirectory.html', {
            'repositories': repositories,
            'campuses': CAMPUS_LIST,
            'state_repositories': None,
            'description': None,
        }
    )

def statewideDirectory(request):
    repositories_solr_query = SOLR_select(q='*:*', rows=0, start=0, facet='true', facet_mincount=1, facet_field=['repository_data'], facet_limit='-1')
    solr_repositories = repositories_solr_query.facet_counts['facet_fields']['repository_data']

    repositories = []
    for repository_data in solr_repositories:
        repository = getRepositoryData(repository_data=repository_data)
        if repository['campus'] == '':
            repositories.append({
                'name': repository['name'],
                'repository_id': re.match(r'https://registry\.cdlib\.org/api/v1/repository/(?P<repository_id>\d*)/?', repository['url']).group('repository_id')
            })

    binned_repositories = []
    bin = []
    for repository in repositories:
        if repository['name'][0] in string.punctuation:
            bin.append(repository)
    if len(bin) > 0:
        binned_repositories.append({'punctuation': bin})

    for char in string.ascii_uppercase:
        bin = []
        for repository in repositories:
            if repository['name'][0] == char or repository['name'][0] == char.upper:
                bin.append(repository)
        if len(bin) > 0:
            bin.sort()
            binned_repositories.append({char: bin})

    return render(
        request,
        'calisphere/statewideDirectory.html', {
            'state_repositories': binned_repositories,
            'campuses': None,
            'meta_image': None,
            'description': None,
            'q': None,
        }
    )


def institutionView(request, institution_id, subnav=False, institution_type='repository|campus'):
    institution_url = 'https://registry.cdlib.org/api/v1/' + institution_type + '/' + institution_id + '/'
    institution_details = json_loads_url(institution_url + "?format=json")
    if 'ark' in institution_details and institution_details['ark'] != '':
        contact_information = json_loads_url("http://dsc.cdlib.org/institution-json/" + institution_details['ark'])
    else:
        contact_information = ''

    if 'campus' in institution_details and len(institution_details['campus']) > 0:
        uc_institution = institution_details['campus']
    else:
        uc_institution = False

    if subnav == 'items':
        queryParams = processQueryRequest(request)
        fq = solrize_filters(queryParams['filters'])

        if institution_type == 'repository':
            fq.append('repository_url: "' + institution_url + '"')
            facet_fields = list(facet_filter_type['facet'] for facet_filter_type in FACET_FILTER_TYPES if facet_filter_type['facet'] != 'repository_data')

        if institution_type == 'campus':
            queryParams['campus_slug'] = institution_details['slug']
            fq.append('campus_url: "' + institution_url + '"')
            facet_fields = list(facet_filter_type['facet'] for facet_filter_type in FACET_FILTER_TYPES)

        solr_search = SOLR_select(
            q=queryParams['query_terms'],
            rows=queryParams['rows'],
            start=queryParams['start'],
            sort=solrize_sort(queryParams['sort']),
            fq=fq,
            facet='true',
            facet_mincount=1,
            facet_limit='-1',
            facet_field=facet_fields
        )

        if institution_type == 'repository':
            facets = facetQuery(facet_fields, queryParams, solr_search, 'repository_url: "' + institution_url + '"')
        elif institution_type == 'campus':
            facets = facetQuery(facet_fields, queryParams, solr_search, 'campus_url: "' + institution_url + '"')
        else:
            facets = facetQuery(facet_fields, queryParams, solr_search)

        for i, facet_item in enumerate(facets['collection_data']):
            collection = (getCollectionData(collection_data=facet_item[0]), facet_item[1])
            facets['collection_data'][i] = collection

        if institution_type == 'campus':
            for i, facet_item in enumerate(facets['repository_data']):
                repository = (getRepositoryData(repository_data=facet_item[0]), facet_item[1])
                facets['repository_data'][i] = repository

        filter_display = {}
        for filter_type in queryParams['filters']:
            if filter_type == 'collection_url':
                filter_display['collection_url'] = []
                for filter_item in queryParams['filters'][filter_type]:
                    collection_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/collection/(?P<url>\d*)/?', filter_item)
                    if collection_api_url is not None:
                        collection = getCollectionData(collection_id=collection_api_url.group('url'))
                        collection.pop('local_id', None)
                        filter_display['collection_url'].append(collection)
            elif filter_type == 'repository_url':
                filter_display['repository_url'] = []
                for filter_item in queryParams['filters'][filter_type]:
                    repository_api_url = re.match(r'^https://registry\.cdlib\.org/api/v1/repository/(?P<url>\d*)/', filter_item)
                    if repository_api_url is not None:
                        repository = getRepositoryData(repository_id=repository_api_url.group('url'))
                        repository.pop('local_id', None)
                        filter_display['repository_url'].append(repository)
            else:
                filter_display[filter_type] = copy.copy(queryParams['filters'][filter_type])

        context = {
            'q': queryParams['q'],
            'rq': queryParams['rq'],
            'filters': filter_display,
            'rows': queryParams['rows'],
            'start': queryParams['start'],
            'sort': queryParams['sort'],
            'search_results': solr_search.results,
            'facets': facets,
            'numFound': solr_search.numFound,
            'pages': int(math.ceil(float(solr_search.numFound)/int(queryParams['rows']))),
            'view_format': queryParams['view_format'],
            'institution': institution_details,
            'contact_information': contact_information,
        }

        if institution_type == 'campus':
            context['title'] = institution_details['name']
            context['FACET_FILTER_TYPES'] = FACET_FILTER_TYPES
            context['campus_slug'] = institution_details['slug']
            context['form_action'] = reverse('calisphere:campusView', kwargs={'campus_slug': institution_details['slug'], 'subnav': 'items'})
            for campus in CAMPUS_LIST:
                if institution_id == campus['id'] and 'featuredImage' in campus:
                    context['featuredImage'] = campus['featuredImage']

        if institution_type == 'repository':
            context['FACET_FILTER_TYPES'] = list(facet_filter_type for facet_filter_type in FACET_FILTER_TYPES if facet_filter_type['facet'] != 'repository_data')
            context['repository_id'] = institution_id
            context['uc_institution'] = uc_institution
            context['form_action'] = reverse('calisphere:repositoryView', kwargs={'repository_id': institution_id, 'subnav': 'items'})

            # title for UC institutions needs to show parent campus
            if uc_institution:
                context['title'] = u'{0} / {1}'.format(
                    uc_institution[0]['name'],
                    institution_details['name']
                )
            else:
                context['title'] = institution_details['name']

            if uc_institution == False:
                for unit in FEATURED_UNITS:
                    if unit['id'] == institution_id:
                        context['featuredImage'] = unit['featuredImage']

            # add institution_data to query params for related collections
            institution_data = institution_url + "::" + institution_details['name']
            if len(institution_details['campus']) > 0:
                institution_data = institution_data + "::" + institution_details['campus'][0]['name']
            queryParams['filters']['repository_data'] = [institution_data]

        context['related_collections'] = relatedCollections(request, queryParams)
        context['num_related_collections'] = len(queryParams['filters']['collection_url']) if len(queryParams['filters']['collection_url']) > 0 else len(facets['collection_data'])
        context['rc_page'] = queryParams['rc_page']

        return render(request, 'calisphere/institutionViewItems.html', context)

    else:
        page = int(request.GET['page']) if 'page' in request.GET else 1

        if institution_type == 'repository':
            institutions_fq = ['repository_url: "' + institution_url + '"']
        if institution_type == 'campus':
            institutions_fq = ['campus_url: "' + institution_url + '"']

        collections_solr_search = SOLR_select(
            q='',
            rows=0,
            start=0,
            fq=institutions_fq,
            facet='true',
            facet_mincount=1,
            facet_limit='-1',
            facet_field=['sort_collection_data']
        )

        pages = int(math.ceil(float(len(collections_solr_search.facet_counts['facet_fields']['sort_collection_data']))/10))
        # doing the search again;
        # could we slice this from the results above?
        collections_solr_search = SOLR_select(
            q='',
            rows=0,
            start=0,
            fq=institutions_fq,
            facet='true',
            facet_mincount=1,
            facet_offset=(page-1)*10,
            facet_limit='10',
            facet_field=['sort_collection_data'],
            facet_sort='index',
        )

        # solrpy gives us a dict == unsorted (!)
        # use the `facet_decade` mode of process_facets to do a lexical sort by value ....
        related_collections = list(
            collection[0] for collection in process_facets(
                collections_solr_search.facet_counts['facet_fields']['sort_collection_data'],
                [],
                'facet_decade',
            )
        )
        for i, related_collection in enumerate(related_collections):
            collection_parts = process_sort_collection_data(related_collection)
            collection_data = getCollectionData(
                collection_data=u'{0}::{1}'.format(
                    collection_parts[2],
                    collection_parts[1],
                )
            )
            related_collections[i] = getCollectionMosaic(collection_data['url'])

        context = {
            'page': page,
            'pages': pages,
            'collections': related_collections,
            'contact_information': contact_information,
            'institution': institution_details,
        }

        if page+1 <= pages:
            context['next_page'] = page+1
        if page-1 > 0:
            context['prev_page'] = page-1


        if institution_type == 'campus':
            context['campus_slug'] = institution_details['slug']
            context['title'] = institution_details['name']
            for campus in CAMPUS_LIST:
                if institution_id == campus['id'] and 'featuredImage' in campus:
                    context['featuredImage'] = campus['featuredImage']
            context['repository_id'] = None

        if institution_type == 'repository':
            context['repository_id'] = institution_id
            context['uc_institution'] = uc_institution
            # title for UC institutions needs to show parent campus
            # refactor, as this is copy/pasted in this commit
            if uc_institution:
                context['title'] = u'{0} / {1}'.format(
                    uc_institution[0]['name'],
                    institution_details['name']
                )
            else:
                context['title'] = institution_details['name']


            if uc_institution == False:
                for unit in FEATURED_UNITS:
                    if unit['id'] == institution_id:
                        context['featuredImage'] = unit['featuredImage']

            if not 'featuredImage' in context:
                context['featuredImage'] = None

        return render(request, 'calisphere/institutionViewCollections.html', context)

def campusView(request, campus_slug, subnav=False):
    campus_id = ''
    featured_image = ''
    for campus in CAMPUS_LIST:
        if campus_slug == campus['slug']:
            campus_id = campus['id']
            campus_name = campus['name']
            if 'featuredImage' in campus:
                featured_image = campus['featuredImage']
    if campus_id == '':
        print "Campus registry ID not found"

    if subnav == 'institutions':
        campus_url = 'https://registry.cdlib.org/api/v1/campus/' + campus_id + '/'
        campus_details = json_loads_url(campus_url + "?format=json")

        if 'ark' in campus_details and campus_details['ark'] != '':
            contact_information = json_loads_url("http://dsc.cdlib.org/institution-json/" + campus_details['ark'])
        else:
            contact_information = ''

        campus_fq = ['campus_url: "' + campus_url + '"']

        institutions_solr_search = SOLR_select(
            q='',
            rows=0,
            start=0,
            fq=campus_fq,
            facet='true',
            facet_mincount=1,
            facet_limit='-1',
            facet_field = ['repository_data']
        )

        related_institutions = list(institution[0] for institution in process_facets(institutions_solr_search.facet_counts['facet_fields']['repository_data'], []))

        for i, related_institution in enumerate(related_institutions):
            related_institutions[i] = getRepositoryData(repository_data=related_institution)
        related_institutions = sorted(related_institutions, key=lambda related_institution: related_institution['name'])


        return render(request, 'calisphere/institutionViewInstitutions.html', {
            'title': campus_name,
            'featuredImage': featured_image,
            'campus_slug': campus_slug,
            'institutions': related_institutions,
            'institution': campus_details,
            'contact_information': contact_information
        })

    else:
        return institutionView(request, campus_id, subnav, 'campus')

def repositoryView(request, repository_id, subnav=False):
    return institutionView(request, repository_id, subnav, 'repository')

def contactOwner(request):
    # print request.GET
    return render(request, 'calisphere/thankyou.html');

def posters(request):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    this_data = os.path.join(this_dir, 'poster-data.json')
    poster_data = json.loads(open(this_data).read())
    poster_data = sorted(poster_data.items())

    return render(request, 'calisphere/posters.html', {
        'poster_data': poster_data 
    })

def sitemapSection(request, section):
    storage = _lazy_load(conf.STORAGE_CLASS)(location=conf.ROOT_DIR)
    path = os.path.join(conf.ROOT_DIR, 'sitemap-{}.xml'.format(section))

    f = storage.open(path)
    content = f.readlines()
    f.close()
    return HttpResponse(content, content_type='application/xml')

def sitemapSectionZipped(request, section):
    storage = _lazy_load(conf.STORAGE_CLASS)(location=conf.ROOT_DIR)
    path = os.path.join(conf.ROOT_DIR, 'sitemap-{}.xml.gz'.format(section))

    f = storage.open(path)
    content = f.readlines()
    f.close()
    return HttpResponse(content, content_type='application/zip')
