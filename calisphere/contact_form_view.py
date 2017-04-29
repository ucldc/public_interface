from __future__ import unicode_literals, print_function
from collections import OrderedDict
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from contact_form.views import ContactFormView
from contact_form.forms import ContactForm
import urlparse


class CalisphereContactForm(ContactForm):
    name = forms.CharField(
        max_length=100,
        label='Name:',
        widget=forms.TextInput(attrs={'placeholder': 'Your full name'}),
    )
    email = forms.EmailField(
        max_length=200,
        label='Email:',
        widget=forms.TextInput(attrs={'placeholder': 'Your email'}),
    )
    email2 = forms.EmailField(
        max_length=200,
        label='Verify Email:',
        widget=forms.TextInput(attrs={'placeholder': 'Verify your email'}),
    )
    body = forms.CharField(
        widget=forms.Textarea,
        label='Message',
    )
    referer = forms.CharField(widget=forms.HiddenInput())

    template_name = 'contact_form/contact_form.txt'
    subject_template_name = "contact_form/contact_form_subject.txt"

    def __init__(self, request, *args, **kwargs):
        super(
            CalisphereContactForm,
            self
        ).__init__(request=request, *args, **kwargs)
        fields_keyOrder = [
            'name',
            'email',
            'email2',
            'body',
            'referer',
        ]
        if (self.fields.has_key('keyOrder')):
            self.fields.keyOrder = fields_keyOrder
        else:
            self.fields = OrderedDict(
                (k, self.fields[k]) for k in fields_keyOrder
            )


class CalisphereContactFormView(ContactFormView):
    '''view for main email contact form'''
    # use our custom form
    form_class = CalisphereContactForm
    def get_success_url(self):
        # fix the host name to stay on the proxy http://stackoverflow.com/a/5686726/1763984
        # pass the referer on to the "sent" email confirmation page
        return urlparse.urljoin(
            settings.UCLDC_FRONT ,
            '{0}?referer={1}'.format(
                reverse('contact_form_sent'),
                self.request.POST.get('referer')
            )
        )
