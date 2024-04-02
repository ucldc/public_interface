from django.conf import settings
from functools import wraps
from django.utils.decorators import available_attrs
from django.views.decorators.cache import cache_page

# https://stackoverflow.com/questions/27347921/in-django-can-per-view-cache-decorator-be-session-dependent-for-a-b-testings
def cache_by_session_state(func):
    @wraps(func, assigned=available_attrs(func))
    def wrapper(request, *args, **kwargs):
        index = request.session.get('index', settings.DEFAULT_INDEX)
        if (
            (index == 'solr' and not settings.SOLR_URL) or
            (index == 'es' and not settings.ES_URL)
        ):
            index = settings.DEFAULT_INDEX
        cached = cache_page(60 * 1, key_prefix=index)(func)
        return cached(request, *args, **kwargs)
    return wrapper
