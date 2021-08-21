from django.test import Client
import unittest
from .temp import query_encode
from .collection_views import Collection
from .institution_views import Repository, Campus
import re
# Create your tests here.


class CollectionQueriesTestCase(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        pass

    def test_get_item_count(self):
        collection = Collection(466)
        solr_params = {
            "filters": [collection.basic_filter],
            "rows": 0
        }
        solr_params = query_encode(**solr_params)
        manual_params = {
            'rows': 0,
            'fq': collection.filter,
        }
        self.assertEqual(solr_params, manual_params)

    def test_get_facets(self):
        collection = Collection(466)
        facet_fields = collection.custom_schema_facets
        solr_params = {
            "filters": [collection.basic_filter],
            "rows": 0,
            "facets": [ff.facet for ff in facet_fields]
        }
        encoded = query_encode(**solr_params)
        manual_params = {
            'facet': 'true',
            'rows': 0,
            'facet_field': [f"{ff.facet}_ss" for ff in facet_fields],
            'fq': collection.filter,
            'facet_limit': '-1',
            'facet_mincount': 1,
            'facet_sort': 'count',
        }
        self.assertEqual(encoded, manual_params)

    def test_get_mosaic(self):
        collection = Collection(466)
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
            'fq': [collection.filter, 'type_ss: \"image\"']
        }
        self.assertEqual(solr_params_encoded, search_terms)

        solr_params['filters'].pop(1)
        solr_params['exclude'] = [{"type_ss": ["image"]}]
        solr_params = query_encode(**solr_params)
        search_terms['fq'] = [
            collection.filter,
            '(*:* AND -type_ss:\"image\")'
        ]
        self.assertEqual(solr_params, search_terms)

    def test_get_lockup(self):
        collection = Collection(466)
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
            'fq': collection.filter,
            'fl': (
                'collection_data, reference_image_md5, '
                'url_item, id, title, type_ss'
            )
        }
        self.assertEqual(solr_params_encoded, rc_params)

        solr_params.pop('query_string')
        solr_params_encoded = query_encode(**solr_params)
        rc_params.pop('q')
        self.assertEqual(solr_params_encoded, rc_params)

    def test_collection_facet_thumb_params(self):
        collection = Collection(466)
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
                    collection.filter,
                    f'{facet}_ss: "{escaped_cluster_value}"'
                ]
            }
        self.assertEqual(solr_params, thumb_params)

    def test_get_cluster_thumbnails(self):
        collection = Collection(466)
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
            'fq': [collection.filter,
                   f'{facet}_ss: "{escaped_cluster_value}"']
        }
        self.assertEqual(solr_params, thumb_params)


class InstitutionQueriesTestCase(unittest.TestCase):
    def test_campus_directory(self):
        solr_params = {
            "facets": ["repository_ids"]
        }
        solr_params = query_encode(**solr_params)
        repositories_query = {
            "size": 0,
            "aggs": {
                "repository_ids": {
                    "terms": {
                        "field": "repository_ids",
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(solr_params, repositories_query)

    def test_statewide_directory(self):
        solr_params = {
            "facets": ["repository_ids"]
        }
        solr_params = query_encode(**solr_params)
        repositories_query = {
            "size": 0,
            "aggs": {
                "repository_ids": {
                    "terms": {
                        "field": "repository_ids",
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(solr_params, repositories_query)

    # def test_institution_collections(self):
    #     institution = Repository(25)
    #     solr_params = {
    #         'filters': institution.basic_filter,
    #         'facets': ['collection_data']
    #     }
    #     collections_params = {
    #         "query": institution.filter,
    #         "size": 0,
    #         "aggs": {
    #             "collection_data": {
    #                 "terms": {
    #                     "field": "collection_data.keyword",
    #                     "order": {
    #                         "_key": "asc"
    #                     }
    #                 }
    #             }
    #         }
    #     }
    #     self.assertEqual(solr_params, collections_params)

    def test_campus_institutions(self):
        institution = Campus('UCI')
        solr_params = {
            'filters': [institution.basic_filter],
            'facets': ['repository_data']
        }
        solr_params = query_encode(**solr_params)
        institutions_search = {
            "query": {
                "terms": {
                    "campus_ids": [institution.id]
                }
            },
            "size": 0,
            "aggs": {
                "repository_data": {
                    "terms": {
                        "field": "repository_data.keyword",
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(solr_params, institutions_search)


class CollectionDataQueriesTestCase(unittest.TestCase):
    def test_get_collection_data(self):
        solr_params = {
            'facets': ['collection_data']
        }
        solr_params = query_encode(**solr_params)
        collections_query = {
            "size": 0,
            "aggs": {
                "collection_data": {
                    "terms": {
                        "field": "collection_data.keyword",
                        "size": 10000
                    }
                }
            }
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
            "query": {
                "query_string": {
                    "query": f"harvest_id_s:*{_fixid(item_id)}"
                }
            },
            "size": 10
        }
        self.assertEqual(solr_params, old_id_search)

    def test_report_collection_facet(self):
        collection_id = 466
        facet = "subject"
        solr_params = {
            "filters": [{'collection_ids': [collection_id]}],
            "facets": [facet]
        }
        solr_params = query_encode(**solr_params)

        collection_facet_query = {
            "query": {
                "terms": {'collection_ids': [collection_id]}
            },
            "size": 0,
            "aggs": {
                facet: {
                    "terms": {
                        "field": f'{facet}.keyword',
                        "size": 10000
                    }
                }
            }
        }
        self.assertEqual(solr_params, collection_facet_query)


# c = Client()

# c.get('/')
# c.get('/exhibitions/')
