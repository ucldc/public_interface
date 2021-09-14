from functools import wraps
from django.utils.decorators import available_attrs
from django.views.decorators.cache import cache_page

# https://stackoverflow.com/questions/27347921/in-django-can-per-view-cache-decorator-be-session-dependent-for-a-b-testings
def cache_by_session_state(func):
    @wraps(func, assigned=available_attrs(func))
    def wrapper(request, *args, **kwargs):
        print(f'from decorator: {request.session["index"]}')
        cached = cache_page(60 * 15, key_prefix=request.session['index'])(func)
        return cached(request, *args, **kwargs)
    return wrapper
