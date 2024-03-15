
from future import standard_library
standard_library.install_aliases()
import urllib.parse


def settings(request):
    """
    Put selected settings variables into the default template context
    """
    from django.conf import settings
    permalink = urllib.parse.urljoin(settings.UCLDC_FRONT, request.path)
    if request.META['QUERY_STRING']:
        query_string = request.GET.copy()
        if '_pjax' in query_string:
            del query_string['_pjax']
        if len(query_string) > 0:
            permalink = '?'.join([permalink, query_string.urlencode()])

    return {
        'thumbnailUrl': settings.THUMBNAIL_URL,
        'devMode': settings.UCLDC_DEVEL,
        'ucldcImages': settings.UCLDC_IMAGES,
        'ucldcMedia': settings.UCLDC_MEDIA,
        'ucldcIiif': settings.UCLDC_IIIF,
        'ucldcNuxeoThumbs': settings.UCLDC_NUXEO_THUMBS,
        'gaSiteCode': settings.GA_SITE_CODE,
        'ga4SiteCode': settings.GA4_SITE_CODE,
        'matomoSiteCode': settings.MATOMO_SITE_CODE,
        'contactFlag': settings.CONTRUBUTOR_CONTACT_FLAG,
        'permalink': permalink,
        'q': '',
        'page': None,
        'meta_image': None,
        'campus_slug': None,
        'form_action': None,
        'numFound': None,
        'prev_page': None,
        'next_page': None,
        'featuredImage': None,
        'themedCollections': None,
        'collection_q': None,
        'alphabet': None,
        'referral': None,
    }
