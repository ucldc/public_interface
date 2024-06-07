# written based on https://github.com/django/django/blob/stable/3.2.x/django/contrib/redirects/middleware.py
# since the part of the middleware that looks up the redirect from the 
# database is not encapsulated, we cannot easily subclass this the
# RedirectFallbackMiddleware. 

from django.http import HttpResponseGone, HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
from .create_redirect_dict import get_redirects

REDIRECTS = get_redirects()

class InMemoryRedirectMiddleware(MiddlewareMixin):
    # Defined as class-level attributes to be subclassing-friendly.
    response_gone_class = HttpResponseGone
    response_redirect_class = HttpResponsePermanentRedirect

    def process_response(self, request, response):
        # No need to check for a redirect for non-404 responses.
        if response.status_code != 404:
            return response

        full_path = request.get_full_path().strip('/')
        print(full_path)

        r = None
        try:
            r = REDIRECTS[full_path]
        except KeyError:
            pass

        print(r)
        if r is not None:
            if r == '':
                return self.response_gone_class()
            return self.response_redirect_class(r)

        # No redirect was found. Return the response.
        return response