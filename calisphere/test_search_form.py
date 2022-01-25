from django.test import Client
import unittest
from .temp import query_encode
from .collection_views import Collection
from .institution_views import Repository, Campus
from . import constants
from .search_form import SearchForm
from django.http import QueryDict
from urllib.parse import urlencode


def solr_query_new(form):
    solr_query_new = {
        "query_string": form.query_string,
        "filters": [ft.basic_query for ft in form.facet_filter_types 
                    if ft.basic_query],
        "rows": int(form.rows),
        "start": int(form.start),
        "sort": tuple(
            (constants.SORT_OPTIONS[form.sort]).split(' ')
        ),
        "facets": [ft.facet_field for ft in form.facet_filter_types]
    }
    if form.implicit_filter:
        solr_query_new['filters'].append(form.basic_implicit_filter)
    return solr_query_new


class SearchFormTestCase(unittest.TestCase):

    def build_query(self, test):
        form = SearchForm(QueryDict(urlencode(test, True)))
        search_query = query_encode(**form.query_encode())
        return search_query

    def test_keyword_only_search(self):
        test = {'q': 'welcome'}
        solr = {'q': 'welcome', 'facet': 'true', 'facet_field': [
            'type_ss', 'facet_decade', 'repository_data', 'collection_data'], 
            'facet_limit': '-1', 'facet_mincount': 1, 'sort': 'score desc', 
            'rows': 24
        }
        self.assertEqual(self.build_query(test), solr)

    def test_refine_query(self):
        test = {'q': 'welcome', 'rq': 'anthill'}
        solr = {'q': 'welcome AND anthill', 'facet': 'true', 'facet_field': [
            'type_ss', 'facet_decade', 'repository_data', 'collection_data'], 
            'facet_limit': '-1', 'facet_mincount': 1, 'sort': 'score desc', 
            'rows': 24
        }
        self.assertEqual(self.build_query(test), solr)

    def test_filter_query(self):
        test = {'q': 'welcome', 'rq': 'anthill', 'type_ss': ['text', 'image']}
        solr = {
            'q': 'welcome AND anthill', 
            'fq': 'type_ss: "text" OR type_ss: "image"', 'facet': 'true', 
            'facet_field': [
                'type_ss', 'facet_decade', 'repository_data', 'collection_data'
            ], 'facet_limit': '-1', 'facet_mincount': 1, 'sort': 'score desc', 
            'rows': 24
        }
        self.assertEqual(self.build_query(test), solr)

    def test_multiple_filters(self):
        test = {'q': 'welcome', 'rq': 'anthill', 'type_ss': ['text', 'image'], 
                'collection_data': ['466', '26695']}
        solr = {
            'q': 'welcome AND anthill', 
            'fq': [
                'type_ss: "text" OR type_ss: "image"', 
                ('collection_url: '
                    '"https://registry.cdlib.org/api/v1/collection/466/" '
                    'OR collection_url: '
                    '"https://registry.cdlib.org/api/v1/collection/26695/"')
            ], 
            'facet': 'true', 
            'facet_field': [
                'type_ss', 'facet_decade', 'repository_data', 'collection_data'
            ], 
            'facet_limit': '-1', 'facet_mincount': 1, 'sort': 'score desc', 
            'rows': 24
        }
        self.assertEqual(self.build_query(test), solr)

    def test_filters_only(self):
        test = {'type_ss': ['text', 'image'], 'collection_data': ['466', '26695']}
        solr = {
            'fq': [
                'type_ss: "text" OR type_ss: "image"', 
                ('collection_url: '
                    '"https://registry.cdlib.org/api/v1/collection/466/" '
                    'OR collection_url: '
                    '"https://registry.cdlib.org/api/v1/collection/26695/"')
            ], 
            'facet': 'true', 
            'facet_field': [
                'type_ss', 'facet_decade', 'repository_data', 'collection_data'
            ], 
            'facet_limit': '-1', 'facet_mincount': 1, 'sort': 'sort_title asc', 
            'rows': 24
        }
        self.assertEqual(self.build_query(test), solr)
