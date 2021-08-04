from future import standard_library
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import Http404, HttpResponse, QueryDict
from . import constants
from . import facet_filter_type as facet_module
from .cache_retry import SOLR_select, SOLR_raw, json_loads_url
from . import search_form
from .collection_views import Collection, get_related_collections
from .institution_views import Repository
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

col_regex = (r'https://registry\.cdlib\.org/api/v1/collection/'
             r'(?P<id>\d*)/?')
col_template = "https://registry.cdlib.org/api/v1/collection/{0}/"
repo_regex = (r'https://registry\.cdlib\.org/api/v1/repository/'
              r'(?P<id>\d*)/?')


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


def get_component(media_json, order):
    component = media_json['structMap'][order]
    component['selected'] = True
    if 'format' in component:
        media_data = component

    # remove emptry strings from list
    for k, v in list(component.items()):
        if isinstance(v, list) and isinstance(v[0], str):
            component[k] = [
                name for name in v if name and name.strip()
            ]
    component = dict((k, v) for k, v in list(component.items()) if v)

    return component, media_data


def item_view(request, item_id=''):
    item_id_search_term = 'id:"{0}"'.format(item_id)
    item_solr_search = SOLR_select(q=item_id_search_term)
    order = request.GET.get('order')

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

    item = item_solr_search.results[0]
    if 'reference_image_dimensions' in item:
        split_ref = item['reference_image_dimensions'].split(':')
        item['reference_image_dimensions'] = split_ref
    if 'structmap_url' in item and len(item['structmap_url']) >= 1:
        item['harvest_type'] = 'hosted'
        structmap_url = item['structmap_url'].replace(
            's3://static', 'https://s3.amazonaws.com/static')
        media_json = json_loads_url(structmap_url)

        media_data = None

        # simple object
        if 'structMap' not in media_json:
            if 'format' in media_json:
                media_data = media_json

        # complex object
        if 'structMap' in media_json:
            # complex object
            if order and 'structMap' in media_json:
                # fetch component object
                item['selected'] = False
                item['selectedComponentIndex'] = int(order)
                component, media_data = get_component(media_json, int(order))
                item['selectedComponent'] = component
            else:
                item['selected'] = True
                if 'format' in media_json:
                    media_data = media_json
                else:
                    media_data = media_json['structMap'][0]
            item['contentFile'] = get_hosted_content_file(media_data)
            item['structMap'] = media_json['structMap']

            # single or multi-format object
            formats = [
                component['format']
                for component in media_json['structMap']
                if 'format' in component
            ]
            item['multiFormat'] = False
            if len(set(formats)) > 1:
                item['multiFormat'] = True

            # carousel has captions or not
            item['hasComponentCaptions'] = True
            if all(f == 'image' for f in formats):
                item['hasComponentCaptions'] = False

            # number of components
            item['componentCount'] = len(media_json['structMap'])

            # has fixed item thumbnail image
            item['has_fixed_thumb'] = False
            if 'reference_image_md5' in item:
                item['has_fixed_thumb'] = True

        item['contentFile'] = get_hosted_content_file(media_data)
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
        col_id = (re.match(
            col_regex, collection_data.split('::')[0]).group('id'))
        collection = Collection(col_id)
        item['parsed_collection_data'].append(collection.item_view())

    for repository_data in item.get('repository_data'):
        repo_id = re.match(
            repo_regex, repository_data.split('::')[0]).group('id')
        repo = Repository(repo_id)
        item['parsed_repository_data'].append(repo.get_repo_data())
        item['institution_contact'].append(repo.get_contact_info())

    meta_image = False
    if item.get('reference_image_md5', False):
        meta_image = urllib.parse.urljoin(
            settings.UCLDC_FRONT,
            '/crop/999x999/{0}'.format(
                item['reference_image_md5']),
        )

    if item.get('rights_uri'):
        uri = item.get('rights_uri')
        item['rights_uri'] = {
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
                'item': item,
                'item_solr_search': item_solr_search,
                'meta_image': meta_image,
                'repository_id': None,
                'itemId': None,
            })
    search_results = {'reference_image_md5': None}
    search_results.update(item)
    related_collections, num_related_collections = (
        get_related_collections(item_id_query))
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
        form = search_form.SearchForm(request)
        results = form.search()
        facets = form.facet_query()
        filter_display = form.filter_display

        params = request.GET.copy()
        context = {
            'facets': facets,
            'q': form.q,
            'search_form': form.context(),
            'search_results': results.results,
            'numFound': results.numFound,
            'pages': int(math.ceil(results.numFound / int(form.rows))),
            'related_collections': get_related_collections(params)[0],
            'num_related_collections':
            len(params.getlist('collection_data'))
            if len(params.getlist('collection_data')) > 0 else len(
                facets['collection_data']),
            'form_action': reverse('calisphere:search'),
            'FACET_FILTER_TYPES': form.facet_filter_types,
            'filters': filter_display,
            'repository_id': None,
            'itemId': None,
        }

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
        custom_facets = Collection(link_back_id).custom_facets
        facet_filter_types.extend(custom_facets)
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

    solr_params = search_form.solr_encode(params, facet_filter_types)
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
        context = search_form.search_defaults(params)
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
    collection_url = col_template.format(collection_id)
    collection_details = json_loads_url(collection_url + '?format=json')
    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))

    for repository in collection_details.get('repository'):
        repository['resource_id'] = repository.get('resource_uri').split(
            '/')[-2]

    context = search_form.SearchForm(request).context()
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
    collection_url = col_template.format(collection_id)
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
    escaped_facet_value = search_form.solr_escape(parsed_facet_value)
    params.update({'fq': f"{facet}_ss:\"{escaped_facet_value}\""})
    if 'view_format' not in params:
        params.update({'view_format': 'list'})
    if 'rows' not in params:
        params.update({'rows': '48'})
    if 'sort' not in params:
        params.update({'sort': 'oldest-end'})

    context = search_form.search_defaults(params)

    # Collection Views don't allow filtering or faceting by
    # collection_data or repository_data
    facet_filter_types = [
        facet_filter_type for facet_filter_type in constants.FACET_FILTER_TYPES
        if facet_filter_type['facet'] != 'collection_data'
        and facet_filter_type['facet'] != 'repository_data'
    ]

    extra_filter = 'collection_url: "' + collection_url + '"'

    # perform the search
    solr_params = search_form.solr_encode(params, facet_filter_types)
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

    # context['facets'] = search_form.facet_query(
    #    facet_filter_types, params, solr_search, extra_filter)

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
