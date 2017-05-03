#!/usr/bin/env python

from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import chr
from builtins import object
import urllib.request, urllib.error, urllib.parse
from collections import namedtuple
import string
import random
from .cache_retry import json_loads_url
from django.core.cache import cache
from django.conf import settings
import time

CollectionLink = namedtuple('CollectionLink', 'url, label')


class CollectionManager(object):
    """ manage collection information that is parsed from solr facets """

    def __init__(self, solr_url, solr_key):
        cache_key = 'collection-manager'  # won't vary except on djano restart
        saved = cache.get(cache_key)
        if saved:
            # got this cached
            self.data = saved['data']  # `_data` from solr
            self.parsed = saved['parsed']  # parsed into `CollectionLink`
            self.names = saved['names']  # dict of URL-> collection label
            self.split = saved['split']  # set up for a-z
            self.no_collections = saved[
                'no_collections']  # number of collections per letter for a-z
            self.shuffled = saved['shuffled']  # For the collections explore
        else:
            # look it up from solr
            url = (
                '{0}/query?facet.field=collection_data&facet=on&rows=0&facet.limit=-1&facet.mincount=1'
                .format(solr_url))
            req = urllib.request.Request(url, None,
                                  {'X-Authentication-Token': solr_key})
            save = {}
            save['data'] = self.data = json_loads_url(req)['facet_counts'][
                'facet_fields']['collection_data'][::2]
            self.parse()
            save['parsed'] = self.parsed
            save['names'] = self.names
            save['split'] = self.split
            save['no_collections'] = self.no_collections
            save['shuffled'] = self.shuffled
            cache.set(cache_key, save, settings.DJANGO_CACHE_TIMEOUT)

    def parse(self):
        def sort_key(collection_link):
            return collection_link.label.translate(
                {ord(c): None
                 for c in string.punctuation}).upper()

        self.parsed = sorted(
            [CollectionLink(*x.rsplit('::')) for x in self.data], key=sort_key)

        split_collections = {'num': [], 'a': []}
        names = {}

        current_char = 'a'
        for collection_link in self.parsed:
            names[collection_link.url] = collection_link.label
            for c in collection_link.label:
                if c not in string.punctuation:
                    if c in string.digits:
                        split_collections['num'].append(collection_link)
                    elif c.lower() == current_char:
                        split_collections[current_char].append(collection_link)
                    else:
                        while c.lower() != current_char and current_char <= 'z':
                            current_char = chr(ord(current_char) + 1)
                            split_collections[current_char] = []
                        split_collections[current_char].append(collection_link)
                    break
        self.split = split_collections
        self.names = names

        self.no_collections = []
        for c in list(string.ascii_lowercase):
            if len(self.split[c]) == 0:
                self.no_collections.append(c)

        random.seed(time.strftime("%d/%m/%Y"))

        self.shuffled = random.sample(self.parsed, len(self.parsed))


"""
Copyright (c) 2016, Regents of the University of California
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
