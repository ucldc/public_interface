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

FACET_FILTER_TYPES = [{
    'facet': 'type_ss',
    'display_name': 'Type of Item',
    'filter': 'type_ss'
}, {
    'facet': 'facet_decade',
    'display_name': 'Decade',
    'filter': 'facet_decade'
}, {
    'facet': 'repository_data',
    'display_name': 'Contributing Institution',
    'filter': 'repository_url'
}, {
    'facet': 'collection_data',
    'display_name': 'Collection',
    'filter': 'collection_url'
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
