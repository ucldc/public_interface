from django.test import Client
import unittest
from .cache_retry import query_encode
from .collection_views import Collection
from .institution_views import Repository, Campus
import re
# Create your tests here.


class CollectionQueriesTestCase(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        pass

    def test_get_item_count(self):
        collection = Collection(466, 'solr')
        solr_params = {
            "filters": [collection.basic_filter],
            "rows": 0
        }
        solr_params = query_encode(**solr_params)
        manual_params = {
            'rows': 0,
            'fq': 'collection_url: "' + collection.url + '"',
            'start': None,
        }
        self.assertEqual(solr_params, manual_params)

    def test_get_facets(self):
        collection = Collection(466, 'solr')
        facet_fields = collection.custom_schema_facets
        solr_params = {
            "filters": [collection.basic_filter],
            "rows": 0,
            "facets": [ff.field for ff in facet_fields],
            "facet_sort": 'count'
        }
        encoded = query_encode(**solr_params)
        manual_params = {
            'facet': 'true',
            'rows': 0,
            'facet_field': [f"{ff.facet}_ss" for ff in facet_fields],
            'fq': 'collection_url: "' + collection.url + '"',
            'facet_limit': '-1',
            'facet_mincount': 1,
            'facet_sort': 'count',
            'start': None,
        }
        self.assertEqual(encoded, manual_params)

    def test_get_mosaic(self):
        collection = Collection(466, 'solr')
        solr_params = {
            "query_string": "*:*",
            "filters": [
                collection.basic_filter,
                {"type_ss": ["image"]}
            ],
            "result_fields": [
                "reference_image_md5",
                "url_item",
                "id",
                "title",
                "collection_url",
                "type_ss"
            ],
            "sort": ("sort_title", "asc"),
            "rows": 6
        }
        solr_params_encoded = query_encode(**solr_params)

        search_terms = {
            'q': '*:*',
            'fl': (
                'reference_image_md5, url_item, id, '
                'title, collection_url, type_ss'),
            'sort': 'sort_title asc',
            'rows': 6,
            'fq': ['collection_url: "' + collection.url + '"', 'type_ss: \"image\"'],
            'start': None,
        }
        self.assertEqual(solr_params_encoded, search_terms)

        solr_params['filters'].pop(1)
        solr_params['exclude'] = [{"type_ss": ["image"]}]
        solr_params = query_encode(**solr_params)
        search_terms['fq'] = [
            'collection_url: "' + collection.url + '"',
            '(*:* AND -type_ss:\"image\")'
        ]
        self.assertEqual(solr_params, search_terms)

    def test_get_lockup(self):
        collection = Collection(466, 'solr')
        keyword_query = "welcome"

        solr_params = {
            'query_string': keyword_query,
            'filters': [collection.basic_filter],
            'result_fields': [
                "collection_data",
                "reference_image_md5",
                "url_item",
                "id",
                "title",
                "type_ss"
            ],
            "rows": 3,
        }
        solr_params_encoded = query_encode(**solr_params)
        rc_params = {
            'q': keyword_query,
            'rows': 3,
            'fq': 'collection_url: "' + collection.url + '"',
            'fl': (
                'collection_data, reference_image_md5, '
                'url_item, id, title, type_ss'
            ),
            'start': None,
        }
        self.assertEqual(solr_params_encoded, rc_params)

        solr_params.pop('query_string')
        solr_params_encoded = query_encode(**solr_params)
        rc_params.pop('q')
        self.assertEqual(solr_params_encoded, rc_params)

    def test_collection_facet_thumb_params(self):
        collection = Collection(466, 'solr')
        facet = "date"
        escaped_cluster_value = "October 17-18, 1991"
        solr_params = {
            "filters": [
                collection.basic_filter, 
                {f"{facet}_ss": [escaped_cluster_value]}
            ],
            "result_fields": ["reference_image_md5, type_ss"],
            "rows": 3
        }
        solr_params = query_encode(**solr_params)
        thumb_params = {
                'rows': 3,
                'fl': 'reference_image_md5, type_ss',
                'fq': [
                    'collection_url: "' + collection.url + '"',
                    f'{facet}_ss: "{escaped_cluster_value}"'
                ],
                'start': None,
            }
        self.assertEqual(solr_params, thumb_params)

    def test_get_cluster_thumbnails(self):
        collection = Collection(466, 'solr')
        escaped_cluster_value = "AIDS (Disease)"
        facet = "subject"
        solr_params = {
            'filters': [
                collection.basic_filter,
                {f'{facet}_ss': [escaped_cluster_value]}
            ],
            'result_fields': ['reference_image_md5', 'type_ss'],
            'rows': 3
        }
        solr_params = query_encode(**solr_params)
        thumb_params = {
            'rows': 3,
            'fl': 'reference_image_md5, type_ss',
            'fq': ['collection_url: "' + collection.url + '"',
                   f'{facet}_ss: "{escaped_cluster_value}"'],
            'start': None,
        }
        self.assertEqual(solr_params, thumb_params)


class InstitutionQueriesTestCase(unittest.TestCase):
    def test_campus_directory(self):
        solr_params = {
            "query_string": "*:*",
            "facets": ["repository_url"]
        }
        solr_params = query_encode(**solr_params)
        repositories_query = {
            'q': '*:*',
            'rows': 0,
            'facet': 'true',
            'facet_mincount': 1,
            'facet_field': ['repository_url'],
            'facet_limit': '-1',
            'start': None,
        }
        self.assertEqual(solr_params, repositories_query)

    def test_statewide_directory(self):
        solr_params = {
            "query_string": "*:*",
            "facets": ["repository_url"]
        }
        solr_params = query_encode(**solr_params)
        repositories_query = {
            "q": '*:*',
            "rows": 0,
            "facet": 'true',
            "facet_mincount": 1,
            "facet_field": ['repository_url'],
            "facet_limit": '-1',
            'start': None,
        }
        self.assertEqual(solr_params, repositories_query)

    def test_institution_collections(self):
        institution = Repository(25, 'solr')
        solr_params = {
            'filters': [institution.basic_filter],
            'facets': ['sort_collection_data'],
            'facet_sort': 'index'
        }
        solr_params = query_encode(**solr_params)
        collections_params = {
            'rows': 0,
            'fq': 'repository_url: "https://registry.cdlib.org/api/v1/repository/25/"',
            'facet': 'true',
            'facet_mincount': 1,
            'facet_limit': '-1',
            'facet_field': ['sort_collection_data'],
            'facet_sort': 'index',
            'start': None,
        }
        self.assertEqual(solr_params, collections_params)

    def test_campus_institutions(self):
        institution = Campus('UCI', 'solr')
        solr_params = {
            'filters': [institution.basic_filter],
            'facets': ['repository_data']
        }
        solr_params = query_encode(**solr_params)
        institutions_search = {
            'rows': 0,
            'fq': 'campus_url: "https://registry.cdlib.org/api/v1/campus/3/"',
            'facet': 'true',
            'facet_mincount': 1,
            'facet_limit': '-1',
            'facet_field': ['repository_data'],
            'start': None,
        }
        self.assertEqual(solr_params, institutions_search)


class CollectionDataQueriesTestCase(unittest.TestCase):
    def test_get_collection_data(self):
        solr_params = {
            'facets': ['collection_data']
        }
        solr_params = query_encode(**solr_params)
        collections_query = {
            "facet_field": ['collection_data'],
            'facet': 'true',
            'rows': 0,
            'facet_limit': '-1',
            'facet_mincount': 1,
            'start': None,
        }
        self.assertEqual(solr_params, collections_query)


class ViewQueriesTestCase(unittest.TestCase):
    def test_item_view(self):
        item_id = "466--http:/example"

        def _fixid(id):
            return re.sub(r'^(\d*--http:/)(?!/)', r'\1/', id)

        solr_params = {
            "query_string": f"harvest_id_s:*{_fixid(item_id)}",
            "rows": 10
        }
        solr_params = query_encode(**solr_params)
        old_id_search = {
            'q': 'harvest_id_s:*{}'.format(_fixid(item_id)),
            'rows': 10,
            'start': None,
        }
        self.assertEqual(solr_params, old_id_search)

    def test_report_collection_facet(self):
        collection_url = "https://registry.cdlib.org/api/v1/collection/466/"
        facet = "subject"
        solr_params = {
            "filters": [{'collection_url': [collection_url]}],
            "facets": [facet],
            "facet_sort": "count",
        }
        solr_params = query_encode(**solr_params)

        collection_facet_query = {
            'facet': 'true',
            'rows': 0,
            'facet_field': ['{}_ss'.format(facet)],
            'fq': 'collection_url: "{}"'.format(collection_url),
            'facet_limit': '-1',
            'facet_mincount': 1,
            'facet_sort': 'count',
            'start': None,
        }
        self.assertEqual(solr_params, collection_facet_query)


# c = Client()

# c.get('/')
# c.get('/exhibitions/')
