from future import standard_library
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import Http404, JsonResponse
from calisphere.collection_data import CollectionManager
from . import constants
from .facet_filter_type import FacetFilterType
from .cache_retry import SOLR_select, json_loads_url
from . import search_form
from builtins import range

import os
import math
import string
import urllib.parse
import re

standard_library.install_aliases()

col_regex = (r'https://registry\.cdlib\.org/api/v1/collection/'
             r'(?P<id>\d*)/?')
col_template = "https://registry.cdlib.org/api/v1/collection/{0}/"

def collections_directory(request):
    solr_collections = CollectionManager(settings.SOLR_URL,
                                         settings.SOLR_API_KEY)
    collections = []

    page = int(request.GET['page']) if 'page' in request.GET else 1

    for collection_link in solr_collections.shuffled[(page - 1) * 10:page *
                                                     10]:
        col_id = re.match(col_regex, collection_link.url).group('id')
        try:
            collections.append(Collection(col_id).get_mosaic())
        except Http404:
            continue

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

    return render(
        request,
        'calisphere/collections/collectionsRandomExplore.html',
        context
    )


def collections_az(request, collection_letter):
    solr_collections = CollectionManager(settings.SOLR_URL,
                                         settings.SOLR_API_KEY)
    collections_list = solr_collections.split[collection_letter.lower()]

    page = int(request.GET['page']) if 'page' in request.GET else 1
    pages = int(math.ceil(len(collections_list) / 10))

    collections = []
    for collection_link in collections_list[(page - 1) * 10:page * 10]:
        col_id = re.match(col_regex, collection_link.url).group('id')
        try:
            collections.append(Collection(col_id).get_mosaic())
        except Http404:
            continue

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

    return render(request, 'calisphere/collections/collectionsAZ.html',
                  context)


def collections_titles(request):
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


def collections_search(request):
    return render(
        request,
        'calisphere/collections/collectionsTitleSearch.html',
        {
            'collections': [],
            'collection_q': True
        }
    )


class Collection(object):

    def __init__(self, collection_id):
        self.id = collection_id
        self.url = col_template.format(collection_id)
        self.details = json_loads_url(f"{self.url}?format=json")
        if not self.details:
            raise Http404(f"{collection_id} does not exist.")

        for repo in self.details.get('repository'):
            repo['resource_id'] = repo.get('resource_uri').split('/')[-2]

        self.custom_facets = self._parse_custom_facets()
        self.custom_schema_facets = self._generate_custom_schema_facets()

        self.solr_filter = 'collection_url: "' + self.url + '"'

    def _parse_custom_facets(self):
        custom_facets = []
        if self.details.get('custom_facet'):
            for custom_facet in self.details.get('custom_facet'):
                custom_facets.append(
                    FacetFilterType(
                        custom_facet['facet_field'],
                        custom_facet['label'],
                        custom_facet['facet_field'],
                        custom_facet.get('sort_by', 'count')
                    )
                )
        return custom_facets

    def _generate_custom_schema_facets(self):
        custom_schema_facets = [fd for fd in constants.UCLDC_SCHEMA_FACETS
                                if fd.facet != 'spatial']
        if self.custom_facets:
            for custom in self.custom_facets:
                for i, facet in enumerate(custom_schema_facets):
                    if custom.facet == f"{facet.facet}_ss":
                        custom_schema_facets[i] = constants.FacetDisplay(
                            facet.facet, custom.display_name)
        return custom_schema_facets

    def get_summary_data(self):
        if hasattr(self, 'summary'):
            return self.summary

        summary_url = os.path.join(
            settings.UCLDC_METADATA_SUMMARY,
            '{}.json'.format(self.id),
        )
        self.summary = json_loads_url(summary_url)
        if not self.summary:
            raise Http404(f"{self.id} does not have summary data")

        self.item_count = self.summary['item_count']
        return self.summary

    def get_item_count(self):
        if hasattr(self, 'item_count'):
            return self.item_count

        solr_params = {
            'facet': 'false',
            'rows': 0,
            'fq': 'collection_url:"{}"'.format(self.url),
        }
        solr_search = SOLR_select(**solr_params)
        self.item_count = solr_search.numFound
        return self.item_count

    def _choose_facet_sets(self, facet_set):
        if not facet_set:
            return False
        if len(facet_set['values']) < 1:
            return False

        # # exclude homogenous facet values;
        # ie: all 10 records have type: image
        # if (len(facet_set['values']) == 1 and
        #         facet_set['values'][0]['count'] == self.item_count):
        #     # although technically, this could mean that
        #     # 8 records have type: [image]
        #     # 1 record has type: [image, image]
        #     # 1 record has type: None
        #     return False

        # # exclude completely unique facet values
        # if facet_set['values'][0]['count'] == 1:
        #     return False

        return True

    def get_facet_sets(self):
        facet_sets = self.get_facets(self.custom_schema_facets)

        # choose facet sets to show
        chosen_facet_sets = [facet_set for facet_set in facet_sets
                             if self._choose_facet_sets(facet_set)]
        facet_sets = chosen_facet_sets

        return facet_sets

    def get_facets(self, facet_fields):
        # facet=true&facet.query=*&rows=0&facet.field=title_ss&facet.pivot=title_ss,collection_data"
        solr_params = {
            'facet': 'true',
            'rows': 0,
            'facet_field': [f"{ff.facet}_ss" for ff in facet_fields],
            'fq': 'collection_url:"{}"'.format(self.url),
            'facet_limit': '-1',
            'facet_mincount': 1,
            'facet_sort': 'count',
        }
        solr_search = SOLR_select(**solr_params)
        self.item_count = solr_search.numFound

        facets = []
        for facet_field in facet_fields:
            values = solr_search.facet_counts.get('facet_fields').get(
                '{}_ss'.format(facet_field.facet))
            if not values:
                facets.append(None)

            unique = len(values)
            records = sum(values.values())

            values = [{'label': k, 'count': v, 'uri': reverse(
                'calisphere:collectionFacetValue',
                kwargs={
                    'collection_id': self.id,
                    'cluster': facet_field.facet,
                    'cluster_value': urllib.parse.quote_plus(k),
                })} for k, v in values.items()]

            facets.append({
                'facet_field': facet_field,
                'records': records,
                'unique': unique,
                'values': values
            })

        return facets

    def get_mosaic(self):
        repositories = []
        for repository in self.details.get('repository'):
            if 'campus' in repository and len(repository['campus']) > 0:
                repositories.append(repository['campus'][0]['name'] +
                                    ", " + repository['name'])
            else:
                repositories.append(repository['name'])

        # get 6 image items from the collection for the mosaic preview
        search_terms = {
            'q': '*:*',
            'fields': (
                'reference_image_md5, url_item, id, '
                'title, collection_url, type_ss'),
            'sort': 'sort_title asc',
            'rows': 6,
            'start': 0,
            'fq':
            [f'collection_url: \"{ self.url }\"', 'type_ss: \"image\"']
        }
        display_items = SOLR_select(**search_terms)
        items = display_items.results

        search_terms['fq'] = [
            f'collection_url: \"{ self.url }\"',
            '(*:* AND -type_ss:\"image\")'
        ]
        ugly_display_items = SOLR_select(**search_terms)
        # if there's not enough image items, get some non-image
        # items for the mosaic preview
        if len(items) < 6:
            items = items + ugly_display_items.results

        return {
            'name': self.details['name'],
            'description': self.details['description'],
            'collection_id': self.id,
            'institutions': repositories,
            'numFound': display_items.numFound + ugly_display_items.numFound,
            'display_items': items
        }

    def item_view(self):
        production_disqus = (
            settings.UCLDC_FRONT == 'https://calisphere.org/' or
            settings.UCLDC_DISQUS == 'prod'
        )
        if production_disqus:
            disqus_shortname = self.details.get(
                'disqus_shortname_prod')
        else:
            disqus_shortname = self.details.get(
                'disqus_shortname_test')

        return {
            "url": self.url,
            "name": self.details.get('name'),
            "id": self.id,
            "local_id": self.details.get('local_id'),
            "slug": self.details.get('slug'),
            "harvest_type": self.details.get('harvest_type'),
            "custom_facet": self.details.get('custom_facet'),
            "disqus_shortname": disqus_shortname
        }


def collection_search(request, collection_id):
    collection = Collection(collection_id)

    form = search_form.CollectionForm(request, collection)
    solr_search = SOLR_select(**form.solr_encode())

    facets = form.facet_query(solr_search, collection.solr_filter)

    context = {
        'search_form': form.context(),
        'search_results': solr_search.results,
        'numFound': solr_search.numFound,
        'pages': int(math.ceil(solr_search.numFound / int(form.rows))),
        'facets': facets
    }

    solr_params = form.solr_encode()
    total_items = SOLR_select(**{**solr_params, **{
        'q': '',
        'fq': [collection.solr_filter],
        'rows': 0,
        'facet': 'false'
    }})

    context['filters'] = {}
    params = request.GET.copy()
    for filter_type in form.facet_filter_types:
        param_name = filter_type['facet']
        display_name = filter_type['filter']
        filter_transform = filter_type['filter_display']

        if len(params.getlist(param_name)) > 0:
            context['filters'][display_name] = list(
                map(filter_transform, params.getlist(param_name)))

    if settings.UCLDC_FRONT == 'https://calisphere.org/':
        browse = False
    else:
        browse = collection.get_facet_sets()

    context.update({
        'browse': browse,
        'meta_robots': None,
        'totalNumItems':
        total_items.numFound,
        'FACET_FILTER_TYPES':
        form.facet_filter_types,
        'collection':
        collection.details,
        'collection_id':
        collection_id,
        'form_action':
        reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    })

    return render(
        request, 'calisphere/collections/collectionView.html', context)


def collection_facet(request, collection_id, facet):
    collection = Collection(collection_id)
    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} is not a valid facet".format(facet))

    params = request.GET.copy()
    context = search_form.search_defaults(params)
    if not params.get('view_format'):
        context['view_format'] = 'list'

    context.update({
        'facet':
        [tup for tup in collection.custom_schema_facets
            if tup.facet == facet][0]})
    facets = collection.get_facets([context['facet']])[0]
    if not facets:
        raise Http404("{0} has no facet values".format(facet))

    values = facets['values']
    if not values:
        raise Http404("{0} has no facet values".format(facet))

    if params.get('sort') == 'smallestFirst':
        values.reverse()
    if params.get('sort') == 'az':
        values.sort(key=lambda v: v['label'])
    if params.get('sort') == 'za':
        values.sort(key=lambda v: v['label'], reverse=True)

    if context.get('view_format') == 'grid':
        if params.get('page') and params.get('page') != 'None':
            page = int(params.get('page'))
        else:
            page = 1
        end = page * 24
        start = end - 24

        values = values[start:end]
        for value in values:
            escaped_cluster_value = search_form.solr_escape(value['label'])
            thumb_params = {
                'facet': 'false',
                'rows': 3,
                'fl': 'reference_image_md5, type_ss',
                'fq':
                    [f'collection_url: "{collection.url}"',
                     f'{facet}_ss: "{escaped_cluster_value}"']
            }
            solr_thumbs = SOLR_select(**thumb_params)
            value['thumbnails'] = solr_thumbs.results

        context.update({
            'page_info':
            {
                'page': page,
                'start': start+1,
                'end': end
            }
        })

    context.update({
        'values': values,
        'unique': facets['unique'],
        'records': facets['records'],
        'ratio': round((facets['unique'] / facets['records']) * 100, 2)
    })

    context.update({
        # 'title': f"{facet.capitalize()}{pluralize(values)}
        # Used in {collection.details['name']}",
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection.details,
        'collection_id': collection_id,
        'form_action': reverse(
            'calisphere:collectionFacet',
            kwargs={'collection_id': collection_id, 'facet': facet}),
    })

    context.update({
        'item_count': collection.get_item_count(),
        'clusters': collection.get_facet_sets()
    })

    return render(
        request, 'calisphere/collections/collectionFacet.html', context)


def collection_facet_json(request, collection_id, facet):
    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} is not a valid facet".format(facet))

    collection = Collection(collection_id)
    facets = collection.get_facets([constants.FacetDisplay(facet, 'json')])[0]
    if not facets:
        raise Http404("{0} has no facet values".format(facet))

    return JsonResponse(facets['values'], safe=False)


def collection_facet_value(request, collection_id, cluster, cluster_value):
    collection = Collection(collection_id)

    if cluster not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} is not a valid facet".format(cluster))

    params = request.GET.copy()

    parsed_cluster_value = urllib.parse.unquote_plus(cluster_value)
    escaped_cluster_value = search_form.solr_escape(parsed_cluster_value)
    params.update({'fq': f"{cluster}_ss:\"{escaped_cluster_value}\""})

    context = search_form.search_defaults(params)

    # Collection Views don't allow filtering or faceting by
    # collection_data or repository_data
    facet_filter_types = [
        facet_filter_type for facet_filter_type in constants.FACET_FILTER_TYPES
        if facet_filter_type['facet'] != 'collection_data'
        and facet_filter_type['facet'] != 'repository_data'
    ]

    # Add Custom Facet Filter Types
    facet_filter_types = facet_filter_types + collection.custom_facets
    # If relation_ss is not already defined as a custom facet, and is included
    # in search parameters, add the relation_ss facet implicitly
    if not collection.custom_facets:
        if params.get('relation_ss'):
            facet_filter_types.append(
                FacetFilterType(
                    'relation_ss',
                    'Relation',
                    'relation_ss',
                    'value',
                    faceting_allowed=False
                )
            )

    # perform the search
    solr_params = search_form.solr_encode(params, facet_filter_types)
    solr_params['fq'].append(collection.solr_filter)
    solr_search = SOLR_select(**solr_params)
    context['search_results'] = solr_search.results
    context['numFound'] = solr_search.numFound
    if context['numFound'] == 1:
        return redirect('calisphere:itemView',
                        solr_search.results[0]['id'])
    total_items = SOLR_select(**{**solr_params, **{
        'q': '',
        'fq': [collection.solr_filter],
        'rows': 0,
        'facet': 'false'
    }})

    context['pages'] = int(
        math.ceil(solr_search.numFound / int(context['rows'])))

    context['facets'] = search_form.facet_query(facet_filter_types, params,
                                                solr_search, collection.solr_filter)

    context['filters'] = {}
    for filter_type in facet_filter_types:
        param_name = filter_type['facet']
        display_name = filter_type['filter']
        filter_transform = filter_type['filter_display']

        if len(params.getlist(param_name)) > 0:
            context['filters'][display_name] = list(
                map(filter_transform, params.getlist(param_name)))

    collection_name = collection.details.get('name')
    context.update({'cluster': cluster})
    context.update({'cluster_value': parsed_cluster_value})
    context.update({
        'meta_robots': "noindex,nofollow",
        'totalNumItems': total_items.numFound,
        'FACET_FILTER_TYPES': facet_filter_types,
        'collection': collection.details,
        'collection_id': collection_id,
        'title': (
            f"{cluster}: {parsed_cluster_value} "
            f"({solr_search.numFound} items) from: {collection_name}"
        ),
        'description': None,
        'solrParams': solr_params,
        'form_action': reverse(
            'calisphere:collectionFacetValue',
            kwargs={
              'collection_id': collection_id,
              'cluster': cluster,
              'cluster_value': cluster_value,
            }),
    })

    return render(
        request, 'calisphere/collections/collectionFacetValue.html', context)


def collection_metadata(request, collection_id):
    collection = Collection(collection_id)
    summary_data = collection.get_summary_data()

    params = request.GET.copy()
    context = search_form.search_defaults(params)
    context = {
        'title': f"Metadata report for {collection.details['name']}",
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection.details,
        'collection_id': collection_id,
        'summary_data': summary_data,
        'UCLDC_SCHEMA_FACETS': constants.UCLDC_SCHEMA_FACETS,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(
        request, 'calisphere/collections/collectionMetadata.html', context)


def get_cluster_thumbnails(collection_url, facet, facet_value):
    escaped_cluster_value = search_form.solr_escape(facet_value)
    thumb_params = {
        'facet': 'false',
        'rows': 3,
        'fl': 'reference_image_md5, type_ss',
        'fq': [f'collection_url: "{collection_url}"',
               f'{facet.facet}_ss: "{escaped_cluster_value}"']
        }
    solr_thumbs = SOLR_select(**thumb_params)
    return solr_thumbs.results

# average 'best case': http://127.0.0.1:8000/collections/27433/browse/
# long rights statement: http://127.0.0.1:8000/collections/26241/browse/
# questioning grid usefulness: http://127.0.0.1:8000/collections/26935/browse/
# grid is helpful for ireland, building, ruin, stone:
# http://127.0.0.1:8000/collections/12378/subject/?view_format=grid&sort=largestFirst
# failed browse page: http://127.0.0.1:8000/collections/10318/browse/
# failed browse page: http://127.0.0.1:8000/collections/26666/browse/
# known issue, no thumbnails: http://127.0.0.1:8000/collections/26666/browse/
# less useful thumbnails: http://127.0.0.1:8000/collections/26241/browse/


def collection_browse(request, collection_id):
    collection = Collection(collection_id)
    facet_sets = collection.get_facet_sets()

    if len(facet_sets) == 0:
        return redirect('calisphere:collectionView', collection_id)

    for facet_set in facet_sets:
        facet_set['thumbnails'] = get_cluster_thumbnails(
            collection.url,
            facet_set['facet_field'],
            facet_set['values'][0]['label']
        )

    context = {
        'meta_robots': "noindex,nofollow",
        'collection': collection.details,
        'collection_id': collection_id,
        'UCLDC_SCHEMA_FACETS': constants.UCLDC_SCHEMA_FACETS,
        'item_count': collection.get_item_count(),
        'clusters': facet_sets,
        'facet': None,
        'form_action': reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(
        request, 'calisphere/collections/collectionBrowse.html', context)


def get_related_collections(params, slug=None, repository_id=None):
    solr_params = search_form.solr_encode(
        params, constants.FACET_FILTER_TYPES, [{'facet': 'collection_data'}])
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
    # remove collections with a count of 0 and sort by count
    related_collections = field.process_facets(
        related_collections, params.getlist('collection_data'))
    # remove 'count'
    related_collections = list(facet for facet, count in related_collections)

    # get three items for each related collection
    three_related_collections = []
    rc_page = int(params.get('rc_page', 0))
    for i in range(rc_page * 3, rc_page * 3 + 3):
        if len(related_collections) <= i or not related_collections[i]:
            break

        col_id = (re.match(
            col_regex, related_collections[i].split('::')[0]).group('id'))
        collection = Collection(col_id)

        rc_solr_params = {
            'q': solr_params['q'],
            'rows': '3',
            'fq': [f"collection_url: \"{ collection.url }\""],
            'fields': (
                'collection_data, reference_image_md5, '
                'url_item, id, title, type_ss'
            )
        }
        collection_items = SOLR_select(**rc_solr_params)
        collection_items = collection_items.results

        if len(collection_items) < 3:
            # redo the query without any search terms
            rc_solr_params['q'] = ''
            collection_items_no_query = SOLR_select(**rc_solr_params)
            collection_items = (
                collection_items + collection_items_no_query.results)

        if len(collection_items) <= 0:
            break

        lockup_data = {
            'image_urls': collection_items,
            'name': collection.details['name'],
            'collection_id': collection.id
        }

        repositories = []
        for repository in collection.details.get('repository'):
            if 'campus' in repository and len(repository['campus']) > 0:
                repositories.append(repository['campus'][0]['name'] +
                                    ", " + repository['name'])
            else:
                repositories.append(repository['name'])
        lockup_data['institution'] = (', ').join(repositories)

        three_related_collections.append(lockup_data)

    return three_related_collections, len(related_collections)
