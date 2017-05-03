import ssl
# PEP 0476
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

from django.template.defaulttags import URLNode
# http://stackoverflow.com/a/20009830/1763984

old_render = URLNode.render


def new_render(cls, context):
    """ Override existing url method to use pluses instead of spaces
    """
    return old_render(cls, context).replace("%3A", ":")


URLNode.render = new_render

default_app_config = 'calisphere.apps.CalisphereAppConfig'
