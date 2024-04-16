from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import Http404, JsonResponse
from calisphere.collection_data import CollectionManager
from . import constants
from .facet_filter_type import FacetFilterType, TypeFF, CollectionFF
from .utils import json_loads_url
from .item_manager import ItemManager
from .search_form import CollectionForm, ESCollectionForm, solr_escape
from builtins import range
from .decorators import cache_by_session_state

import os
import math
import string
import urllib.parse

col_regex = (r'https://registry\.cdlib\.org/api/v1/collection/'
             r'(?P<id>\d*)/?')
col_template = "https://registry.cdlib.org/api/v1/collection/{0}/"


@cache_by_session_state
def collections_directory(request):
    index = request.session.get("index")
    indexed_collections = CollectionManager(index)
    collections = []

    page = int(request.GET['page']) if 'page' in request.GET else 1

    for col in indexed_collections.shuffled[(page - 1) * 10:page * 10]:
        try:
            collections.append(Collection(col.id, index).get_mosaic())
        except Http404:
            continue

    context = {
        'meta_robots': None,
        'collections': collections,
        'random': True,
        'pages': int(
            math.ceil(len(indexed_collections.shuffled) / 10))
    }

    if page * 10 < len(indexed_collections.shuffled):
        context['next_page'] = page + 1
    if page - 1 > 0:
        context['prev_page'] = page - 1

    return render(
        request,
        'calisphere/collections/collectionsRandomExplore.html',
        context
    )


@cache_by_session_state
def collections_az(request, collection_letter):
    index = request.session.get("index")
    indexed_collections = CollectionManager(index)
    collections_list = indexed_collections.split[collection_letter.lower()]

    page = int(request.GET['page']) if 'page' in request.GET else 1
    pages = int(math.ceil(len(collections_list) / 10))

    collections = []
    for col in collections_list[(page - 1) * 10:page * 10]:
        try:
            collections.append(Collection(col.id, index).get_mosaic())
        except Http404:
            continue

    alphabet = list((character, True if character.lower() not in
                     indexed_collections.no_collections else False)
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


@cache_by_session_state
def collections_titles(request):
    '''create JSON/data for the collections search page'''

    def djangoize(id):
        '''turn registry URI into URL on django site'''
        return reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': id})

    index = request.session.get("index")
    collections = CollectionManager(index)
    data = [{
        'uri': djangoize(id),
        'title': title
    } for (uri, title, id) in collections.parsed]
    return JsonResponse(data, safe=False)


@cache_by_session_state
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

    def __init__(self, collection_id, index):
        self.id = collection_id
        self.url = col_template.format(collection_id)
        self.index = index
        self.details = json_loads_url(f"{self.url}?format=json")
        if not self.details:
            raise Http404(f"{collection_id} does not exist.")

        for repo in self.details.get('repository'):
            repo['resource_id'] = repo.get('resource_uri').split('/')[-2]

        self.custom_facets = self._parse_custom_facets()
        self.custom_schema_facets = self._generate_custom_schema_facets()

        if index == 'es':
            self.basic_filter = {'collection_url': [self.id]}
        else:
            self.basic_filter = {'collection_url': [self.url]}

    def _parse_custom_facets(self):
        custom_facets = []
        for custom_facet in self.details.get('custom_facet', []):
            facet_field = custom_facet['facet_field']
            if self.index == 'es':
                # TODO: check that `sort_by` works as expected!
                custom_facets.append(
                    type(
                        f"{facet_field}Class",
                        (FacetFilterType, ),
                        {
                            'form_name': custom_facet['facet_field'],
                            'facet_field': (
                                f"{custom_facet['facet_field'][:-3]}.raw"),
                            'display_name': custom_facet['label'],
                            'filter_field': (
                                f"{custom_facet['facet_field'][:-3]}.raw"),
                            'sort_by': custom_facet['sort_by'],
                            'faceting_allowed': True
                        }
                    )
                )
            else:
                custom_facets.append(
                    type(
                        f"{facet_field}Class",
                        (FacetFilterType, ),
                        {
                            'form_name': custom_facet['facet_field'],
                            'facet_field': custom_facet['facet_field'],
                            'display_name': custom_facet['label'],
                            'filter_field': custom_facet['facet_field'],
                            'sort_by': custom_facet['sort_by'],
                            'faceting_allowed': True
                        }
                    )
                )

        return custom_facets

    def _generate_custom_schema_facets(self):
        if self.index == 'es':
            custom_schema_facets = [fd for fd in constants.UCLDC_ES_SCHEMA_FACETS
                                    if fd.facet != 'spatial']
        else:
            custom_schema_facets = [fd for fd in constants.UCLDC_SOLR_SCHEMA_FACETS
                                    if fd.facet != 'spatial']

        # Use a registry-specified display name over constants.py display name
        if self.custom_facets:
            for custom in self.custom_facets:
                for i, facet in enumerate(custom_schema_facets):
                    if custom.facet_field == facet.field:
                        custom_schema_facets[i] = constants.FacetDisplayField(
                            facet.facet, custom.display_name, facet.field)
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

        item_query = {
            "filters": [self.basic_filter],
            "rows": 0
        }
        item_count_search = ItemManager(self.index).search(item_query)
        self.item_count = item_count_search.numFound
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
        facet_query = {
            "filters": [self.basic_filter],
            "rows": 0,
            "facets": [ff.field for ff in facet_fields]
        }
        facet_search = ItemManager(self.index).search(facet_query)
        self.item_count = facet_search.numFound

        facets = []
        for facet_field in facet_fields:
            values = facet_search.facet_counts.get('facet_fields').get(
                facet_field.field)
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

        if self.index == 'es':
            sort = ("sort_title.raw", "asc")
        else:
            sort = ("sort_title", "asc")

        # get 6 image items from the collection for the mosaic preview
        search_terms = {
            "filters": [
                self.basic_filter,
                {TypeFF.filter_field: ["image"]}
            ],
            "result_fields": [
                "reference_image_md5",
                "url_item",
                "id",
                "title",
                CollectionFF.filter_field,
                "type"
            ],
            "sort": sort,
            "rows": 6
        }
        display_items = ItemManager(self.index).search(search_terms)
        items = display_items.results

        search_terms['filters'].pop(1)
        search_terms['exclude'] = [{TypeFF.filter_field: ["image"]}]

        ugly_display_items = ItemManager(self.index).search(search_terms)
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

    def get_lockup(self, keyword_query):
        rc_params = {
            'query_string': keyword_query,
            'filters': [self.basic_filter],
            'result_fields': [
                "collection_data",
                "reference_image_md5",
                "url_item",
                "id",
                "title",
                "type"
            ],
            "rows": 3,
        }
        collection_items = ItemManager(self.index).search(rc_params)
        collection_items = collection_items.results

        if len(collection_items) < 3:
            # redo the query without any search terms
            rc_params.pop('query_string')
            collection_items_no_query = ItemManager(self.index).search(rc_params)
            collection_items += collection_items_no_query.results

        if len(collection_items) <= 0:
            # throw error
            print('no related collection items')

        repositories = []
        for repo in self.details.get('repository'):
            if 'campus' in repo and len(repo['campus']) > 0:
                repositories.append(repo['campus'][0]['name'] +
                                    ", " + repo['name'])
            else:
                repositories.append(repo['name'])

        return {
            'image_urls': collection_items,
            'name': self.details['name'],
            'collection_id': self.id,
            'institution': (', ').join(repositories)
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


@cache_by_session_state
def collection_search(request, collection_id):
    index = request.session.get("index")

    collection = Collection(collection_id, index)

    if index == 'solr':
        form = CollectionForm(request.GET.copy(), collection)
    else:
        form = ESCollectionForm(request.GET.copy(), collection)
    results = ItemManager(index).search(form.get_query())
    filter_display = form.filter_display()

    if settings.UCLDC_FRONT == 'https://calisphere.org/':
        browse = False
    else:
        browse = True
        # browse = collection.get_facet_sets()

    context = {
        'q': form.q,
        'search_form': form.context(),
        'facets': form.get_facets(results.facet_counts['facet_fields']),
        'pages': int(math.ceil(results.numFound / int(form.rows))),
        'numFound': results.numFound,
        'search_results': results.results,
        'filters': filter_display,
        'browse': browse,
        'meta_robots': None,
        'totalNumItems': collection.get_item_count(),
        'collection':
        collection.details,
        'collection_id':
        collection_id,
        'form_action':
        reverse(
            'calisphere:collectionView',
            kwargs={'collection_id': collection_id}),
    }

    return render(
        request, 'calisphere/collections/collectionView.html', context)


@cache_by_session_state
def collection_facet(request, collection_id, facet):
    index = request.session.get("index")
    collection = Collection(collection_id, index)
    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} is not a valid facet".format(facet))

    facet_type = [tup for tup in collection.custom_schema_facets
                  if tup.facet == facet][0]

    facets = collection.get_facets([facet_type])[0]
    if not facets:
        raise Http404("{0} has no facet values".format(facet))

    values = facets['values']
    if not values:
        raise Http404("{0} has no facet values".format(facet))

    sort = request.GET.get('sort', 'largestFirst')
    if sort == 'smallestFirst':
        values.reverse()
    if sort == 'az':
        values.sort(key=lambda v: v['label'])
    if sort == 'za':
        values.sort(key=lambda v: v['label'], reverse=True)

    view_format = request.GET.get('view_format', 'list')
    context = {}
    if view_format == 'grid':
        page = int(request.GET.get('page', 1))
        end = page * 24
        start = end - 24

        values = values[start:end]
        for value in values:
            escaped_cluster_value = solr_escape(value['label'])
            thumb_params = {
                "filters": [
                    collection.basic_filter, 
                    {facet_type.field: [escaped_cluster_value]}
                ],
                "result_fields": ["reference_image_md5, type_ss"],
                "rows": 3
            }
            thumbs = ItemManager(index).search(thumb_params)
            value['thumbnails'] = thumbs.results

        context.update({
            'page_info':
            {
                'page': page,
                'start': start+1,
                'end': end
            }
        })

    context.update({
        'q': request.GET.get('q', ''),
        'sort': sort,
        'view_format': view_format,
        'facet': facet_type,
        'values': values,
        'unique': facets['unique'],
        'records': facets['records'],
        'ratio': round((facets['unique'] / facets['records']) * 100, 2),
        'meta_robots': "noindex,nofollow",
        'description': None,
        'collection': collection.details,
        'collection_id': collection_id,
        'form_action': reverse(
            'calisphere:collectionFacet',
            kwargs={'collection_id': collection_id, 'facet': facet}),
        'item_count': collection.get_item_count(),
        'clusters': collection.get_facet_sets()
    })

    return render(
        request, 'calisphere/collections/collectionFacet.html', context)


@cache_by_session_state
def collection_facet_json(request, collection_id, facet):
    index = request.session.get("index")

    if facet not in [f.facet for f in constants.UCLDC_SCHEMA_FACETS]:
        raise Http404("{} is not a valid facet".format(facet))

    collection = Collection(collection_id, index)
    facet_type = [tup for tup in collection.custom_schema_facets
                  if tup.facet == facet][0]

    facets = collection.get_facets([facet_type])[0]
    if not facets:
        raise Http404("{0} has no facet values".format(facet))

    return JsonResponse(facets['values'], safe=False)


@cache_by_session_state
def collection_facet_value(request, collection_id, cluster, cluster_value):
    index = request.session.get("index")
    collection = Collection(collection_id, index)

    cluster_type = [tup for tup in collection.custom_schema_facets
                    if tup.facet == cluster][0]

    if not cluster_type:
        raise Http404("{} is not a valid facet".format(cluster))

    if index == 'solr':
        form = CollectionForm(request.GET.copy(), collection)
    else:
        form = ESCollectionForm(request.GET.copy(), collection)

    parsed_cluster_value = urllib.parse.unquote_plus(cluster_value)
    escaped_cluster_value = solr_escape(parsed_cluster_value)
    extra_filter = {cluster_type.field: [escaped_cluster_value]}

    form.implicit_filter.append(extra_filter)
    results = ItemManager(index).search(form.get_query())

    if results.numFound == 1:
        return redirect('calisphere:itemView', results.results[0]['id'])

    collection_name = collection.details.get('name')
    context = {
        'search_form': form.context(),
        'search_results': results.results,
        'numFound': results.numFound,
        'pages': int(math.ceil(results.numFound / int(form.rows))),
        'facets': form.get_facets(results.facet_counts['facet_fields']),
        'filters': form.filter_display(),
        'cluster': cluster,
        'cluster_value': parsed_cluster_value,
        'meta_robots': "noindex,nofollow",
        'collection': collection.details,
        'collection_id': collection_id,
        'title': (
            f"{cluster}: {parsed_cluster_value} "
            f"({results.numFound} items) from: {collection_name}"
        ),
        'description': None,
        'form_action': reverse(
            'calisphere:collectionFacetValue',
            kwargs={
              'collection_id': collection_id,
              'cluster': cluster,
              'cluster_value': cluster_value,
            }),
    }

    return render(
        request, 'calisphere/collections/collectionFacetValue.html', context)


@cache_by_session_state
def collection_metadata(request, collection_id):
    index = request.session.get("index")
    collection = Collection(collection_id, index)
    summary_data = collection.get_summary_data()

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


def get_cluster_thumbnails(collection, facet, facet_value, index):
    escaped_cluster_value = solr_escape(facet_value)
    thumb_params = {
        'filters': [
            collection.basic_filter,
            {facet.field: [escaped_cluster_value]}
        ],
        'result_fields': ['reference_image_md5', 'type'],
        'rows': 3
    }
    thumbs = ItemManager(index).search(thumb_params)
    return thumbs.results

# average 'best case': http://127.0.0.1:8000/collections/27433/browse/
# long rights statement: http://127.0.0.1:8000/collections/26241/browse/
# questioning grid usefulness: http://127.0.0.1:8000/collections/26935/browse/
# grid is helpful for ireland, building, ruin, stone:
# http://127.0.0.1:8000/collections/12378/subject/?view_format=grid&sort=largestFirst
# failed browse page: http://127.0.0.1:8000/collections/10318/browse/
# failed browse page: http://127.0.0.1:8000/collections/26666/browse/
# known issue, no thumbnails: http://127.0.0.1:8000/collections/26666/browse/
# less useful thumbnails: http://127.0.0.1:8000/collections/26241/browse/


@cache_by_session_state
def collection_browse(request, collection_id):
    index = request.session.get("index")
    collection = Collection(collection_id, index)
    facet_sets = collection.get_facet_sets()

    if len(facet_sets) == 0:
        return redirect('calisphere:collectionView', collection_id)

    for facet_set in facet_sets:
        facet_set['thumbnails'] = get_cluster_thumbnails(
            collection,
            facet_set['facet_field'],
            facet_set['values'][0]['label'],
            index
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


def get_rc_from_ids(rc_ids, rc_page, keyword_query, index):
    # get three items for each related collection
    three_related_collections = []
    rc_page = int(rc_page)
    for i in range(rc_page * 3, rc_page * 3 + 3):
        if len(rc_ids) <= i or not rc_ids[i]:
            break

        collection = Collection(rc_ids[i], index)
        lockup_data = collection.get_lockup(keyword_query)
        three_related_collections.append(lockup_data)

    return three_related_collections
