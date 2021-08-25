from future import standard_library
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import Http404, HttpResponse
from . import constants
from . import facet_filter_type as facet_module
from .cache_retry import SOLR_select, SOLR_get, SOLR_raw, json_loads_url
from .search_form import (SearchForm, solr_escape, CollectionFacetValueForm,
                          CarouselForm, CollectionCarouselForm, 
                          CampusCarouselForm, CampusForm, RepositoryForm)
from .collection_views import Collection, get_rc_from_ids
from .institution_views import Repository, Campus
from .facet_filter_type import CollectionFF
from static_sitemaps.util import _lazy_load
from static_sitemaps import conf
from requests.exceptions import HTTPError
from exhibits.models import ExhibitItem, Exhibit
from .temp import query_encode

import os
import math
import re
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
    from_item_page = request.META.get("HTTP_X_FROM_ITEM_PAGE")

    item_id_search_term = 'id:"{0}"'.format(item_id)
    item_search = SOLR_get(q=item_id_search_term)
    order = request.GET.get('order')

    if not item_search.found:
        # second level search
        def _fixid(id):
            return re.sub(r'^(\d*--http:/)(?!/)', r'\1/', id)

        old_id_query = {
            "query_string": f"harvest_id_s:*{_fixid(item_id)}",
            "rows": 10
        }
        old_id_search = SOLR_select(**query_encode(**old_id_query))
        if old_id_search.numFound:
            return redirect('calisphere:itemView',
                            old_id_search.results[0]['id'])
        else:
            raise Http404("{0} does not exist".format(item_id))

    item = item_search.item
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
    related_collections = []
    for col_id in item.get('collection_ids'):
        collection = Collection(col_id)
        item['parsed_collection_data'].append(collection.item_view())
        if not from_item_page:
            lockup_data = collection.get_lockup(item_id_search_term)
            related_collections.append(lockup_data)

    for repo_id in item.get('repository_ids'):
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

    search_results = {'reference_image_md5': None}
    search_results.update(item)

    num_related_collections = len(related_collections)

    template = "calisphere/itemViewer.html"
    context = {
        'q': '',
        'item': search_results,
        'item_solr_search': item_search.resp,
        'meta_image': meta_image,
        'repository_id': None,
        'itemId': None,
    }

    if not from_item_page:
        carousel_search_results, carousel_num_found = item_view_carousel_mlt(
            item_id)

        template = "calisphere/itemView.html"
        context = {
            'q': '',
            'item': search_results,
            'item_solr_search': item_search.resp,
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
        }

    return render(request, template, context)


def search(request):
    if request.method == 'GET' and len(request.GET.getlist('q')) > 0:
        form = SearchForm(request.GET.copy())
        results = form.search()
        facets = form.get_facets()
        filter_display = form.filter_display()

        rc_ids = [cd[0]['id'] for cd in facets[CollectionFF.facet_field]]
        if len(request.GET.getlist('collection_data')):
            rc_ids = request.GET.getlist('collection_data')

        num_related_collections = len(rc_ids)
        related_collections = get_rc_from_ids(
            rc_ids, form.rc_page, form.query_string)

        context = {
            'facets': facets,
            'q': form.q,
            'search_form': form.context(),
            'search_results': results.results,
            'numFound': results.numFound,
            'pages': int(math.ceil(results.numFound / int(form.rows))),
            'related_collections': related_collections,
            'num_related_collections': num_related_collections,
            'form_action': reverse('calisphere:search'),
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
    item_id = request.GET.get('itemId')
    if item_id is None:
        raise Http404("No item id specified")

    referral = request.GET.get('referral')
    link_back_id = ''
    form = CarouselForm(request.GET.copy())

    if referral == 'institution':
        link_back_id = request.GET.get('repository_data', None)
    if referral == 'collection':
        link_back_id = request.GET.get('collection_data', None)
        collection = Collection(link_back_id)
        form = CollectionCarouselForm(request.GET.copy(), collection)
    if referral == 'campus':
        link_back_id = request.GET.get('campus_slug', None)
        form = CampusCarouselForm(request.GET.copy(), Campus(link_back_id))

    carousel_params = form.query_encode()

    # if no query string or filters, do a "more like this" search
    if not form.query_string and not carousel_params.get('filters'):
        search_results, num_found = item_view_carousel_mlt(item_id)
    else:
        try:
            carousel_search = SOLR_select(**query_encode(**carousel_params))
        except HTTPError as e:
            # https://stackoverflow.com/a/19384641/1763984
            print((request.get_full_path()))
            raise (e)
        search_results = carousel_search.results
        num_found = carousel_search.numFound

    if request.GET.get('init'):
        context = form.context()

        context.update({
            'filters': form.filter_display(),
            'numFound': num_found,
            'search_results': search_results,
            'item_id': item_id,
            'referral': request.GET.get('referral'),
            'referralName': request.GET.get('referralName'),
            'campus_slug': request.GET.get('campus_slug'),
            'linkBackId': link_back_id
        })
        template = 'calisphere/carouselContainer.html'

    else:
        template = 'calisphere/carousel.html'
        context = {
                'start': request.GET.get('start', 0),
                'search_results': search_results,
                'item_id': item_id
            }
    return render(request, template, context)


campus_template = "https://registry.cdlib.org/api/v1/campus/{0}/"
repo_template = "https://registry.cdlib.org/api/v1/repository/{0}/"


def get_related_collections(request):
    form = SearchForm(request.GET.copy())
    field = CollectionFF(request.GET.copy())

    if request.GET.get('campus_slug'):
        slug = request.GET.get('campus_slug')
        form = CampusForm(request.GET.copy(), Campus(slug))

    rc_params = form.query_encode([field])
    rc_params['rows'] = 0

    # mlt search
    if not form.query_string and not rc_params.get('filters'):
        if request.GET.get('itemId'):
            rc_params['query_string'] = (
                f"id:{request.GET.get('itemId')}")

    related_collections = SOLR_select(**query_encode(**rc_params))
    related_collections = related_collections.facet_counts['facet_fields'][
        CollectionFF.facet_field]

    # remove collections with a count of 0 and sort by count
    related_collections = field.process_facets(related_collections)
    # remove 'count'
    related_collections = list(facet for facet, count in related_collections)

    # get three items for each related collection
    three_related_collections = []
    rc_page = int(request.GET.get('rc_page', 0))
    for i in range(rc_page * 3, rc_page * 3 + 3):
        if len(related_collections) <= i or not related_collections[i]:
            break

        col_id = (re.match(
            col_regex, related_collections[i].split('::')[0]).group('id'))
        collection = Collection(col_id)
        lockup_data = collection.get_lockup(rc_params['query_string'])
        three_related_collections.append(lockup_data)

    return three_related_collections, len(related_collections)


def related_collections(request):
    three_rcs, num_related_collections = get_related_collections(request)

    params = request.GET.copy()
    context = {
        'q': params.get('q'),
        'rq': params.getlist('rq'),
        'num_related_collections': num_related_collections,
        'related_collections': three_rcs,
        'search_form': {'rc_page': int(params.get('rc_page'))},
        'itemId': params.get('itemId'),
        'referral': params.get('referral'),
        'referralName': params.get('referralName'),
        'filters': False
    }
    if context['referral'] in ['institution', 'campus']:
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

    # facet=true&facet.query=*&rows=0&facet.field=title_ss&facet.pivot=title_ss,collection_data"
    facet_params = {
        "filters": [{'collection_url': [collection_url]}],
        "facets": [facet],
        "facet_sort": "count"
    }
    facet_search = SOLR_select(**query_encode(**facet_params))

    values = facet_search.facet_counts.get(
        'facet_fields').get('{}_ss'.format(facet))
    if not values:
        raise Http404("{0} has no values".format(facet))
    unique = len(values)
    records = sum(values.values())
    ratio = unique / records

    context = {
        'q': '',
        'facet': facet,
        'values': values,
        'unique': unique,
        'records': records,
        'ratio': ratio,
        'title': f"{facet} values from {collection_details['name']}",
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection_details,
        'collection_id': collection_id,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(request, 'calisphere/reportCollectionFacet.html', context)


def report_collection_facet_value(request, collection_id, facet, facet_value):
    collection = Collection(collection_id)
    collection_details = collection.details

    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} does not exist".format(facet))

    parsed_facet_value = urllib.parse.unquote_plus(facet_value)
    escaped_facet_value = solr_escape(parsed_facet_value)

    form = CollectionFacetValueForm(request.GET.copy(), collection)
    filter_params = form.query_encode()

    if not filter_params.get('filters'):
        filter_params['filters'] = {f'{facet}_ss': [escaped_facet_value]}
    else:
        filter_params['filters'].append({f'{facet}_ss': [escaped_facet_value]})

    filter_search = SOLR_select(**query_encode(**filter_params))

    collection_name = collection_details.get('name')

    context = form.context()
    context.update({
        'search_form': form.context(),
        'search_results': filter_search.results,
        'numFound': filter_search.numFound,
        'pages': int(math.ceil(filter_search.numFound / int(form.rows))),
        'facet': facet,
        'facet_value': parsed_facet_value,
        'meta_robots': "noindex,nofollow",
        'collection': collection_details,
        'collection_id': collection_id,
        'title': (
            f"{facet}: {parsed_facet_value} ({filter_search.numFound} items)"
            f" from: {collection_name}"),
        'description': None,
        'solrParams': filter_params,
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
