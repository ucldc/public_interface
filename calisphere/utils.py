import pickle
import hashlib
import json
import urllib.request
import urllib.error
import urllib.parse

from django.core.cache import cache
from retrying import retry


# create a hash for a cache key
def kwargs_md5(**kwargs):
    m = hashlib.md5()
    m.update(pickle.dumps(kwargs))
    return m.hexdigest()


# wrapper function for json.loads(urllib2.urlopen)
@retry(wait_exponential_multiplier=2, stop_max_delay=10000)  # milliseconds
def json_loads_url(url_or_req):
    key = kwargs_md5(key='json_loads_url', url=url_or_req)
    data = cache.get(key)
    if not data:
        try:
            data = json.loads(
                urllib.request.urlopen(url_or_req).read().decode('utf-8'))
        except urllib.error.HTTPError:
            data = {}
    return data

# Escape OpenSearch `query_string` query reserved characters
# (Solr has a smaller, overlapping subset of special characters)
# Exceptions:
#  - we are allowing phrase queries surrounded by ""
#  - we are allowing wildcard expressions using *
def query_string_escape(text):
    for reserved in ['\\', '+', '-', '=', '&&', '||',
                     '!', '(', ')', '{', '}',
                     '[', ']', '^', '~', '?',
                     "'", ':', '/']:
        text = text.replace(reserved, f'\\{reserved}')

    return text
