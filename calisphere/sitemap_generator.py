import re
from builtins import next
from builtins import range
import os
import gzip
import shutil
from django.template import loader
from django.contrib.sitemaps import Sitemap as RegularDjangoSitemap
from static_sitemaps.generator import SitemapGenerator
from static_sitemaps import conf
from calisphere.collection_data import CollectionManager
from public_interface import settings

class CalisphereSitemapGenerator(SitemapGenerator):
    ''' subclass django-static-sitemaps '''

    def __init__(self, verbosity):
        SitemapGenerator.__init__(self, verbosity)
        self.baseurl = self.normalize_url(conf.get_url())

    def write_index(self):
        ''' write sitemap.xml index file and the sitemap files it references '''
        parts = []

        for section, site in list(self.sitemaps.items()):
            if issubclass(site, RegularDjangoSitemap):
                parts.extend(self.write_data_regular(section, site))
            elif section == 'items':
                collections = CollectionManager(settings.SOLR_URL,
                                 settings.SOLR_API_KEY).parsed
                print(len(collections))
                for collection in collections:
                    col_id = re.match(
                        r'^https://registry.cdlib.org/api/v1/collection/(?P<collection_id>\d+)/$',
                    collection.url).group('collection_id')
                    parts.extend(self.write_data_fast(
                        f"collection_{col_id}", site, collection.url))
            else:
                parts.extend(self.write_data_fast(section, site))

        path = os.path.join(conf.ROOT_DIR, 'sitemap.xml')
        self.out('Writing index file.', 2)

        output = loader.render_to_string(conf.INDEX_TEMPLATE,
                                         {'sitemaps': parts})
        self._write(path, output)

    def write_data_regular(self, section, site):
        ''' process regular Django sitemap, which assumes list data '''
        if callable(site):
            pages = site().paginator.num_pages
        else:
            pages = site.paginator.num_pages

        parts = []
        for page in range(1, pages + 1):
            filename = conf.FILENAME_TEMPLATE % {
                'section': section,
                'page': page
            }
            lastmod = self.write_page(site, page, filename)

            if conf.USE_GZIP:
                filename += '.gz'

            parts.append({
                'location': '%s%s' % (self.baseurl, filename),
                'lastmod': lastmod
            })

        return parts

    def write_data_fast(self, section, site, collection_url=None):
        ''' process data using generator and streaming xml '''
        # FIXME need to generalize this code if we ever want to use it for anything other than Calisphere items
        sitemap = site(collection_url)
        items = sitemap.items()  # generator yielding all items
        parts = []

        for page in range(sitemap.num_pages):
            filename = conf.FILENAME_TEMPLATE % {
                'section': section,
                'page': page + 1
            }
            self.out('Writing sitemap %s' % filename, 2)
            path = os.path.join(conf.ROOT_DIR, filename)
            with open(path, 'w+') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>')
                f.write(
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
                )
                if (page+1 == sitemap.num_pages):
                    limit = sitemap.solr_total % sitemap.limit
                else:
                    limit = sitemap.limit
                for n in range(limit):
                    item = next(items)
                    f.write('<url>')
                    f.write(
                        '<loc>https://calisphere.org/item/{0}/</loc>'.format(
                            item['id'])
                    )  # FIXME hardcoded to only work for Calisphere items
                    # <lastmod>
                    f.write('<lastmod>{0}</lastmod>'.format(item['timestamp']))
                    # <changefreq>
                    # <priority>
                    # <lastmod>
                    # FIXME hardcoded to only work for Calisphere items
                    if item['reference_image_md5']:
                        f.write(
                            '<image:image><image:loc>https://calisphere.org/crop/999x999/{0}</image:loc></image:image>'
                            .format(item['reference_image_md5']))
                    f.write('</url>')
                f.write('</urlset>')

            if conf.USE_GZIP:
                self.compress(path)
                filename += '.gz'
            # implement lastmod?
            parts.append({
                'lastmod': None,
                'location': '{}{}'.format(self.baseurl, filename)
            })

        return parts

    def compress(self, path):
        self.out('Compressing...')
        with open(path, 'rb') as f_in, gzip.open('{}.gz'.format(path),
                                                 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
