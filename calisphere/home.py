from django.conf import settings
from django.views.generic import TemplateView
from django.shortcuts import render
from django.views.decorators.gzip import gzip_page
from django.utils.decorators import method_decorator
from django.contrib.humanize.templatetags.humanize import intcomma
from calisphere.collection_data import CollectionManager

import json
import random
import os
import math


class HomeView(TemplateView):

    template_name = "calisphere/home.html"

    def __init__(self):
        """
        Constructor. Called in the URLconf;
        """
        this_dir = os.path.dirname(os.path.realpath(__file__))
        this_data = os.path.join(this_dir, 'home-data.json')
        self.home_data = json.loads(open(this_data).read())
        indexed_collections = CollectionManager("es")
        self.total_objects = intcomma(
            int(
                math.floor((int(indexed_collections.total_objects) - 1) / 25000) *
                25000))

    @method_decorator(gzip_page)
    def get(self, request):
        """ view for home page """
        random.shuffle(self.home_data['home'])
        random.shuffle(self.home_data['uc_partners'])
        random.shuffle(self.home_data['statewide_partners'])

        for partner in self.home_data['uc_partners']:
            partner['thumb'] = (
                f"{settings.UCLDC_IMAGES}/{partner['thumb']}")
        for partner in self.home_data['statewide_partners']:
            partner['thumb'] = (
                f"{settings.UCLDC_IMAGES}/{partner['thumb']}")

        # return one lock_up; and arrays for the featured stuff
        return render(
            request, self.template_name, {
                'meta_robots': None,
                'lock_up': self.home_data['home'][0],
                'uc_partners': self.home_data['uc_partners'],
                'statewide_partners': self.home_data['statewide_partners'],
                'total_objects': self.total_objects,
            })
