import re
import operator

from django.apps import apps
from django.conf import settings
from .cache_retry import json_loads_url
from calisphere.collection_data import CollectionManager

# FACETS are retrieved from Solr for a user to potentially FILTER on
# FILTERS are FACETS that have been selected by the user already
# We use more robust solr fields for a FACET (_data) so we don't have
# to hit registry for a repository name just to enumerate available FACETS
# We use more specific solr fields for a FILTER (_url) so if there is a
# change in some of the robust data and a harvest hasn't been run
# (ie - a collection name changes) the FILTER still works

col_regex = (
    r'^https://registry\.cdlib\.org/api/v1/collection/(?P<id>\d*)/?')
col_template = "https://registry.cdlib.org/api/v1/collection/{0}/"
repo_regex = (
    r'^https://registry\.cdlib\.org/api/v1/repository/(?P<id>\d*)/?')
repo_template = "https://registry.cdlib.org/api/v1/repository/{0}/"


class FacetFilterType(object):
    def __init__(self,
                 facet_solr_name,
                 display_name,
                 filter_solr_name,
                 sort_by='count',
                 faceting_allowed=True):
        self.facet = facet_solr_name
        self.display_name = display_name
        self.filter = filter_solr_name
        self.sort_by = sort_by    # 'count' or 'value'
        self.faceting_allowed = faceting_allowed

    def filter_transform(self, filter_val):
        return filter_val

    def facet_transform(self, facet_val):
        return facet_val

    def filter_display(self, filter_val):
        return filter_val

    def process_facets(self, facets, filter_params, sort_override=None):
        filters = list(map(self.filter_transform, filter_params))

        # remove facets with count of zero
        display_facets = dict(
            (facet, count) for facet, count in list(
                facets.items()) if count != 0)

        # sort facets by value of sort_by - either count or value
        sort_by = sort_override if sort_override else self.sort_by
        if sort_by == 'value':
            display_facets = sorted(
                iter(list(display_facets.items())), key=operator.itemgetter(0))
        elif sort_by == 'count':
            display_facets = sorted(
                iter(list(display_facets.items())),
                key=operator.itemgetter(1),
                reverse=True)

        # append selected filters even if they have a count of 0
        for f in filters:
            if not any(f in facet[0] for facet in display_facets):
                if self.facet == 'collection_data':
                    api_url = re.match(col_regex, f)
                    collection = self.filter_display(api_url.group('id'))
                    display_facets.append(("{}::{}".format(
                        collection.get('url'), collection.get('name')), 0))
                elif self.facet == 'repository_data':
                    api_url = re.match(repo_regex, f)
                    repository = self.repo_from_id(api_url.group('id'))
                    display_facets.append(("{}::{}".format(
                        repository.get('url'), repository.get('name')), 0))
                else:
                    display_facets.append((f, 0))

        return display_facets

    def __str__(self):
        return f'FacetFilterTypeClass: {self.facet}'

    def __getitem__(self, key):
        return getattr(self, key)


class RepositoryFacetFilterType(FacetFilterType):
    def filter_transform(self, repository_id):
        return repo_template.format(repository_id)

    def facet_transform(self, facet_val):
        url = facet_val.split('::')[0]
        repo_id = re.match(repo_regex, url).group('id')
        return self.repo_from_id(repo_id)

    def filter_display(self, filter_val):
        repository = self.repo_from_id(filter_val)
        repository.pop('local_id', None)
        return repository

    def repo_from_id(self, repo_id):
        app = apps.get_app_config('calisphere')
        repo = {
            'url': repo_template.format(repo_id),
            'id': repo_id
        }
        repo_details = app.registry.repository_data.get(int(repo['id']), {})
        repo['name'] = repo_details.get('name', None)
        repo['ga_code'] = repo_details.get('google_analytics_tracking_code', None)

        prod_aeon = settings.UCLDC_FRONT == 'https://calisphere.org/'
        if prod_aeon:
            repo['aeon_url'] = repo_details.get('aeon_prod', None)
        else:
            repo['aeon_url'] = repo_details.get('aeon_test', None)

        parent = repo_details['campus']
        pslug = ''
        if len(parent):
            pslug = '{0}-'.format(parent[0].get('slug', None))
        repo['slug'] = pslug + repo_details.get('slug', None)

        return repo


class CollectionFacetFilterType(FacetFilterType):
    def filter_transform(self, collection_id):
        return col_template.format(collection_id)

    def facet_transform(self, collection_data):
        parts = collection_data.split('::')
        collection = {
            'url': parts[0] if len(parts) >= 1 else '',
            'name': parts[1] if len(parts) >= 2 else ''
        }
        collection_api_url = re.match(col_regex, collection['url'])
        if collection_api_url is None:
            print('no collection api url:')
            collection['id'] = ''
        else:
            collection['id'] = collection_api_url.group('id')

        return collection

    def filter_display(self, collection_id):
        solr_collections = CollectionManager(settings.SOLR_URL,
                                             settings.SOLR_API_KEY)
        collection = {
            'url': col_template.format(collection_id),
            'id': collection_id
        }

        collection['name'] = solr_collections.names.get(
            collection['url'])

        if not collection['name']:
            collection_details = json_loads_url("{0}?format=json".format(
                collection['url']))
            collection['name'] = collection_details.get(
                'name', '[no collection name]')

        return collection
