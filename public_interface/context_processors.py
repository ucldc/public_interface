
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

    multiple_indexes = False
    thumbnailUrl = settings.THUMBNAIL_URL
    iiifUrl = settings.UCLDC_IIIF
    nuxeoThumbnails = settings.UCLDC_NUXEO_THUMBS
    mediaUrl = settings.UCLDC_MEDIA

    if settings.SOLR_URL and settings.SOLR_API_KEY:
        multiple_indexes = True
        if request.session.get('index') == 'solr':
            thumbnailUrl = settings.THUMBNAIL_URL_SOLR
            iiifUrl = settings.UCLDC_IIIF_SOLR
            nuxeoThumbnails = settings.UCLDC_NUXEO_THUMBS_SOLR
            mediaUrl = settings.UCLDC_MEDIA_SOLR

    return {
        'thumbnailUrl': thumbnailUrl,
        'devMode': settings.UCLDC_DEVEL,
        'ucldcImages': settings.UCLDC_IMAGES,   # still used in microdata.html
        'ucldcMedia': mediaUrl,
        'ucldcIiif': iiifUrl,
        'ucldcNuxeoThumbs': nuxeoThumbnails,
        'gaSiteCode': settings.GA_SITE_CODE,
        'ga4SiteCode': settings.GA4_SITE_CODE,
        'matomoSiteCode': settings.MATOMO_SITE_CODE,
        'contactFlag': settings.CONTRUBUTOR_CONTACT_FLAG,
        'permalink': permalink,
        'multiple_indexes': multiple_indexes,
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
