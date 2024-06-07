from django.apps import AppConfig
from calisphere.registry_data import RegistryManager
from redirects.create_redirect_dict import get_redirects


class CalisphereAppConfig(AppConfig):
    # http://stackoverflow.com/a/16111968/1763984
    name = 'calisphere'
    verbose_name = name

    def ready(self):
        self.registry = RegistryManager()
        self.redirects = get_redirects()
