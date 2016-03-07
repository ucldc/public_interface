import urlparse

def settings(request):
    """
    Put selected settings variables into the default template context
    """
    from django.conf import settings
    return {
        'thumbnailUrl': settings.THUMBNAIL_URL,
        'devMode': settings.UCLDC_DEVEL,
        'ucldcWalkMe': settings.UCLDC_WALKME,
        'ucldcImages': settings.UCLDC_IMAGES,
        'ucldcMedia': settings.UCLDC_MEDIA,
        'ucldcIiif': settings.UCLDC_IIIF,
        'gaSiteCode': settings.GA_SITE_CODE,
        'contactFlag': settings.CONTRUBUTOR_CONTACT_FLAG,
        'permalink': urlparse.urljoin(settings.UCLDC_FRONT, request.path),
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

