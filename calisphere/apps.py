from django.apps import AppConfig
from calisphere.registry_data import RegistryManager


class CalisphereAppConfig(AppConfig):
    # http://stackoverflow.com/a/16111968/1763984
    name = 'calisphere'
    verbose_name = name

    def ready(self):
        self.registry = RegistryManager()
