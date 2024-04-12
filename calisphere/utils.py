import pickle
import hashlib
import json
import sys
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
@retry(stop_max_delay=200)  # milliseconds
def json_loads_url(url_or_req):
    key = kwargs_md5(key='json_loads_url', url=url_or_req)
    data = cache.get(key)
    if not data:
        print(f"cache miss for {url_or_req}", file=sys.stderr, flush=True)
        try:
            data = json.loads(
                urllib.request.urlopen(url_or_req).read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f'HTTPError: {url_or_req} {e}', file=sys.stderr, flush=True)
            data = {}
        except urllib.error.URLError as e:
            print('URLError: ' + url_or_req + ' ' + str(e), file=sys.stderr, flush=True)
            data = {}
    return data
