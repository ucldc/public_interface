import re
from django.apps import apps
from django.conf import settings
from .cache_retry import SOLR_select, SOLR_raw, json_loads_url
from calisphere.collection_data import CollectionManager
# FACETS are retrieved from Solr for a user to potentially FILTER on
# FILTERS are FACETS that have been selected by the user already
# We use more robust solr fields for a FACET (_data)
# so we don't have to hit registry for a repository name just to enumerate available FACETS
# We use more specific solr fields for a FILTER (_url)
# so if there is a change in some of the robust data and a harvest hasn't been run (ie - a collection name changes)
# the FILTER still works

# FACET_TYPES = [
#     ('type_ss', 'Type of Item'),
#     ('facet_decade', 'Decade'),
#     ('repository_data', 'Contributing Institution'),
#     ('collection_data', 'Collection'),
# ]

def repositoryIdToUrl(id):
    repository_template = "https://registry.cdlib.org/api/v1/repository/{0}/"
    return repository_template.format(id)

def collectionIdToUrl(id):
    collection_template = "https://registry.cdlib.org/api/v1/collection/{0}/"
    return collection_template.format(id)

def getCollectionData(collection_data=None, collection_id=None):
    collection = {}
    if collection_data:
        parts = collection_data.split('::')
        collection['url'] = parts[0] if len(parts) >= 1 else ''
        collection['name'] = parts[1] if len(parts) >= 2 else ''
        collection_api_url = re.match(
            r'^https://registry\.cdlib\.org/api/v1/collection/(?P<url>\d*)/?',
            collection['url'])
        if collection_api_url is None:
            print('no collection api url:')
            collection['id'] = ''
        else:
            collection['id'] = collection_api_url.group('url')
    elif collection_id:
        solr_collections = CollectionManager(settings.SOLR_URL,
                                             settings.SOLR_API_KEY)
        collection[
            'url'] = "https://registry.cdlib.org/api/v1/collection/{0}/".format(
                collection_id)
        collection['id'] = collection_id
        collection_details = json_loads_url(
            "{0}?format=json".format(collection['url']))

        collection['name'] = solr_collections.names.get(collection['url']
            ) or collection_details.get('name', '[no collection name]')

        collection['local_id'] = collection_details['local_id']
        collection['slug'] = collection_details['slug']
    return collection

def getRepositoryData(repository_data=None, repository_id=None, repository_url=None):
    """ supply either `repository_data` from solr or the `repository_id` or `repository_url`
        all the reset will be looked up and filled in
    """
    app = apps.get_app_config('calisphere')
    repository = {}
    repository_details = {}
    if not (repository_data) and not (repository_id) and repository_url:
        repository_id = re.match(
            r'https://registry\.cdlib\.org/api/v1/repository/(?P<repository_id>\d*)/?',
            repository_url).group('repository_id')
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
        repository[
            'url'] = "https://registry.cdlib.org/api/v1/repository/{0}/".format(
                repository_id)
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
    parent = repository_details['campus']
    pslug = ''
    if len(parent):
        pslug = '{0}-'.format(parent[0].get('slug', None))
    repository['slug'] = pslug + repository_details.get('slug', None)
    return repository

def collectionFilterDisplay(filter_item):
    collection = getCollectionData(
        collection_id=filter_item)
    collection.pop('local_id', None)
    collection.pop('slug', None)
    return collection

def repositoryFilterDisplay(filter_item):
    repository = getRepositoryData(
        repository_id=filter_item)
    repository.pop('local_id', None)
    return repository

SORT_OPTIONS = {
    'relevance': 'score desc',
    'a': 'sort_title asc',
    'z': 'sort_title desc',
    'oldest-start': 'sort_date_start asc',
    'oldest-end': 'sort_date_end asc',
    'newest-start': 'sort_date_start desc',
    'newest-end': 'sort_date_end desc'
}

FACET_FILTER_TYPES = [{
    'facet': 'type_ss',
    'display_name': 'Type of Item',
    'filter': 'type_ss',
    'filter_transform': lambda (filterVal) : filterVal,
    'facet_transform': lambda (facetVal) : facetVal,
    'filter_display': lambda (filterVal) : filterVal
}, {
    'facet': 'facet_decade',
    'display_name': 'Decade',
    'filter': 'facet_decade',
    'filter_transform': lambda (filterVal) : filterVal,
    'facet_transform': lambda (facetVal) : facetVal,
    'filter_display': lambda (filterVal) : filterVal
}, {
    'facet': 'repository_data',
    'display_name': 'Contributing Institution',
    'filter': 'repository_url',
    'filter_transform': lambda (filterVal) : repositoryIdToUrl(filterVal),
    'facet_transform': lambda (facetVal) : getRepositoryData(repository_data=facetVal),
    'filter_display': lambda (filterVal) : repositoryFilterDisplay(filterVal)
}, {
    'facet': 'collection_data',
    'display_name': 'Collection',
    'filter': 'collection_url',
    'filter_transform': lambda (filterVal) : collectionIdToUrl(filterVal),
    'facet_transform': lambda (facetVal) : getCollectionData(collection_data=facetVal),
    'filter_display': lambda (filterVal) : collectionFilterDisplay(filterVal)
}]

# Make a copy of FACET_FILTER_TYPES to reset to original.
DEFAULT_FACET_FILTER_TYPES = FACET_FILTER_TYPES[:]

CAMPUS_LIST = [{
    'featuredImage': {
        'src': '/thumb-uc_berkeley.jpg',
        'url': '/item/ark:/13030/ft400005ht/'
    },
    'id': '1',
    'name': 'UC Berkeley',
    'slug': 'UCB'
}, {
    'featuredImage': {
        'src': '/thumb-uc_davis.jpg',
        'url': '/item/ark:/13030/kt6779r95t/'
    },
    'id': '2',
    'name': 'UC Davis',
    'slug': 'UCD'
}, {
    'featuredImage': {
        'src': '/thumb-uc_irvine.jpg',
        'url': '/item/ark:/13030/hb6s2007ns/'
    },
    'id': '3',
    'name': 'UC Irvine',
    'slug': 'UCI'
}, {
    'featuredImage': {
        'src': '/thumb-uc_la.jpg',
        'url': '/item/ark:/21198/zz002bzhj9/'
    },
    'id': '10',
    'name': 'UCLA',
    'slug': 'UCLA'
}, {
    'featuredImage': {
        'src': '/thumb-uc_merced.jpg',
        'url': '/item/630a2224-a666-47ab-bd51-cda382108b6a/'
    },
    'id': '4',
    'name': 'UC Merced',
    'slug': 'UCM'
}, {
    'featuredImage': {
        'src': '/thumb-uc_riverside.jpg',
        'url': '/item/3669304d-960c-4c1d-b870-32c9dc3b288b/'
    },
    'id': '5',
    'name': 'UC Riverside',
    'slug': 'UCR'
}, {
    'featuredImage': {
        'src': '/thumb-uc_sandiego.jpg',
        'url': '/item/ark:/20775/bb34824128/'
    },
    'id': '6',
    'name': 'UC San Diego',
    'slug': 'UCSD'
}, {
    'featuredImage': {
        'src': '/thumb-uc_sf-v2.jpg',
        'url': '/item/3fe65b42-122e-48de-8e4b-bc8dcf531216/'
    },
    'id': '7',
    'name': 'UC San Francisco',
    'slug': 'UCSF'
}, {
    'featuredImage': {
        'src': '/thumb-uc_santabarbara.jpg',
        'url': '/item/ark:/13030/kt00003279/'
    },
    'id': '8',
    'name': 'UC Santa Barbara',
    'slug': 'UCSB'
}, {
    'featuredImage': {
        'src': '/thumb-uc_santacruz.jpg',
        'url': '/item/ark:/13030/hb4b69n74p/'
    },
    'id': '9',
    'name': 'UC Santa Cruz',
    'slug': 'UCSC'
}]

FEATURED_UNITS = [{
    'featuredImage': {
        'src': '/thumb-inst_marin.jpg',
        'url': '/item/ark:/13030/kt609nf54t/'
    },
    'id': '87'
}, {
    'featuredImage': {
        'src': '/thumb-inst_la-public-library.jpg',
        'url': '/item/26094--LAPL00027224/'
    },
    'id': '143'
}, {
    'featuredImage': {
        'src': '/thumb-inst_sf-public-library.jpg',
        'url': '/item/26095--AAE-0653/'
    },
    'id': '144'
}, {
    'featuredImage': {
        'src': '/thumb-inst_humboldt-state-university.jpg',
        'url': '/item/ark:/13030/ft096n9702/'
    },
    'id': '77'
}, {
    'featuredImage': {
        'src': '/thumb-inst_museum.jpg',
        'url': '/item/ark:/13030/kt5v19q1h9/'
    },
    'id': '93'
}, {
    'featuredImage': {
        'src': '/thumb-inst_japanese.jpg',
        'url': '/item/ark:/13030/tf3489n611/'
    },
    'id': '80'
}, {
    'featuredImage': {
        'src': '/thumb-inst_riverside.jpg',
        'url': '/item/ark:/13030/kt7z09r48v/'
    },
    'id': '108'
}, {
    'featuredImage': {
        'src': '/thumb-inst_huntington.jpg',
        'url': '/item/ark:/13030/kt5t1nd9ph/'
    },
    'id': '146'
}, {
    'featuredImage': {
        'src': '/thumb-inst_lgbt.jpg',
        'url': '/item/ark:/13030/kt7d5nf4s3/'
    },
    'id': '72'
}, {
    'featuredImage': {
        'src': '/thumb-inst_tulare-county.jpg',
        'url': '/item/ark:/13030/c800007n/'
    },
    'id': '149'
}]
