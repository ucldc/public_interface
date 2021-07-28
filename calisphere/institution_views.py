from future import standard_library
from django.shortcuts import render
from django.urls import reverse
from django.http import Http404
from . import constants
from .facet_filter_type import get_repository_data
from .cache_retry import SOLR_select, json_loads_url
from . import search_form
from .collection_views import Collection, get_related_collections

import math
import re
import string

standard_library.install_aliases()

repo_regex = (r'https://registry\.cdlib\.org/api/v1/repository/'
              r'(?P<repository_id>\d*)/?')
col_regex = (r'https://registry\.cdlib\.org/api/v1/collection/'
             r'(?P<id>\d*)/?')


def process_sort_collection_data(string):
    '''temporary; should parse sort_collection_data
       with either `:` or `::` dlimiter style
    '''
    if '::' in string:
        return string.split('::', 2)
    else:
        part1, remainder = string.split(':', 1)
        part2, part3 = remainder.rsplit(':https:')
        return [part1, part2, 'https:{}'.format(part3)]


def campus_directory(request):
    repositories_solr_query = SOLR_select(
        q='*:*',
        rows=0,
        start=0,
        facet='true',
        facet_mincount=1,
        facet_field=['repository_url'],
        facet_limit='-1')
    solr_repositories = repositories_solr_query.facet_counts['facet_fields'][
        'repository_url']

    repositories = []
    for repository_url in solr_repositories:
        repository = get_repository_data(repository_url=repository_url)
        if repository['campus']:
            repositories.append({
                'name':
                repository['name'],
                'campus':
                repository['campus'],
                'repository_id':
                re.match(
                    repo_regex,
                    repository['url']).group('repository_id')
            })

    repositories = sorted(
        repositories,
        key=lambda repository: (repository['campus'], repository['name']))
    # Use hard-coded campus list so UCLA ends up in the correct order
    # campuses = sorted(list(set(
    #     [repository['campus'] for repository in repositories])))

    return render(
        request, 'calisphere/campusDirectory.html', {
            'repositories': repositories,
            'campuses': constants.CAMPUS_LIST,
            'state_repositories': None,
            'description': None,
        })


def statewide_directory(request):
    repositories_solr_query = SOLR_select(
        q='*:*',
        rows=0,
        start=0,
        facet='true',
        facet_mincount=1,
        facet_field=['repository_url'],
        facet_limit='-1')
    solr_repositories = repositories_solr_query.facet_counts['facet_fields'][
        'repository_url']
    repositories = []
    for repository_url in solr_repositories:
        repository = get_repository_data(repository_url=repository_url)
        if repository['campus'] == '':
            repositories.append({
                'name':
                repository['name'],
                'repository_id':
                re.match(
                    repo_regex,
                    repository['url']).group('repository_id')
            })

    binned_repositories = []
    bin = []
    for repository in repositories:
        if repository['name'][0] in string.punctuation:
            bin.append(repository)
    if len(bin) > 0:
        binned_repositories.append({'punctuation': bin})

    for char in string.ascii_uppercase:
        bin = []
        for repository in repositories:
            if repository['name'][0] == char or repository['name'][
                    0] == char.upper:
                bin.append(repository)
        if len(bin) > 0:
            bin.sort(key=lambda r: r['name'])
            binned_repositories.append({char: bin})

    return render(
        request, 'calisphere/statewideDirectory.html', {
            'state_repositories': binned_repositories,
            'campuses': None,
            'meta_image': None,
            'description': None,
            'q': None,
        })


class Campus(object):
    def __init__(self, slug):
        campus = [c for c in constants.CAMPUS_LIST if slug == c['slug']][0]
        if not campus:
            raise Http404(f"{slug} campus does not exist.")

        self.slug = slug
        self.id = campus.get('id')
        self.featured_image = campus.get('featuredImage')
        self.type = 'campus'
        self.url = (
            f'https://registry.cdlib.org/api/v1/campus/{self.id}/')

        self.details = json_loads_url(self.url + "?format=json")
        if not self.details:
            raise Http404("{0} does not exist".format(id))

        self.name = self.details.get('name')
        if self.details.get('ark'):
            self.contact_info = json_loads_url(
                "http://dsc.cdlib.org/institution-json/" +
                self.details.get('ark'))
        else:
            self.contact_info = ''

        self.solr_filter = 'campus_url: "' + self.url + '"'


class Repository(object):
    def __init__(self, id):
        self.id = id
        self.type = 'repository'
        self.url = (
            f'https://registry.cdlib.org/api/v1/repository/{id}/'
        )
        self.details = json_loads_url(self.url + "?format=json")

        if not self.details:
            raise Http404("{0} does not exist".format(id))

        self.name = self.full_name = self.details.get('name')
        if self.details.get('ark'):
            self.contact_info = json_loads_url(
                "http://dsc.cdlib.org/institution-json/" +
                self.details.get('ark'))
        else:
            self.contact_info = ''

        self.uc = self.details.get('campus', False)
        if self.uc:
            self.full_name = "{self.uc[0].name} / {self.name}"

        self.featured_image = None
        if not self.uc:
            feat = [u for u in constants.FEATURED_UNITS if u['id'] == self.id]
            if feat:
                self.featured_image = feat.get('featuredImage')

        self.solr_filter = 'repository_url: "' + self.url + '"'


def institution_search(params, institution):
    facet_filter_types = list(constants.FACET_FILTER_TYPES)
    extra_filter = None
    if institution.type == 'repository':
        facet_filter_types = [
            f for f in constants.FACET_FILTER_TYPES
            if f['facet'] != 'repository_data'
        ]

    solr_params = search_form.solr_encode(params, facet_filter_types)
    solr_params['fq'].append(institution.solr_filter)
    solr_search = SOLR_select(**solr_params)

    facets = search_form.facet_query(facet_filter_types, params,
                                     solr_search, extra_filter)

    filter_display = {}
    for filter_type in facet_filter_types:
        param_name = filter_type['facet']
        display_name = filter_type['filter']
        filter_transform = filter_type['filter_display']

        if len(params.getlist(param_name)) > 0:
            filter_display[display_name] = list(
                map(filter_transform, params.getlist(param_name)))

    context = search_form.search_defaults(params)
    pages = int(math.ceil(
        solr_search.numFound / int(context['rows']))),
    context.update({
        'filters': filter_display,
        'search_results': solr_search.results,
        'facets': facets,
        'numFound': solr_search.numFound,
        'pages': pages,
        'institution': institution.details,
        'contact_information': institution.contact_info,
        'FACET_FILTER_TYPES': facet_filter_types
    })

    return context


def institution_collections(request, institution):

    page = int(request.GET['page']) if 'page' in request.GET else 1

    collections_params = {
        'q': '',
        'rows': 0,
        'start': 0,
        'fq': [institution.solr_filter],
        'facet': 'true',
        'facet_mincount': 1,
        'facet_limit': '-1',
        'facet_field': ['sort_collection_data'],
        'facet_sort': 'index'
    }

    collections_solr_search = SOLR_select(**collections_params)

    pages = int(
        math.ceil(
            len(collections_solr_search.facet_counts[
                'facet_fields']['sort_collection_data']) / 10))

    # solrpy gives us a dict == unsorted (!)
    # use the `facet_decade` mode of process_facets to do a
    # lexical sort by value ....
    solr_related_collections = list(
        collection[0] for collection in
        constants.DEFAULT_FACET_FILTER_TYPES[3].process_facets(
            collections_solr_search.facet_counts['facet_fields']
            ['sort_collection_data'],
            [],
            'value',
        ))
    start = ((page-1) * 10)
    end = page * 10
    solr_related_collections = solr_related_collections[start:end]

    related_collections = []
    for i, related_collection in enumerate(solr_related_collections):
        collection_parts = process_sort_collection_data(
            related_collection)
        col_id = re.match(col_regex, collection_parts[2]).group('id')
        try:
            related_collections.append(
                Collection(col_id).get_mosaic())
        except Http404:
            pass

    context = {
        'page': page,
        'pages': pages,
        'collections': related_collections,
        'contact_information': institution.contact_info,
        'institution': institution.details,
    }

    if page + 1 <= pages:
        context['next_page'] = page + 1
    if page - 1 > 0:
        context['prev_page'] = page - 1

    return context


def repository_search(request, repository_id):
    institution = Repository(repository_id)
    params = request.GET.copy()

    context = institution_search(params, institution)

    related_collections = get_related_collections(
        params, repository_id=institution.id)[0]

    context.update({
        'repository_id': institution.id,
        'uc_institution': institution.uc,
        'related_collections': related_collections,
        'form_action': reverse(
            'calisphere:repositorySearch',
            kwargs={'repository_id': institution.id}
        )
    })

    page = (int(context['start']) // int(context['rows'])) + 1
    context['title'] = f"{institution.full_name} Items"
    if page > 1:
        context['title'] = f"{institution.full_name} Items - page {page}"

    context['featuredImage'] = institution.featured_image

    if len(params.getlist('collection_data')):
        context['num_related_collections'] = len(
            params.getlist('collection_data'))
    else:
        context['num_related_collections'] = len(
            context['facets']['collection_data'])

    return render(request, 'calisphere/institutionViewItems.html', context)


def repository_collections(request, repository_id):
    institution = Repository(repository_id)

    context = institution_collections(request, institution)

    context.update({
        'repository_id': institution.id,
        'uc_institution': institution.uc,
        'featuredImage': institution.featured_image
    })

    # title for UC institutions needs to show parent campus
    # refactor, as this is copy/pasted in this commit
    context['title'] = institution.full_name
    if context['page'] > 1:
        context['title'] = (
            f"{institution.full_name} Collections - page {context['page']}")

    return render(request, 'calisphere/institutionViewCollections.html',
                  context)


def campus_search(request, campus_slug):
    institution = Campus(campus_slug)
    params = request.GET.copy()
    context = institution_search(params, institution)

    page = (int(context['start']) // int(context['rows'])) + 1
    title = f"{institution.name} Items"
    if (page > 1):
        title = (f"{institution.name} Items - page {page}")

    related_collections = get_related_collections(
        params, slug=institution.slug)[0]

    context.update({
        'repository_id': None,
        'title': title,
        'campus_slug': institution.slug,
        'related_collections': related_collections,
        'form_action': reverse(
            'calisphere:campusSearch',
            kwargs={'campus_slug': institution.slug}),
        'featuredImage': institution.featured_image
    })

    if len(params.getlist('collection_data')):
        context['num_related_collections'] = len(
            params.getlist('collection_data'))
    else:
        context['num_related_collections'] = len(
            context['facets']['collection_data'])

    return render(request, 'calisphere/institutionViewItems.html', context)


def campus_collections(request, campus_slug):
    institution = Campus(campus_slug)

    context = institution_collections(request, institution)
    context['title'] = institution.name
    if context['page'] > 1:
        context['title'] = (
            f"{institution.name} Collections - page {context['page']}")

    context['institution']['campus'] = None

    context.update({
        'campus_slug': institution.slug,
        'featuredImage': institution.featured_image,
        'repository_id': None,
    })

    return render(request, 'calisphere/institutionViewCollections.html',
                  context)


def campus_institutions(request, campus_slug):
    institution = Campus(campus_slug)

    institutions_solr_search = SOLR_select(
        q='',
        rows=0,
        start=0,
        fq=['campus_url: "' + institution.url + '"'],
        facet='true',
        facet_mincount=1,
        facet_limit='-1',
        facet_field=['repository_data'])

    related_institutions = list(
        institution[0] for institution in
        constants.DEFAULT_FACET_FILTER_TYPES[2].process_facets(
            institutions_solr_search.facet_counts['facet_fields']
            ['repository_data'], []))

    for i, related_institution in enumerate(related_institutions):
        related_institutions[i] = get_repository_data(
            repository_data=related_institution)
    related_institutions = sorted(
        related_institutions,
        key=lambda related_institution: related_institution['name'])

    return render(
        request,
        'calisphere/institutionViewInstitutions.html',
        {
            # 'campus': institution.name,
            'title': f'{institution.name} Contributors',
            'featuredImage': institution.featured_image,
            'campus_slug': campus_slug,
            'institutions': related_institutions,
            'institution': institution.details,
            'contact_information': institution.contact_info,
            'repository_id': None,
        })
