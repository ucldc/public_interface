from future import standard_library
from builtins import range
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import Http404, HttpResponse, QueryDict
from . import constants
from . import facet_filter_type as facet_module
from .cache_retry import SOLR_select, SOLR_raw, json_loads_url
from static_sitemaps.util import _lazy_load
from static_sitemaps import conf
from requests.exceptions import HTTPError
from exhibits.models import ExhibitItem, Exhibit

import os
import math
import re
import copy
import simplejson as json
import urllib.parse

standard_library.install_aliases()


def get_more_collection_data(collection_data):
    collection = facet_module.getCollectionData(
        collection_data=collection_data,
        collection_id=None,
    )
    collection_details = json_loads_url("{0}?format=json".format(
        collection['url']))
    if not collection_details:
        return None

    collection['local_id'] = collection_details['local_id']
    collection['slug'] = collection_details['slug']
    collection['harvest_type'] = collection_details['harvest_type']
    collection['custom_facet'] = collection_details['custom_facet']

    production_disqus = (
        settings.UCLDC_FRONT == 'https://calisphere.org/' or
        settings.UCLDC_DISQUS == 'prod'
    )
    if production_disqus:
        collection['disqus_shortname'] = collection_details.get(
            'disqus_shortname_prod')
    else:
        collection['disqus_shortname'] = collection_details.get(
            'disqus_shortname_test')

    return collection


def get_collection_mosaic(collection_url):
    # get collection information from collection registry
    collection_details = json_loads_url(collection_url + "?format=json")

    if not collection_details:
        return None

    collection_repositories = []
    for repository in collection_details.get('repository'):
        if 'campus' in repository and len(repository['campus']) > 0:
            collection_repositories.append(repository['campus'][0]['name'] +
                                           ", " + repository['name'])
        else:
            collection_repositories.append(repository['name'])

    # get 6 image items from the collection for the mosaic preview
    search_terms = {
        'q': '*:*',
        'fields':
        'reference_image_md5, url_item, id, title, collection_url, type_ss',
        'sort': 'sort_title asc',
        'rows': 6,
        'start': 0,
        'fq':
        ['collection_url: \"' + collection_url + '\"', 'type_ss: \"image\"']
    }
    display_items = SOLR_select(**search_terms)
    items = display_items.results

    search_terms['fq'] = [
        'collection_url: \"' + collection_url + '\"',
        '(*:* AND -type_ss:\"image\")'
    ]
    ugly_display_items = SOLR_select(**search_terms)
    # if there's not enough image items, get some non-image
    # items for the mosaic preview
    if len(items) < 6:
        items = items + ugly_display_items.results

    return {
        'name': collection_details['name'],
        'description': collection_details['description'],
        'collection_id': collection_details['id'],
        'institutions': collection_repositories,
        'numFound': display_items.numFound + ugly_display_items.numFound,
        'display_items': items
    }


def facet_query(facet_filter_types, params, solr_search, extra_filter=None):
    # get facet counts
    # if the user's selected some of the available facets (ie - there are
    # filters selected for this field type) perform a search as if those
    # filters were not applied to obtain facet counts
    #
    # since we AND filters of the same type, counts should go UP when
    # more than one facet is selected as a filter, not DOWN (or'ed filters
    # of the same type)

    facets = {}
    for facet_filter_type in facet_filter_types:
        facet_type = facet_filter_type['facet']
        if (len(params.getlist(facet_type)) > 0):
            exclude_facets_of_type = params.copy()
            exclude_facets_of_type.pop(facet_type)

            solr_params = solr_encode(exclude_facets_of_type,
                                      facet_filter_types,
                                      [facet_filter_type])
            if extra_filter:
                solr_params['fq'].append(extra_filter)
            facet_search = SOLR_select(**solr_params)

            solr_facets = facet_search.facet_counts['facet_fields'][facet_type]
        else:
            solr_facets = solr_search.facet_counts['facet_fields'][facet_type]

        facets[facet_type] = facet_filter_type.process_facets(
            solr_facets,
            params.getlist(facet_type)
        )

        for j, facet_item in enumerate(facets[facet_type]):
            facets[facet_type][j] = (facet_filter_type.facet_transform(
                facet_item[0]), facet_item[1])

    return facets


def search_defaults(params):
    context = {
        'q': params.get('q', ''),
        'rq': params.getlist('rq'),
        'rows': params.get('rows', '24'),
        'start': params.get('start', 0),
        'sort': params.get('sort', 'relevance'),
        'view_format': params.get('view_format', 'thumbnails'),
        'rc_page': params.get('rc_page', 0)
    }
    return context


def solr_escape(text):
    return text.replace('?', '\\?').replace('"', '\\"')


def solr_encode(params, filter_types, facet_types=[]):
    if len(facet_types) == 0:
        facet_types = filter_types

    # concatenate query terms from refine query and query box
    query_terms = []
    q = params.get('q')
    if q:
        query_terms.append(solr_escape(q))

    for qt in params.getlist('rq'):
        if qt:
            query_terms.append(solr_escape(qt))

    for qt in params.getlist('fq'):
        if qt:
            query_terms.append(qt)

    if len(query_terms) == 1:
        query_terms_string = query_terms[0]
    else:
        query_terms_string = " AND ".join(query_terms)

    # query_terms_string = query_terms_string.replace('?', '')

    filters = []
    for filter_type in filter_types:
        selected_filters = params.getlist(filter_type['facet'])
        if (len(selected_filters) > 0):
            filter_transform = filter_type['filter_transform']

            selected_filters = list([
                '{0}: "{1}"'.format(filter_type['filter'],
                                    solr_escape(filter_transform(filter_val)))
                for filter_val in selected_filters
            ])
            selected_filters = " OR ".join(selected_filters)
            filters.append(selected_filters)

    try:
        rows = int(params.get('rows', 24))
        start = int(params.get('start', 0))
    except ValueError as err:
        raise Http404("{0} does not exist".format(err))

    query_value = {
        'q':
        query_terms_string,
        'rows': rows,
        'start': start,
        'sort':
        constants.SORT_OPTIONS[
            params.get('sort', 'relevance' if query_terms else 'a')
        ],
        'fq':
        filters,
        'facet':
        'true',
        'facet_mincount':
        1,
        'facet_limit':
        '-1',
        'facet_field':
        list(facet_type['facet'] for facet_type in facet_types)
    }

    query_fields = params.get('qf')
    if query_fields:
        query_value.update({'qf': query_fields})

    return query_value


def get_hosted_content_file(structmap):
    content_file = ''
    if structmap['format'] == 'image':
        iiif_url = '{}{}/info.json'.format(settings.UCLDC_IIIF,
                                           structmap['id'])
        if iiif_url.startswith('//'):
            iiif_url = ''.join(['http:', iiif_url])
        iiif_info = json_loads_url(iiif_url)
        if not iiif_info:
            return None
        size = iiif_info.get('sizes', [])[-1]
        if size['height'] > size['width']:
            access_size = {
                'width': ((size['width'] * 1024) // size['height']),
                'height': 1024
            }
            access_url = iiif_info['@id'] + "/full/,1024/0/default.jpg"
        else:
            access_size = {
                'width': 1024,
                'height': ((size['height'] * 1024) // size['width'])
            }
            access_url = iiif_info['@id'] + "/full/1024,/0/default.jpg"

        content_file = {
            'titleSources': iiif_info,
            'format': 'image',
            'size': access_size,
            'url': access_url
        }
    if structmap['format'] == 'file':
        content_file = {
            'id': structmap['id'],
            'format': 'file',
        }
    if structmap['format'] == 'video':
        access_url = os.path.join(settings.UCLDC_MEDIA, structmap['id'])
        content_file = {
            'id': structmap['id'],
            'format': 'video',
            'url': access_url
        }
    if structmap['format'] == 'audio':
        access_url = os.path.join(settings.UCLDC_MEDIA, structmap['id'])
        content_file = {
            'id': structmap['id'],
            'format': 'audio',
            'url': access_url
        }

    return content_file


def item_view(request, item_id=''):
    item_id_search_term = 'id:"{0}"'.format(item_id)
    item_solr_search = SOLR_select(q=item_id_search_term)
    if not item_solr_search.numFound:
        # second level search
        def _fixid(id):
            return re.sub(r'^(\d*--http:/)(?!/)', r'\1/', id)

        old_id_search = SOLR_select(
            q='harvest_id_s:*{}'.format(_fixid(item_id)))
        if old_id_search.numFound:
            return redirect('calisphere:itemView',
                            old_id_search.results[0]['id'])
        else:
            raise Http404("{0} does not exist".format(item_id))

    for item in item_solr_search.results:
        if 'reference_image_dimensions' in item:
            split_ref = item['reference_image_dimensions'].split(':')
            item['reference_image_dimensions'] = split_ref
        if 'structmap_url' in item and len(item['structmap_url']) >= 1:
            item['harvest_type'] = 'hosted'
            structmap_url = item['structmap_url'].replace(
                's3://static', 'https://s3.amazonaws.com/static')
            structmap_data = json_loads_url(structmap_url)

            if 'structMap' in structmap_data:
                # complex object
                if 'order' in request.GET and 'structMap' in structmap_data:
                    # fetch component object
                    item['selected'] = False
                    order = int(request.GET['order'])
                    item['selectedComponentIndex'] = order
                    component = structmap_data['structMap'][order]
                    component['selected'] = True
                    if 'format' in component:
                        item['contentFile'] = get_hosted_content_file(
                            component)
                    # remove emptry strings from list
                    for k, v in list(component.items()):
                        if isinstance(v, list):
                            if isinstance(v[0], str):
                                component[k] = [
                                    name for name in v if name and name.strip()
                                ]
                    # remove empty lists and empty strings from dict
                    item['selectedComponent'] = dict(
                        (k, v) for k, v in list(component.items()) if v)
                else:
                    item['selected'] = True
                    # if parent content file, get it
                    if 'format' in structmap_data:
                        item['contentFile'] = get_hosted_content_file(
                            structmap_data)
                    # otherwise get first component file
                    else:
                        component = structmap_data['structMap'][0]
                        item['contentFile'] = get_hosted_content_file(
                            component)
                item['structMap'] = structmap_data['structMap']

                # single or multi-format object
                formats = [
                    component['format']
                    for component in structmap_data['structMap']
                    if 'format' in component
                ]
                if len(set(formats)) > 1:
                    item['multiFormat'] = True
                else:
                    item['multiFormat'] = False

                # carousel has captions or not
                if all(f == 'image' for f in formats):
                    item['hasComponentCaptions'] = False
                else:
                    item['hasComponentCaptions'] = True

                # number of components
                item['componentCount'] = len(structmap_data['structMap'])

                # has fixed item thumbnail image
                if 'reference_image_md5' in item:
                    item['has_fixed_thumb'] = True
                else:
                    item['has_fixed_thumb'] = False
            else:
                # simple object
                if 'format' in structmap_data:
                    item['contentFile'] = get_hosted_content_file(
                        structmap_data)
        else:
            item['harvest_type'] = 'harvested'
            if 'url_item' in item:
                if item['url_item'].startswith('http://ark.cdlib.org/ark:'):
                    item['oac'] = True
                    item['url_item'] = item['url_item'].replace(
                        'http://ark.cdlib.org/ark:',
                        'http://oac.cdlib.org/ark:')
                    item['url_item'] = item['url_item'] + '/?brand=oac4'
                else:
                    item['oac'] = False
            # TODO: error handling 'else'

        item['parsed_collection_data'] = []
        item['parsed_repository_data'] = []
        item['institution_contact'] = []
        for collection_data in item.get('collection_data'):
            parsed_collection_data = get_more_collection_data(collection_data)
            if parsed_collection_data:
                item['parsed_collection_data'].append(
                    get_more_collection_data(collection_data))
        for repository_data in item.get('repository_data'):
            item['parsed_repository_data'].append(
                facet_module.getRepositoryData(
                    repository_data=repository_data))

            institution_url = item['parsed_repository_data'][0]['url']
            institution_details = json_loads_url(institution_url +
                                                 "?format=json")
            if 'ark' in institution_details and institution_details[
                    'ark'] != '':
                contact_information = json_loads_url(
                    "http://dsc.cdlib.org/institution-json/" +
                    institution_details['ark'])
            else:
                contact_information = ''

            item['institution_contact'].append(contact_information)

    meta_image = False
    if item_solr_search.results[0].get('reference_image_md5', False):
        meta_image = urllib.parse.urljoin(
            settings.UCLDC_FRONT,
            '/crop/999x999/{0}'.format(
                item_solr_search.results[0]['reference_image_md5']),
        )

    if item_solr_search.results[0].get('rights_uri'):
        uri = item_solr_search.results[0].get('rights_uri')
        item_solr_search.results[0]['rights_uri'] = {
            'url': uri,
            'statement': constants.RIGHTS_STATEMENTS[uri]
        }

    # do this w/o multiple returns?
    from_item_page = request.META.get("HTTP_X_FROM_ITEM_PAGE")
    item_id_query = QueryDict(f'itemId={item_id}')
    if from_item_page:
        return render(
            request, 'calisphere/itemViewer.html', {
                'q': '',
                'item': item_solr_search.results[0],
                'item_solr_search': item_solr_search,
                'meta_image': meta_image,
                'repository_id': None,
                'itemId': None,
            })
    search_results = {'reference_image_md5': None}
    search_results.update(item_solr_search.results[0])
    related_collections, num_related_collections = get_related_collections(
        item_id_query)
    carousel_search_results, carousel_num_found = item_view_carousel_mlt(
        item_id)
    return render(
        request, 'calisphere/itemView.html', {
            'q': '',
            'item': search_results,
            'item_solr_search': item_solr_search,
            'meta_image': meta_image,
            'rc_page': None,
            'related_collections': related_collections,
            'slug': None,
            'title': None,
            'num_related_collections': num_related_collections,
            'rq': None,
            'search_results': carousel_search_results,
            'numFound': carousel_num_found,
            'mlt': True
        })


def search(request):
    if request.method == 'GET' and len(request.GET.getlist('q')) > 0:
        params = request.GET.copy()
        context = search_defaults(params)
        solr_query = solr_encode(params, constants.FACET_FILTER_TYPES)
        solr_search = SOLR_select(**solr_query)

        # TODO: create a no results found page
        if len(solr_search.results) == 0:
            print('no results found')

        context['facets'] = facet_query(
            constants.FACET_FILTER_TYPES, params, solr_search)

        context.update({
            'search_results':
            solr_search.results,
            'numFound':
            solr_search.numFound,
            'pages':
            int(math.ceil(
                    solr_search.numFound / int(context['rows']))),
            'related_collections':
            get_related_collections(params)[0],
            'num_related_collections':
            len(params.getlist('collection_data'))
            if len(params.getlist('collection_data')) > 0 else len(
                context['facets']['collection_data']),
            'form_action':
            reverse('calisphere:search'),
            'FACET_FILTER_TYPES':
            constants.FACET_FILTER_TYPES,
            'filters': {},
            'repository_id':
            None,
            'itemId':
            None,
        })

        for filter_type in constants.FACET_FILTER_TYPES:
            param_name = filter_type['facet']
            display_name = filter_type['filter']
            filter_transform = filter_type['filter_display']

            if len(params.getlist(param_name)) > 0:
                context['filters'][display_name] = list(
                    map(filter_transform, params.getlist(param_name)))

        return render(request, 'calisphere/searchResults.html', context)

    return redirect('calisphere:home')


def item_view_carousel_mlt(item_id):
    carousel_solr_search = SOLR_raw(
        q='id:' + item_id,
        fields='id, type_ss, reference_image_md5, title',
        mlt='true',
        mlt_count='24',
        mlt_fl='title,collection_name,subject',
        mlt_mintf=1,
    )
    if json.loads(carousel_solr_search)['response']['numFound'] == 0:
        raise Http404('No object with id "' + item_id + '" found.')
    search_results = json.loads(
        carousel_solr_search)['response']['docs'] + json.loads(
            carousel_solr_search)['moreLikeThis'][item_id]['docs']
    num_found = len(search_results)

    return search_results, num_found


def item_view_carousel(request):
    params = request.GET.copy()
    item_id = params.get('itemId')
    if item_id is None:
        raise Http404("No item id specified")

    referral = params.get('referral')
    link_back_id = ''
    extra_filter = ''
    facet_filter_types = copy.deepcopy(constants.FACET_FILTER_TYPES)
    if referral == 'institution':
        link_back_id = params.get('repository_data', None)
    elif referral == 'collection':
        link_back_id = params.get('collection_data', None)
        # get any collection-specific facets
        collection_url = (
            f'https://registry.cdlib.org/api/v1/collection/{link_back_id}/')
        collection_details = json_loads_url(collection_url + '?format=json')
        custom_facets = collection_details.get('custom_facet', [])
        for custom_facet in custom_facets:
            facet_filter_types.append(
                facet_module.FacetFilterType(
                    custom_facet['facet_field'],
                    custom_facet['label'],
                    custom_facet['facet_field'],
                    custom_facet.get('sort_by', 'count')
                )
            )
        # Add Custom Facet Filter Types
        if params.get('relation_ss') and len(custom_facets) == 0:
            facet_filter_types.append(
                facet_module.FacetFilterType(
                    'relation_ss',
                    'Relation',
                    'relation_ss',
                    'value',
                    faceting_allowed=False
                )
            )
    elif referral == 'campus':
        link_back_id = params.get('campus_slug', None)
        if link_back_id:
            campus = [c for c in constants.CAMPUS_LIST
                      if c['slug'] == link_back_id]
            campus_id = campus[0]['id']
            if not campus_id or campus_id == '':
                raise Http404("Campus registry ID not found")
            extra_filter = (
                f'campus_url: "https://registry.cdlib.org/api/v1/'
                f'campus/{campus_id}/"'
            )

    solr_params = solr_encode(params, facet_filter_types)
    if extra_filter:
        solr_params['fq'].append(extra_filter)

    # if no query string or filters, do a "more like this" search
    if solr_params['q'] == '' and len(solr_params['fq']) == 0:
        search_results, num_found = item_view_carousel_mlt(item_id)
    else:
        solr_params.update({
            'facet': 'false',
            'fields': 'id, type_ss, reference_image_md5, title'
        })
        if solr_params.get('start') == 'NaN':
            solr_params['start'] = 0

        try:
            carousel_solr_search = SOLR_select(**solr_params)
        except HTTPError as e:
            # https://stackoverflow.com/a/19384641/1763984
            print((request.get_full_path()))
            raise (e)
        search_results = carousel_solr_search.results
        num_found = carousel_solr_search.numFound

    if 'init' in params:
        context = search_defaults(params)
        context['start'] = solr_params[
            'start'] if solr_params['start'] != 'NaN' else 0

        context['filters'] = {}
        for filter_type in facet_filter_types:
            param_name = filter_type['facet']
            display_name = filter_type['filter']
            filter_transform = filter_type['filter_display']

            if len(params.getlist(param_name)) > 0:
                context['filters'][display_name] = list(
                    map(filter_transform, params.getlist(param_name)))

        context.update({
            'numFound': num_found,
            'search_results': search_results,
            'item_id': item_id,
            'referral': request.GET.get('referral'),
            'referralName': request.GET.get('referralName'),
            'campus_slug': request.GET.get('campus_slug'),
            'linkBackId': link_back_id
        })

        return render(request, 'calisphere/carouselContainer.html', context)
    else:
        return render(
            request, 'calisphere/carousel.html', {
                'start': params.get('start', 0),
                'search_results': search_results,
                'item_id': item_id
            })


def get_related_collections(params, slug=None, repository_id=None):
    solr_params = solr_encode(params, constants.FACET_FILTER_TYPES,
                              [{
                                'facet': 'collection_data'
                              }])
    solr_params['rows'] = 0

    slug = params.get('campus_slug') if params.get('campus_slug') else slug

    if slug:
        campus = [c for c in constants.CAMPUS_LIST if c['slug'] == slug]
        extra_filter = (
            'campus_url: "https://registry.cdlib.org/api/v1/'
            'campus/' + campus[0]['id'] + '/"'
        )
        solr_params['fq'].append(extra_filter)
    if repository_id:
        extra_filter = (
            f'repository_url: "https://registry.cdlib.org/api/v1/'
            f'repository/{repository_id}/"'
        )
        solr_params['fq'].append(extra_filter)

    # mlt search
    if len(solr_params['q']) == 0 and len(solr_params['fq']) == 0:
        if params.get('itemId'):
            solr_params['q'] = 'id:' + params.get('itemId', '')

    related_collections = SOLR_select(**solr_params)
    related_collections = related_collections.facet_counts['facet_fields'][
        'collection_data']

    field = constants.DEFAULT_FACET_FILTER_TYPES[3]
    collection_urls = list(
        map(field.filter_transform, params.getlist('collection_data')))
    # remove collections with a count of 0 and sort by count
    related_collections = field.process_facets(
        related_collections, collection_urls)
    # remove 'count'
    related_collections = list(facet for facet, count in related_collections)

    # get three items for each related collection
    three_related_collections = []
    rc_page = int(params.get('rc_page', 0))
    for i in range(rc_page * 3, rc_page * 3 + 3):
        if len(related_collections) > i:
            collection = facet_module.getCollectionData(related_collections[i])

            rc_solr_params = {
                'q': solr_params['q'],
                'rows': '3',
                'fq': ["collection_url: \"" + collection['url'] + "\""],
                'fields': (
                    'collection_data, reference_image_md5, '
                    'url_item, id, title, type_ss'
                )
            }

            collection_items = SOLR_select(**rc_solr_params)
            collection_items = collection_items.results

            if len(collection_items) < 3:
                rc_solr_params['q'] = ''
                collection_items_no_query = SOLR_select(**rc_solr_params)
                collection_items = (
                    collection_items + collection_items_no_query.results)

            if len(collection_items) > 0:
                collection_data = {
                    'image_urls': collection_items,
                    'name': collection['name'],
                    'collection_id': collection['id']
                }

                # TODO: get this from repository_data in solr rather than
                # from the registry API
                collection_details = json_loads_url(collection['url'] +
                                                    "?format=json")
                if (collection_details.get('repository')
                        and collection_details['repository'][0]['campus']):
                    collection_data[
                        'institution'] = collection_details['repository'][0][
                            'campus'][0]['name'] + ', ' + collection_details[
                                'repository'][0]['name']
                elif collection_details.get('repository'):
                    collection_data['institution'] = collection_details.get(
                        'repository')[0]['name']
                else:
                    collection_data['institution'] = None

                three_related_collections.append(collection_data)

    return three_related_collections, len(related_collections)


def related_collections(request, slug=None, repository_id=None):
    params = request.GET.copy()

    if not params:
        raise Http404("No parameters to provide related collections")

    three_rcs, num_related_collections = get_related_collections(
        params, slug, repository_id)

    context = {
        'q': params.get('q'),
        'rq': params.getlist('rq'),
        'num_related_collections': num_related_collections,
        'related_collections': three_rcs,
        'rc_page': int(params.get('rc_page')),
    }
    if len(params.getlist('itemId')) > 0:
        context['itemId'] = params.get('itemId')
    if len(params.getlist('referral')) > 0:
        context['referral'] = params.get('referral')
        context['referralName'] = params.get('referralName')
        if context['referral'] == 'institution' or context[
                'referral'] == 'campus':
            if (len(params.getlist('facet_decade')) > 0
                    or len(params.getlist('type_ss')) > 0
                    or len(params.getlist('collection_data')) > 0):
                context['filters'] = True
            if context['referral'] == 'campus' and len(
                    params.getlist('repository_data')) > 0:
                context['filters'] = True
    return render(request, 'calisphere/related-collections.html', context)


def related_exhibitions(request):
    params = request.GET.copy()
    if ('itemId' in params):
        exhibit_items = ExhibitItem.objects.select_related('exhibit').filter(
            item_id=params['itemId']).exclude(exhibit__isnull=True)
        exhibit_ids = [exhibit_item.exhibit.pk for exhibit_item
                       in exhibit_items]
        exhibits = Exhibit.objects.filter(pk__in=exhibit_ids)
    else:
        raise Http404("No item id provided for related exhibitions")

    return render(request, 'calisphere/related-exhibitions.html',
                  {'exhibits': exhibits})


def report_collection_facet(request, collection_id, facet):
    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} does not exist".format(facet))
    collection_url = (
        f'https://registry.cdlib.org/api/v1/collection/{collection_id}/')
    collection_details = json_loads_url(collection_url + '?format=json')
    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))

    for repository in collection_details.get('repository'):
        repository['resource_id'] = repository.get('resource_uri').split(
            '/')[-2]

    params = request.GET.copy()
    context = search_defaults(params)
    context.update({'facet': facet})
    # facet=true&facet.query=*&rows=0&facet.field=title_ss&facet.pivot=title_ss,collection_data"
    solr_params = {
        'facet': 'true',
        'rows': 0,
        'facet_field': '{}_ss'.format(facet),
        'fq': 'collection_url:"{}"'.format(collection_url),
        'facet_limit': '-1',
        'facet_mincount': 1,
        'facet_sort': 'count',
    }
    solr_search = SOLR_select(**solr_params)

    values = solr_search.facet_counts.get(
        'facet_fields').get('{}_ss'.format(facet))
    if not values:
        raise Http404("{0} has no values".format(facet))
    unique = len(values)
    records = sum(values.values())
    ratio = unique / records
    context.update({
        'values': values,
        'unique': unique,
        'records': records,
        'ratio': ratio
    })

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

    return render(request, 'calisphere/reportCollectionFacet.html', context)


def report_collection_facet_value(request, collection_id, facet, facet_value):
    collection_url = (
        f'https://registry.cdlib.org/api/v1/collection/{collection_id}/')
    collection_details = json_loads_url(collection_url + '?format=json')

    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))
    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
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
    if 'view_format' not in params:
        params.update({'view_format': 'list'})
    if 'rows' not in params:
        params.update({'rows': '48'})
    if 'sort' not in params:
        params.update({'sort': 'oldest-end'})

    context = search_defaults(params)

    # Collection Views don't allow filtering or faceting by
    # collection_data or repository_data
    facet_filter_types = [
        facet_filter_type for facet_filter_type in constants.FACET_FILTER_TYPES
        if facet_filter_type['facet'] != 'collection_data'
        and facet_filter_type['facet'] != 'repository_data'
    ]

    extra_filter = 'collection_url: "' + collection_url + '"'

    # perform the search
    solr_params = solr_encode(params, facet_filter_types)
    solr_params['fq'].append(extra_filter)
    solr_search = SOLR_select(**solr_params)
    context['search_results'] = solr_search.results
    context['numFound'] = solr_search.numFound
    total_items = SOLR_select(**{**solr_params, **{
        'q': '',
        'fq': [extra_filter],
        'rows': 0,
        'facet': 'false'
    }})

    context['pages'] = int(
        math.ceil(solr_search.numFound / int(context['rows'])))

    # context['facets'] = facet_query(facet_filter_types, params, solr_search,
    #                               extra_filter)

    collection_name = collection_details.get('name')
    context.update({'facet': facet})
    context.update({'facet_value': parsed_facet_value})
    context.update({
        'meta_robots': "noindex,nofollow",
        'totalNumItems': total_items.numFound,
        'FACET_FILTER_TYPES': facet_filter_types,
        'collection': collection_details,
        'collection_id': collection_id,
        'title': (
            f"{facet}: {parsed_facet_value} ({solr_search.numFound} items)"
            f" from: {collection_name}"),
        'description': None,
        'solrParams': solr_params,
        'form_action': reverse(
            'calisphere:reportCollectionFacetValue',
            kwargs={
              'collection_id': collection_id,
              'facet': facet,
              'facet_value': facet_value,
            }),
    })

    return render(
        request, 'calisphere/reportCollectionFacetValue.html', context)


def contact_owner(request):
    # print request.GET
    return render(request, 'calisphere/thankyou.html')


def posters(request):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    this_data = os.path.join(this_dir, 'poster-data.json')
    poster_data = json.loads(open(this_data).read())
    poster_data = sorted(poster_data.items())

    return render(request, 'calisphere/posters.html',
                  {'poster_data': poster_data})


def sitemap_section(request, section):
    storage = _lazy_load(conf.STORAGE_CLASS)(location=conf.ROOT_DIR)
    path = os.path.join(conf.ROOT_DIR, 'sitemap-{}.xml'.format(section))

    try:
        f = storage.open(path)
    except FileNotFoundError:
        raise Http404("{0} does not exist".format(section))

    content = f.readlines()
    f.close()
    return HttpResponse(content, content_type='application/xml')


def sitemap_section_zipped(request, section):
    storage = _lazy_load(conf.STORAGE_CLASS)(location=conf.ROOT_DIR)
    path = os.path.join(conf.ROOT_DIR, 'sitemap-{}.xml.gz'.format(section))

    try:
        f = storage.open(path)
    except FileNotFoundError:
        raise Http404("{0} does not exist".format(section))

    content = f.readlines()
    f.close()
    return HttpResponse(content, content_type='application/zip')
