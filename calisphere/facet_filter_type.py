import re
import operator

from django.apps import apps
from django.conf import settings
from .utils import json_loads_url
from .utils import query_string_escape
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
    form_name = ''
    facet_field = ''
    display_name = ''
    filter_field = ''
    sort_by = 'count'
    faceting_allowed = True

    def __init__(self,
                 request):
        if request is not None:
            self.form_context = request.getlist(self.form_name)
            self.set_query()

    def set_query(self):
        selected_filters = self.form_context
        self.query = []
        self.basic_query = {}
        if len(selected_filters) > 0:
            query = list([
                '{0}: "{1}"'.format(self.filter_field,
                                    query_string_escape(
                                        self.filter_transform(val)))
                for val in selected_filters
            ])
            self.query = " OR ".join(query)
            self.basic_query = {self.filter_field: [
                self.filter_transform(v) for v in selected_filters]}

    def filter_transform(self, filter_val):
        return filter_val

    def facet_transform(self, facet_val):
        return facet_val

    def filter_display(self, filter_val):
        return filter_val

    def process_facets(self, facets, sort_override=None):
        filters = list(map(self.filter_transform, self.form_context))

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
                if self.form_name == 'collection_data':
                    api_url = re.match(col_regex, f)
                    collection = self.filter_display(api_url.group('id'))
                    display_facets.append(("{}::{}".format(
                        collection.get('url'), collection.get('name')), 0))
                elif self.form_name == 'repository_data':
                    api_url = re.match(repo_regex, f)
                    repository = self.repo_from_id(api_url.group('id'))
                    display_facets.append(("{}::{}".format(
                        repository.get('url'), repository.get('name')), 0))
                else:
                    display_facets.append((f, 0))

        return display_facets

    def __str__(self):
        return f'FacetFilterTypeClass: {self.facet_field}'

    def __getitem__(self, key):
        return getattr(self, key)


class ESFacetFilterType(FacetFilterType):
    def set_query(self):
        selected_filters = self.form_context
        self.query = {}
        self.basic_query = {}
        if len(selected_filters) > 0:
            self.query = {
                "terms": {
                    self.filter_field: self.filter_transform(selected_filters)
                }
            }
            self.basic_query = {
                self.filter_field: self.filter_transform(selected_filters)
            }

    def process_facets(self, facets, sort_override=None):
        filters = list(map(self.filter_transform, self.form_context))

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
                if self.form_name == 'collection_data':
                    collection = self.filter_display(f)
                    display_facets.append(("{}::{}".format(
                        collection.get('id'), collection.get('name')), 0))
                elif self.form_name == 'repository_data':
                    repository = self.repo_from_id(f)
                    display_facets.append(("{}::{}".format(
                        repository.get('id'), repository.get('name')), 0))
                else:
                    display_facets.append((f, 0))

        return display_facets


class RelationFF(FacetFilterType):
    form_name = 'relation_ss'
    facet_field = 'relation_ss'
    display_name = 'Relation'
    filter_field = 'relation_ss'
    sort_by = 'value'
    faceting_allowed = False


class ESRelationFF(ESFacetFilterType):
    form_name = 'relation_ss'
    facet_field = 'relation'
    display_name = 'Relation'
    filter_field = 'relation.raw'
    sort_by = 'value'
    faceting_allowed = False


class TypeFF(FacetFilterType):
    form_name = 'type_ss'
    facet_field = 'type_ss'
    display_name = 'Type of Item'
    filter_field = 'type_ss'


class ESTypeFF(ESFacetFilterType):
    form_name = 'type_ss'
    facet_field = 'type'
    display_name = 'Type of Item'
    filter_field = 'type.raw'

    def facet_transform(self, facet_val):
        if facet_val == '':
            return ('type value not supplied')
        return facet_val

    def filter_transform(self, filter_val):
        if 'type value not supplied' in filter_val:
            i = filter_val.index('type value not supplied')
            filter_val[i] = ''
        return filter_val


class DecadeFF(FacetFilterType):
    form_name = 'facet_decade'
    facet_field = 'facet_decade'
    display_name = 'Decade'
    filter_field = 'facet_decade'
    sort_by = 'value'


class ESDecadeFF(ESFacetFilterType):
    form_name = 'facet_decade'
    facet_field = 'date'
    #display_name = 'Decade'
    # see https://github.com/ucldc/rikolti/issues/807
    display_name = 'Date'
    filter_field = 'date.raw'
    sort_by = 'value'

    def facet_transform(self, facet_val):
        if facet_val == '':
            return ('date value not supplied')
        return facet_val

    def filter_transform(self, filter_val):
        if 'date value not supplied' in filter_val:
            i = filter_val.index('date value not supplied')
            filter_val[i] = ''
        return filter_val


class RepositoryFF(FacetFilterType):
    form_name = 'repository_data'
    facet_field = 'repository_data'
    display_name = 'Contributing Institution'
    filter_field = 'repository_url'

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
        pname = ''
        if len(parent):
            pslug = f"{parent[0].get('slug', None)}-"
            pname = f"{parent[0].get('name', '')} "
        repo['slug'] = pslug + repo_details.get('slug', None)
        repo['name'] = pname + repo_details.get('name', None)

        return repo


class ESRepositoryFF(ESFacetFilterType):
    form_name = 'repository_data'
    facet_field = 'repository_data'
    display_name = 'Contributing Institution'
    filter_field = 'repository_url'

    def facet_transform(self, facet_val):
        repo_id = facet_val.split('::')[0]
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
            repo['campus'] = parent[0].get('name', None)
        repo['slug'] = pslug + repo_details.get('slug', None)

        return repo


class CollectionFF(FacetFilterType):
    form_name = 'collection_data'
    facet_field = 'collection_data'
    display_name = 'Collection'
    filter_field = 'collection_url'

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
        indexed_collections = CollectionManager("solr")
        collection = {
            'url': col_template.format(collection_id),
            'id': collection_id
        }

        collection['name'] = indexed_collections.names.get(
            collection['url'])

        if not collection['name']:
            collection_details = json_loads_url("{0}?format=json".format(
                collection['url']))
            collection['name'] = collection_details.get(
                'name', '[no collection name]')

        return collection


class ESCollectionFF(ESFacetFilterType):
    form_name = 'collection_data'
    facet_field = 'collection_data'
    display_name = 'Collection'
    filter_field = 'collection_url'

    def facet_transform(self, collection_data):
        parts = collection_data.split('::')
        collection = {
            'url': col_template.format(parts[0]),
            'id': parts[0],
            'name': parts[1]
        }
        return collection

    def filter_display(self, collection_id):
        indexed_collections = CollectionManager("es")
        collection = {
            'url': col_template.format(collection_id),
            'id': collection_id
        }

        collection['name'] = indexed_collections.names.get(
            collection['url'])

        if not collection['name']:
            collection_details = json_loads_url("{0}?format=json".format(
                collection['url']))
            collection['name'] = collection_details.get(
                'name', '[no collection name]')

        return collection
