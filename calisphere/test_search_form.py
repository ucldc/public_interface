from django.test import Client
import unittest
from .temp import query_encode
from .collection_views import Collection
from .institution_views import Repository, Campus
from . import constants
from .search_form import SearchForm
from django.http import QueryDict
from urllib.parse import urlencode


def es_query_new(form):
    es_query_new = {
        "query_string": form.query_string,
        "filters": [ft.basic_query for ft in form.facet_filter_types 
                    if ft.basic_query],
        "rows": int(form.rows),
        "start": int(form.start),
        # "sort": tuple(
        #     (constants.SORT_OPTIONS[form.sort]).split(' ')
        # ),
        "facets": [ft.facet_field for ft in form.facet_filter_types]
    }
    if form.implicit_filter:
        es_query_new['filters'].append(form.basic_implicit_filter)
    return es_query_new


class SearchFormTestCase(unittest.TestCase):

    def test_keyword_only_search(self):
        params = [
            {'q': 'welcome'},
            {'q': 'welcome', 'rq': 'anthill'},
            {'q': 'welcome', 'rq': 'anthill', 'type_ss': ['text', 'image']},
            {'q': 'welcome', 'rq': 'anthill', 'type_ss': ['text', 'image'], 'collection_data': ['466', '26695']},
            {'type_ss': ['text', 'image'], 'collection_data': ['466', '26695']}
        ]

        for param in params:
            req = QueryDict(urlencode(param))
            form = SearchForm(req)
            search_query = form.query_encode()

            new_query = es_query_new(form)
            new_query = query_encode(**new_query)

            self.assertEqual(search_query, new_query)
