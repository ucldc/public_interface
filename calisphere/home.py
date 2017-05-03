from django.views.generic import TemplateView
from django.shortcuts import render
from django.views.decorators.gzip import gzip_page
from django.utils.decorators import method_decorator

import json
import random
import os


class HomeView(TemplateView):

    template_name = "calisphere/home.html"

    def __init__(self):
        """
        Constructor. Called in the URLconf;
        """
        this_dir = os.path.dirname(os.path.realpath(__file__))
        this_data = os.path.join(this_dir, 'home-data.json')
        self.home_data = json.loads(open(this_data).read())

    @method_decorator(gzip_page)
    def get(self, request):
        """ view for home page """
        random.shuffle(self.home_data['home'])
        random.shuffle(self.home_data['uc_partners'])
        random.shuffle(self.home_data['statewide_partners'])

        # return one lock_up; and arrays for the featured stuff
        return render(request, self.template_name, {
            'lock_up':
            self.home_data['home'][0],
            'uc_partners':
            self.home_data['uc_partners'],
            'statewide_partners':
            self.home_data['statewide_partners'],
        })
