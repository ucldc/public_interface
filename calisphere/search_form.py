from .cache_retry import SOLR_select, json_loads_url
from . import constants
from django.http import Http404
from . import facet_filter_type as facet_module
from builtins import range


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
