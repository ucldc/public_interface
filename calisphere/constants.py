from collections import namedtuple

RIGHTS_STATEMENTS = {
    'http://rightsstatements.org/vocab/InC/1.0/': 'In Copyright',
    'http://rightsstatements.org/vocab/InC-OW-EU/1.0/':
    'In Copyright - EU Orphan Work',
    'http://rightsstatements.org/vocab/InC-EDU/1.0/':
    'In Copyright - Educational Use Permitted',
    'http://rightsstatements.org/vocab/InC-NC/1.0/':
    'In Copyright - Non-Commercial Use Permitted',
    'http://rightsstatements.org/vocab/InC-RUU/1.0/':
    'In Copyright - Rights-Holder(s) Unlocatable or Unidentifiable',
    'http://rightsstatements.org/vocab/NoC-CR/1.0/':
    'No Copyright - Contractual Restrictions',
    'http://rightsstatements.org/vocab/NoC-NC/1.0/':
    'No Copyright - Non-Commercial Use Only',
    'http://rightsstatements.org/vocab/NoC-OKLR/1.0/':
    'No Copyright - Other Known Legal Restrictions',
    'http://rightsstatements.org/vocab/NoC-US/1.0/':
    'No Copyright - United States',
    'http://rightsstatements.org/vocab/CNE/1.0/': 'Copyright Not Evaluated',
    'http://rightsstatements.org/vocab/UND/1.0/': 'Copyright Undetermined',
    'http://rightsstatements.org/vocab/NKC/1.0/': 'No Known Copyright'
}

SORT_OPTIONS = {
    'relevance': 'score desc',
    'a': 'sort_title asc',
    'z': 'sort_title desc',
    'oldest-start': 'sort_date_start asc',
    'oldest-end': 'sort_date_end asc',
    'newest-start': 'sort_date_start desc',
    'newest-end': 'sort_date_end desc'
}

FacetDisplay = namedtuple(
    'FacetDisplay', 'facet, display')

# index schema fields that are of type=keyword so we can get
# facets directly without needing an _ss or .raw suffix
UCLDC_SCHEMA_TERM_FIELDS = [
    'calisphere-id',
    'id',
    'campus_name',
    'campus_data',
    'campus_url',
    'campus_id',
    'collection_name',
    'collection_data',
    'collection_url',
    'collection_id',
    'sort_collection_data',
    'repository_name',
    'repository_data',
    'repository_url',
    'repository_id',
    'rights_uri',
    'url_item',
    'fetcher_type',
    'mapper_type'
]

# index schema fields that are of type=text and thus need a 
# solr _ss or opensearch .raw suffix to get facets
UCLDC_SCHEMA_FACETS = [
  FacetDisplay("title", "title"),
  FacetDisplay("alternative_title", "alternative title"),
  FacetDisplay("creator", "creator"),
  FacetDisplay("contributor", "contributor"),
  FacetDisplay("date", "date"),
  FacetDisplay("publisher", "publisher"),
  FacetDisplay("rights", "rights"),
  FacetDisplay("rights_holder", "rights holder"),
  FacetDisplay("rights_note", "rights note"),
  FacetDisplay("rights_date", "copyright date"),
  FacetDisplay("type", "type"),
  FacetDisplay("format", "format"),
  FacetDisplay("genre", "form/genre"),
  FacetDisplay("extent", "extent"),
  FacetDisplay("identifier", "identifier"),
  FacetDisplay("language", "language"),
  FacetDisplay("subject", "subject"),
  FacetDisplay("temporal", "time period"),
  FacetDisplay("coverage", "place"),
  FacetDisplay("source", "source"),
  FacetDisplay("relation", "relation"),
  FacetDisplay("location", "location"),
  FacetDisplay("spatial", "spatial"),
]

FacetDisplayField = namedtuple(
    'FacetDisplayField', 'facet, display, field')
UCLDC_SOLR_SCHEMA_FACETS = [
    FacetDisplayField(fd.facet, fd.display, f"{fd.facet}_ss") 
    for fd in UCLDC_SCHEMA_FACETS
]
UCLDC_ES_SCHEMA_FACETS = [
    FacetDisplayField(fd.facet, fd.display, f"{fd.facet}.raw")
    for fd in UCLDC_SCHEMA_FACETS
]

CAMPUS_LIST = [
    {
        'featuredImage': {
            'src': '/thumb-uc_berkeley.jpg',
            'url': '/item/ark:/13030/ft400005ht/'
        },
        'id': '1',
        'name': 'UC Berkeley',
        'slug': 'UCB'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_davis.jpg',
            'url': '/item/ark:/13030/kt6779r95t/'
        },
        'id': '2',
        'name': 'UC Davis',
        'slug': 'UCD'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_irvine.jpg',
            'url': '/item/ark:/13030/hb6s2007ns/'
        },
        'id': '3',
        'name': 'UC Irvine',
        'slug': 'UCI'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_la.jpg',
            'url': '/item/ark:/21198/zz002bzhj9/'
        },
        'id': '10',
        'name': 'UCLA',
        'slug': 'UCLA'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_merced.jpg',
            'url': '/item/630a2224-a666-47ab-bd51-cda382108b6a/'
        },
        'id': '4',
        'name': 'UC Merced',
        'slug': 'UCM'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_riverside.jpg',
            'url': '/item/3669304d-960c-4c1d-b870-32c9dc3b288b/'
        },
        'id': '5',
        'name': 'UC Riverside',
        'slug': 'UCR'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_sandiego.jpg',
            'url': '/item/ark:/20775/bb34824128/'
        },
        'id': '6',
        'name': 'UC San Diego',
        'slug': 'UCSD'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_sf-v2.jpg',
            'url': '/item/3fe65b42-122e-48de-8e4b-bc8dcf531216/'
        },
        'id': '7',
        'name': 'UC San Francisco',
        'slug': 'UCSF'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_santabarbara.jpg',
            'url': '/item/ark:/13030/kt00003279/'
        },
        'id': '8',
        'name': 'UC Santa Barbara',
        'slug': 'UCSB'
    },
    {
        'featuredImage': {
            'src': '/thumb-uc_santacruz.jpg',
            'url': '/item/ark:/13030/hb4b69n74p/'
        },
        'id': '9',
        'name': 'UC Santa Cruz',
        'slug': 'UCSC'
    }
]

FEATURED_UNITS = [
    {
        'featuredImage': {
            'src': '/thumb-inst_marin.jpg',
            'url': '/item/ark:/13030/kt609nf54t/'
        },
        'id': '87'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_la-public-library.jpg',
            'url': '/item/2452a3b5fd22df4e5095e680626e189c/'
        },
        'id': '143'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_sf-public-library.jpg',
            'url': '/item/26095--AAE-0653/'
        },
        'id': '144'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_humboldt-state-university.jpg',
            'url': '/item/ark:/13030/ft096n9702/'
        },
        'id': '77'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_museum.jpg',
            'url': '/item/ark:/13030/kt5v19q1h9/'
        },
        'id': '93'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_japanese.jpg',
            'url': '/item/ark:/13030/tf3489n611/'
        },
        'id': '80'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_riverside.jpg',
            'url': '/item/ark:/13030/kt7z09r48v/'
        },
        'id': '108'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_huntington.jpg',
            'url': '/item/be854e7cffc3281b4032a20a5b1d75fd/'
        },
        'id': '304'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_lgbt.jpg',
            'url': '/item/ark:/13030/kt0m3nd81b/'
        },
        'id': '72'
    },
    {
        'featuredImage': {
            'src': '/thumb-inst_tulare-county.jpg',
            'url': '/item/ark:/13030/c800007n/'
        },
        'id': '149'
    }
]
