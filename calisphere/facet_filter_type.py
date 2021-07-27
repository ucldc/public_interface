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
repo_regex = (
    r'^https://registry\.cdlib\.org/api/v1/repository/(?P<id>\d*)/?')


def get_repository_data(repository_data=None,
                        repository_id=None,
                        repository_url=None):
    """ supply either `repository_data` from solr or the `repository_id`
        or `repository_url` all the reset will be looked up and filled in
    """
    repo_regex = (
        r'https://registry\.cdlib\.org/api/v1/repository/(?P<id>\d*)/?')
    app = apps.get_app_config('calisphere')
    repository = {}
    repository_details = {}
    if not (repository_data) and not (repository_id) and repository_url:
        repository_id = re.match(
            repo_regex, repository_url).group('id')
    if repository_data:
        parts = repository_data.split('::')
        repository['url'] = parts[0] if len(parts) >= 1 else ''
        repository['name'] = parts[1] if len(parts) >= 2 else ''
        repository['campus'] = parts[2] if len(parts) >= 3 else ''

        repository_api_url = re.match(
            r'^https://registry\.cdlib\.org/api/v1/repository/(?P<url>\d*)/',
            repository['url'])
        if repository_api_url is None:
            print('no repository api url')
            repository['id'] = ''
        else:
            repository['id'] = repository_api_url.group('url')
            repository_details = app.registry.repository_data.get(
                int(repository['id']), {})
    elif repository_id:
        repository['url'] = (
            f"https://registry.cdlib.org/api/v1/repository/{repository_id}/")
        repository['id'] = repository_id
        repository_details = app.registry.repository_data.get(
            int(repository_id), None)
        repository['name'] = repository_details['name']
        if repository_details['campus']:
            repository['campus'] = repository_details['campus'][0]['name']
        else:
            repository['campus'] = ''
    # details needed for stats
    repository['ga_code'] = repository_details.get(
        'google_analytics_tracking_code', None)

    production_aeon = settings.UCLDC_FRONT == 'https://calisphere.org/'
    if production_aeon:
        repository['aeon_url'] = repository_details.get('aeon_prod', None)
    else:
        repository['aeon_url'] = repository_details.get('aeon_test', None)
    parent = repository_details['campus']
    pslug = ''
    if len(parent):
        pslug = '{0}-'.format(parent[0].get('slug', None))
    repository['slug'] = pslug + repository_details.get('slug', None)
    return repository


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
                    repository = get_repository_data(
                        repository_id=api_url.group('id'))
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
        template = "https://registry.cdlib.org/api/v1/repository/{0}/"
        return template.format(repository_id)

    def facet_transform(self, facet_val):
        return get_repository_data(repository_data=facet_val)

    def filter_display(self, filter_val):
        repository = get_repository_data(repository_id=filter_val)
        repository.pop('local_id', None)
        return repository


class CollectionFacetFilterType(FacetFilterType):
    def filter_transform(self, collection_id):
        template = "https://registry.cdlib.org/api/v1/collection/{0}/"
        return template.format(collection_id)

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
            'url': (
                f"https://registry.cdlib.org/api/v1/"
                f"collection/{collection_id}/"
            ),
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
