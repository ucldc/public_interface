from django.core.management.base import BaseCommand
from calisphere.sitemap_generator import CalisphereSitemapGenerator


class Command(BaseCommand):
    command = None
    help = 'generate sitemaps files for Calisphere'

    def handle(self, **options):
        generator = CalisphereSitemapGenerator(
            int(options.get('verbosity', 0)))
        generator.write()
