from typing import Dict, List, Tuple

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
            'facet_decade',
            'type_ss']
        solr_facets = [f"{facet}_ss" if facet not in exceptions 
                       else facet for facet in facets]
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
