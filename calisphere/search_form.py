from .cache_retry import SOLR_select
from . import constants
from django.http import Http404


def solr_escape(text):
    return text.replace('?', '\\?').replace('"', '\\"')


class SearchForm(object):
    def __init__(self, request):
        self.params = request.GET.copy()
        self.q = request.GET.get('q', '')
        self.rq = request.GET.getlist('rq')
        self.rows = request.GET.get('rows', '24')
        self.start = request.GET.get('start', 0)
        self.sort = request.GET.get('sort', 'relevance')
        self.view_format = request.GET.get('view_format', 'thumbnails')
        self.rc_page = request.GET.get('rc_page', 0)

    def context(self):
        return {
            'q': self.q,
            'rq': self.rq,
            'rows': self.rows,
            'start': self.start,
            'sort': self.sort,
            'view_format': self.view_format,
            'rc_page': self.rc_page
        }

    def solr_encode(self, filter_types, facet_types=[]):
        if len(facet_types) == 0:
            facet_types = filter_types

        # concatenate query terms from refine query and query box
        query_terms = []
        q = self.params.get('q')
        if q:
            query_terms.append(solr_escape(q))

        for qt in self.params.getlist('rq'):
            if qt:
                query_terms.append(solr_escape(qt))

        for qt in self.params.getlist('fq'):
            if qt:
                query_terms.append(qt)

        if len(query_terms) == 1:
            query_terms_string = query_terms[0]
        else:
            query_terms_string = " AND ".join(query_terms)

        # query_terms_string = query_terms_string.replace('?', '')

        filters = []
        for filter_type in filter_types:
            selected_filters = self.params.getlist(filter_type['facet'])
            if (len(selected_filters) > 0):
                filter_transform = filter_type['filter_transform']

                selected_filters = list([
                    '{0}: "{1}"'.format(filter_type['filter'],
                                        solr_escape(
                                            filter_transform(filter_val)))
                    for filter_val in selected_filters
                ])
                selected_filters = " OR ".join(selected_filters)
                filters.append(selected_filters)

        try:
            rows = int(self.params.get('rows', 24))
            start = int(self.params.get('start', 0))
        except ValueError as err:
            raise Http404("{0} does not exist".format(err))

        query_value = {
            'q':
            query_terms_string,
            'rows': rows,
            'start': start,
            'sort':
            constants.SORT_OPTIONS[
                self.params.get('sort', 'relevance' if query_terms else 'a')
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

        query_fields = self.params.get('qf')
        if query_fields:
            query_value.update({'qf': query_fields})

        return query_value

    def facet_query(self, facet_filter_types, solr_search, extra_filter=None):
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
            if (len(self.params.getlist(facet_type)) > 0):
                exclude_facets_of_type = self.params.copy()
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
                self.params.getlist(facet_type)
            )

            for j, facet_item in enumerate(facets[facet_type]):
                facets[facet_type][j] = (facet_filter_type.facet_transform(
                    facet_item[0]), facet_item[1])

        return facets


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
