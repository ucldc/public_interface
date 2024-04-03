from django.conf import settings
from functools import wraps
from django.utils.decorators import available_attrs
from django.views.decorators.cache import cache_page

# https://stackoverflow.com/questions/27347921/in-django-can-per-view-cache-decorator-be-session-dependent-for-a-b-testings
def cache_by_session_state(func):
    @wraps(func, assigned=available_attrs(func))
    def wrapper(request, *args, **kwargs):
        index = request.session.get('index')

        if (
            not index or
            (index == 'solr' and not settings.SOLR_URL) or
            (index == 'es' and not settings.ES_HOST)
        ):
            # no index happens when we have a first-time visitor;
            # index variables without corresponding settings variables
            # can happen in development when there's a persistent
            # browser session across a change in settings configuration
            index = settings.DEFAULT_INDEX
            request.session['index'] = index

        cached = cache_page(60 * 1, key_prefix=index)(func)
        return cached(request, *args, **kwargs)
    return wrapper
