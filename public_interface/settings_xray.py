

from .settings import *

INSTALLED_APPS =  INSTALLED_APPS + ('aws_xray_sdk.ext.django',)

MIDDLEWARE = ('aws_xray_sdk.ext.django.middleware.XRayMiddleware',) + MIDDLEWARE

XRAY_RECORDER = {
    'AUTO_INSTRUMENT': True,
    'AWS_XRAY_TRACING_NAME': 'calisphere public interface',
    'AWS_XRAY_CONTEXT_MISSING': 'LOG_ERROR',
    'PLUGINS': ('ElasticBeanstalkPlugin', 'EC2Plugin'),
}

