
from future import standard_library
standard_library.install_aliases()
from builtins import object
from django.conf import settings
from .cache_retry import json_loads_url
import urllib.parse


class RegistryManager(object):
    def init_registry_data(self, path):
        base = settings.UCLDC_REGISTRY_URL
        page_one = json_loads_url(urllib.parse.urljoin(base, path))
        out = dict((x['id'], x) for x in page_one['objects'])
        next_path = page_one['meta']['next']
        while next_path:
            next_page = json_loads_url(urllib.parse.urljoin(base, next_path))
            out.update(dict((x['id'], x) for x in next_page['objects']))
            next_path = next_page['meta']['next']

        return out

    def __init__(self):
        repository_path = '/api/v1/repository/?format=json'
        # collection_path = '/api/v1/collection/?format=json'
        self.repository_data = self.init_registry_data(repository_path)
        # self.collection_data = self.init_registry_data(collection_path)


"""
Copyright (c) 2015, Regents of the University of California
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
- Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
- Neither the name of the University of California nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
