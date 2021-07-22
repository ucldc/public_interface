from future import standard_library
from django.shortcuts import render
from django.urls import reverse
from django.http import Http404
from . import constants
from . import views
from .facet_filter_type import getCollectionData, getRepositoryData
from .cache_retry import SOLR_select, json_loads_url

import math
import re
import string

standard_library.install_aliases()

repo_regex = (r'https://registry\.cdlib\.org/api/v1/repository/'
              r'(?P<repository_id>\d*)/?')


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
        repository = getRepositoryData(repository_url=repository_url)
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
        repository = getRepositoryData(repository_url=repository_url)
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


def institution_view(request,
                     institution_id,
                     subnav=False,
                     institution_type='repository|campus'):
    institution_url = (
        f'https://registry.cdlib.org/api/v1/'
        f'{institution_type}/{institution_id}/'
    )
    institution_details = json_loads_url(institution_url + "?format=json")

    if not institution_details:
        raise Http404("{0} does not exist".format(institution_id))

    if institution_details.get('ark'):
        contact_information = json_loads_url(
            "http://dsc.cdlib.org/institution-json/" +
            institution_details.get('ark'))
    else:
        contact_information = ''

    if institution_details.get('campus'):
        uc_institution = institution_details.get('campus')
    else:
        uc_institution = False

    if subnav == 'items':
        params = request.GET.copy()

        facet_filter_types = list(constants.FACET_FILTER_TYPES)
        extra_filter = None
        if institution_type == 'repository':
            facet_filter_types = [
                f for f in constants.FACET_FILTER_TYPES
                if f['facet'] != 'repository_data'
            ]
            extra_filter = 'repository_url: "' + institution_url + '"'
        elif institution_type == 'campus':
            extra_filter = 'campus_url: "' + institution_url + '"'

        solr_params = views.solrEncode(params, facet_filter_types)
        if extra_filter:
            solr_params['fq'].append(extra_filter)
        solr_search = SOLR_select(**solr_params)

        facets = views.facetQuery(facet_filter_types, params, solr_search,
                                  extra_filter)

        filter_display = {}
        for filter_type in facet_filter_types:
            param_name = filter_type['facet']
            display_name = filter_type['filter']
            filter_transform = filter_type['filter_display']

            if len(params.getlist(param_name)) > 0:
                filter_display[display_name] = list(
                    map(filter_transform, params.getlist(param_name)))

        context = views.searchDefaults(params)
        context.update({
            'filters':
            filter_display,
            'search_results':
            solr_search.results,
            'facets':
            facets,
            'numFound':
            solr_search.numFound,
            'pages':
            int(math.ceil(
                solr_search.numFound / int(context['rows']))),
            'institution':
            institution_details,
            'contact_information':
            contact_information,
            'FACET_FILTER_TYPES':
            facet_filter_types
        })

        page = (int(context['start']) // int(context['rows'])) + 1
        if institution_type == 'campus':
            if (page > 1):
                title = (
                    f"{institution_details.get('name')} Items - page {page}"
                )
            else:
                title = f"{institution_details.get('name')} Items"

            context.update({
                'repository_id':
                None,
                'title':
                title,
                'campus_slug':
                institution_details.get('slug'),
                'related_collections':
                views.getRelatedCollections(
                    params, slug=institution_details.get('slug'))[0],
                'form_action':
                reverse(
                    'calisphere:campusView',
                    kwargs={
                        'campus_slug': institution_details.get('slug'),
                        'subnav': 'items'
                    })
            })
            for campus in constants.CAMPUS_LIST:
                if (institution_id == campus['id'] 
                        and 'featuredImage' in campus):
                    context['featuredImage'] = campus['featuredImage']

        if institution_type == 'repository':
            context.update({
                'repository_id':
                institution_id,
                'uc_institution':
                uc_institution,
                'related_collections':
                views.getRelatedCollections(params,
                                            repository_id=institution_id)[0],
                'form_action':
                reverse(
                    'calisphere:repositoryView',
                    kwargs={
                        'repository_id': institution_id,
                        'subnav': 'items'
                    })
            })

            # title for UC institutions needs to show parent campus
            if uc_institution and page > 1:
                context['title'] = '{0} / {1} Items - page {2}'.format(
                    uc_institution[0]['name'], institution_details.get('name'),
                    page)
            elif uc_institution:
                context['title'] = '{0} / {1} Items'.format(
                    uc_institution[0]['name'], institution_details.get('name'))
            elif page > 1:
                context['title'] = '{0} Items - page {1}'.format(
                    institution_details.get('name'), page)
            else:
                context['title'] = '{0} Items'.format(
                    institution_details.get('name'))

            if uc_institution is False:
                for unit in constants.FEATURED_UNITS:
                    if unit['id'] == institution_id:
                        context['featuredImage'] = unit['featuredImage']

        if len(params.getlist('collection_data')):
            context['num_related_collections'] = len(
                params.getlist('collection_data'))
        else:
            context['num_related_collections'] = len(facets['collection_data'])

        return render(request, 'calisphere/institutionViewItems.html', context)

    else:
        page = int(request.GET['page']) if 'page' in request.GET else 1

        if institution_type == 'repository':
            institutions_fq = ['repository_url: "' + institution_url + '"']
        if institution_type == 'campus':
            institutions_fq = ['campus_url: "' + institution_url + '"']

        collections_params = {
            'q': '',
            'rows': 0,
            'start': 0,
            'fq': institutions_fq,
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
        # doing the search again;
        # could we slice this from the results above?
        collections_params['facet_offset'] = (page - 1) * 10
        collections_params['facet_limit'] = 10
        collections_params['facet_sort'] = 'index'
        collections_solr_search = SOLR_select(**collections_params)

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

        related_collections = []
        for i, related_collection in enumerate(solr_related_collections):
            collection_parts = views.process_sort_collection_data(
                related_collection)
            collection_data = getCollectionData(
                collection_data='{0}::{1}'.format(
                    collection_parts[2],
                    collection_parts[1],
                ))
            collection_mosaic = views.getCollectionMosaic(
                collection_data.get('url'))
            if collection_mosaic:
                related_collections.append(collection_mosaic)

        context = {
            'page': page,
            'pages': pages,
            'collections': related_collections,
            'contact_information': contact_information,
            'institution': institution_details,
        }

        if page + 1 <= pages:
            context['next_page'] = page + 1
        if page - 1 > 0:
            context['prev_page'] = page - 1

        if institution_type == 'campus':
            context['campus_slug'] = institution_details.get('slug')
            if page > 1:
                context['title'] = '{0} Collections - page {1}'.format(
                    institution_details.get('name'), page)
            else:
                context['title'] = institution_details.get('name')

            for campus in constants.CAMPUS_LIST:
                if institution_id == campus.get(
                        'id') and 'featuredImage' in campus:
                    context['featuredImage'] = campus.get('featuredImage')
            context['repository_id'] = None
            context['institution']['campus'] = None

        if institution_type == 'repository':
            context['repository_id'] = institution_id
            context['uc_institution'] = uc_institution
            # title for UC institutions needs to show parent campus
            # refactor, as this is copy/pasted in this commit
            if uc_institution and page > 1:
                context['title'] = '{0} / {1} Collections - page {2}'.format(
                    uc_institution[0]['name'], institution_details.get('name'),
                    page)
            elif uc_institution:
                context['title'] = '{0} / {1}'.format(
                    uc_institution[0]['name'], institution_details.get('name'))
            elif page > 1:
                context['title'] = '{0} Collections - page {1}'.format(
                    institution_details.get('name'), page)
            else:
                context['title'] = institution_details.get('name')

            if uc_institution is False:
                for unit in constants.FEATURED_UNITS:
                    if unit.get('id') == institution_id:
                        context['featuredImage'] = unit.get('featuredImage')

            if 'featuredImage' not in context:
                context['featuredImage'] = None

        return render(request, 'calisphere/institutionViewCollections.html',
                      context)


def campus_view(request, campus_slug, subnav=False):
    campus_id = ''
    featured_image = ''
    for campus in constants.CAMPUS_LIST:
        if campus_slug == campus['slug']:
            campus_id = campus['id']
            campus_name = campus['name']
            if 'featuredImage' in campus:
                featured_image = campus['featuredImage']
    if campus_id == '':
        print('Campus registry ID not found')

    if subnav == 'institutions':
        campus_url = f'https://registry.cdlib.org/api/v1/campus/{campus_id}/'
        campus_details = json_loads_url(campus_url + "?format=json")

        if 'ark' in campus_details and campus_details['ark'] != '':
            contact_information = json_loads_url(
                "http://dsc.cdlib.org/institution-json/" +
                campus_details['ark'])
        else:
            contact_information = ''

        campus_fq = ['campus_url: "' + campus_url + '"']

        institutions_solr_search = SOLR_select(
            q='',
            rows=0,
            start=0,
            fq=campus_fq,
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
            related_institutions[i] = getRepositoryData(
                repository_data=related_institution)
        related_institutions = sorted(
            related_institutions,
            key=lambda related_institution: related_institution['name'])

        return render(
            request,
            'calisphere/institutionViewInstitutions.html',
            {
                # 'campus': campus_name,
                'title': f'{campus_name} Contributors',
                'featuredImage': featured_image,
                'campus_slug': campus_slug,
                'institutions': related_institutions,
                'institution': campus_details,
                'contact_information': contact_information,
                'repository_id': None,
            })

    else:
        return institution_view(request, campus_id, subnav, 'campus')


def repository_view(request, repository_id, subnav=False):
    return institution_view(request, repository_id, subnav, 'repository')
