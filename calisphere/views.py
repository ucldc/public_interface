from future import standard_library
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import Http404, HttpResponse, QueryDict
from django.template.defaultfilters import urlize
from . import constants
from .utils import json_loads_url
from .item_manager import ItemManager
from .record import Record

from .search_form import (SearchForm, ESSearchForm, solr_escape, 
                          CollectionFacetValueForm, ESCollectionFacetValueForm,
                          CarouselForm, ESCarouselForm,
                          CollectionCarouselForm, ESCollectionCarouselForm,
                          CampusCarouselForm, ESCampusCarouselForm,
                          CampusForm, ESCampusForm)
from .collection_views import Collection, get_rc_from_ids
from .institution_views import Repository, Campus
from .facet_filter_type import CollectionFF
from static_sitemaps.util import _lazy_load
from static_sitemaps import conf
from requests.exceptions import HTTPError
from exhibits.models import ExhibitItem, Exhibit
from .decorators import cache_by_session_state
from django.views.decorators.cache import cache_page

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


def select_index(request, index):
    request.session['index'] = index
    query_dict = request.GET.copy()

    next_page = query_dict.pop('next', ['/'])[0]

    next_page = urllib.parse.urlparse(next_page)
    query = QueryDict(next_page.query, mutable=True)
    query.update(query_dict)
    query['index'] = index      # overwrite any other <index>

    query = query.urlencode()
    return redirect(next_page.path + f"?{query}")


def search_by_harvest_id(item_id, indexed_items):
    # second level search
    def _fixid(id):
        return re.sub(r'^(\d*--http:/)(?!/)', r'\1/', id)

    old_id_query = {
        "query_string": f"harvest_id_s:*{_fixid(item_id)}",
        "rows": 10
    }
    old_id_search = indexed_items.search(old_id_query)
    if old_id_search.numFound:
        return redirect('calisphere:itemView',
                        old_id_search.results[0]['id'])
    else:
        raise Http404("{0} does not exist".format(item_id))


@cache_by_session_state
def item_view(request, item_id=''):
    index = request.session.get('index')
    from_item_page = request.META.get("HTTP_X_FROM_ITEM_PAGE")
    child_index = request.GET.get('order')

    indexed_items = ItemManager(index)
    index_result = indexed_items.get(item_id)
    if not index_result:
        return search_by_harvest_id(item_id, indexed_items)

    item = Record(index_result.item, child_index, index)
    if item.is_hosted():
        item.display['contentFile'] = item.get_media(child_index)

    item.display['parsed_collection_data'] = [
        c.item_view() for c in item.collections]
    item.display['parsed_repository_data'] = [
        r.get_repo_data() for r in item.repositories]
    item.display['institution_contact'] = [
        r.get_contact_info() for r in item.repositories]

    related_collections = []
    if not from_item_page:
        related_collections = [
            c.get_lockup(f'id:"{item_id}"') 
            for c in item.collections
        ]

    relation_links = []
    for relation in item.get_relations():
        if urlize(relation, autoescape=False) == relation:
            relation_links.append({
                'label': relation,
                'uri': (reverse(
                    'calisphere:collectionView',
                    kwargs={'collection_id': item.collections[0].id}) +
                    "?relation_ss=" +
                    urllib.parse.quote(solr_escape(relation)))
                })
        else:
            relation_links.append({
                'label': relation,
                'uri': 'urlize'
            })
    if relation_links:
        item.display['relation_links'] = relation_links

    meta_image = False
    if item.indexed_record.get('reference_image_md5', False):
        meta_image = urllib.parse.urljoin(
            settings.UCLDC_FRONT,
            '/crop/999x999/{0}'.format(
                item.indexed_record['reference_image_md5']),
        )

    if item.indexed_record.get('rights_uri'):
        uri = item.indexed_record.get('rights_uri')
        item.display['rights_uri'] = {
            'url': uri,
            'statement': constants.RIGHTS_STATEMENTS[uri]
        }

    search_results = {'reference_image_md5': None}
    search_results.update(item.display)

    num_related_collections = len(related_collections)

    template = "calisphere/itemViewer.html"
    context = {
        'q': '',
        'item': search_results,
        'item_solr_search': index_result.resp,
        'meta_image': meta_image,
        'repository_id': None,
        'itemId': None,
    }

    if not from_item_page:
        carousel_search_results, carousel_num_found = item_view_carousel_mlt(
            item_id, index)

        template = "calisphere/itemView.html"
        context = {
            'q': '',
            'item': search_results,
            'item_solr_search': index_result.resp,
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


@cache_by_session_state
def search(request):
    index = request.session.get('index')
    if len(request.GET.getlist('q')) <= 0:
        return redirect('calisphere:home')

    if index == 'es':
        form = ESSearchForm(request.GET.copy())
    else:
        form = SearchForm(request.GET.copy())

    results = ItemManager(index).search(form.get_query())
    facets = form.get_facets(results.facet_counts['facet_fields'])
    filter_display = form.filter_display()

    rc_ids = [cd[0]['id'] for cd in facets[CollectionFF.facet_field]]
    if len(request.GET.getlist('collection_data')):
        rc_ids = request.GET.getlist('collection_data')

    num_related_collections = len(rc_ids)
    related_collections = get_rc_from_ids(
        rc_ids, form.rc_page, form.query_string, index)

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


def item_view_carousel_mlt(item_id, index):
    carousel_search = ItemManager(index).more_like_this(item_id)
    if carousel_search.numFound == 0:
        return None, None
        # raise Http404('No object with id "' + item_id + '" found.')
    search_results = carousel_search.results
    num_found = len(search_results)

    return search_results, num_found


@cache_by_session_state
def item_view_carousel(request):
    index = request.session.get('index')
    item_id = request.GET.get('itemId')
    if item_id is None:
        raise Http404("No item id specified")

    referral = request.GET.get('referral')
    link_back_id = ''
    if index == 'es':
        form = ESCarouselForm(request.GET.copy())
    else:
        form = CarouselForm(request.GET.copy())

    if referral == 'institution':
        link_back_id = request.GET.get('repository_data', None)
    if referral == 'collection':
        link_back_id = request.GET.get('collection_data', None)
        collection = Collection(link_back_id, index)
        if index == 'es':
            form = ESCollectionCarouselForm(request.GET.copy(), collection)
        else:
            form = CollectionCarouselForm(request.GET.copy(), collection)
    if referral == 'campus':
        link_back_id = request.GET.get('campus_slug', None)
        if index == 'es':
            form = ESCampusCarouselForm(request.GET.copy(), Campus(link_back_id, index))
        else:
            form = CampusCarouselForm(request.GET.copy(), Campus(link_back_id, index))

    carousel_params = form.get_query()

    # if no query string or filters, do a "more like this" search
    if not form.query_string and not carousel_params.get('filters'):
        search_results, num_found = item_view_carousel_mlt(item_id, index)
    else:
        try:
            carousel_search = ItemManager(index).search(carousel_params)
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
    index = request.session.get('index')
    if index == 'es':
        form = ESSearchForm(request.GET.copy())
    else:
        form = SearchForm(request.GET.copy())
    field = CollectionFF(request.GET.copy())

    if request.GET.get('campus_slug'):
        slug = request.GET.get('campus_slug')
        if index == 'es':
            form = ESCampusForm(request.GET.copy(), Campus(slug, index))
        else:
            form = CampusForm(request.GET.copy(), Campus(slug, index))

    rc_params = form.get_query([field])
    rc_params['rows'] = 0

    # mlt search (TODO, need to actually make MLT?)
    if not form.query_string and not rc_params.get('filters'):
        if request.GET.get('itemId'):
            rc_params['query_string'] = form.query_string = (
                f"id:{request.GET.get('itemId')}")

    related_collections = ItemManager(index).search(rc_params)
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

        if index == 'es':
            col_id = related_collections[i].split('::')[0]
        else:
            col_id = (re.match(
                col_regex, related_collections[i].split('::')[0]).group('id'))
        collection = Collection(col_id, index)
        lockup_data = collection.get_lockup(rc_params['query_string'])
        three_related_collections.append(lockup_data)

    return three_related_collections, len(related_collections)


@cache_by_session_state
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


@cache_by_session_state
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


@cache_by_session_state
def report_collection_facet(request, collection_id, facet):
    index = request.session.get('index')
    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} does not exist".format(facet))
    collection_url = col_template.format(collection_id)
    collection_details = json_loads_url(collection_url + '?format=json')
    if not collection_details:
        raise Http404("{0} does not exist".format(collection_id))

    for repository in collection_details.get('repository'):
        repository['resource_id'] = repository.get('resource_uri').split(
            '/')[-2]

    if index == 'es':
        facet_params = {
            "filters": [{'collection_ids': [collection_id]}],
            "facets": [facet]
        }
    else:
        facet_params = {
            "filters": [{'collection_url': [collection_url]}],
            "facets": [facet]
        }
    facet_search = ItemManager(index).search(facet_params)

    if index == 'es':
        values = facet_search.facet_counts.get(
            'facet_fields').get('{}'.format(facet))
    else:
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


@cache_by_session_state
def report_collection_facet_value(request, collection_id, facet, facet_value):
    index = request.session.get('index')
    collection = Collection(collection_id, index)
    collection_details = collection.details

    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} does not exist".format(facet))

    parsed_facet_value = urllib.parse.unquote_plus(facet_value)
    escaped_facet_value = solr_escape(parsed_facet_value)

    if index == 'es':
        form = ESCollectionFacetValueForm(request.GET.copy(), collection)
    else:
        form = CollectionFacetValueForm(request.GET.copy(), collection)
    filter_params = form.get_query()
    query_string = f"{facet}:\"{escaped_facet_value}\""

    if form.query_string:
        filter_params['query_string'] += f" AND ({query_string})"
    else:
        filter_params['query_string'] = query_string

    filter_search = ItemManager(index).search(filter_params)

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


@cache_page(60*15)
def contact_owner(request):
    # print request.GET
    return render(request, 'calisphere/thankyou.html')


@cache_page(60*15)
def posters(request):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    this_data = os.path.join(this_dir, 'poster-data.json')
    poster_data = json.loads(open(this_data).read())
    poster_data = sorted(poster_data.items())

    for _, poster in poster_data:
        poster['image'] = f"{settings.UCLDC_IMAGES}/{poster['image']}"

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
