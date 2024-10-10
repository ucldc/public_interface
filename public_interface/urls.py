
from django.urls import include, re_path
from django.contrib import admin
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from calisphere.contact_form_view import CalisphereContactFormView
from exhibits.views import calCultures

from calisphere.sitemaps import *

admin.autodiscover()

sitemaps = {
    'static': StaticSitemap,
    'institutions': InstitutionSitemap,
    'collections': CollectionSitemap,
    'themes': ThemeSitemap,
    'exhibitions': ExhibitSitemap,
    'lessonPlans': LessonPlanSitemap,
    'historicalEssays': HistoricalEssaySitemap,
    'items': ItemSitemap,
}

urlpatterns = [
    re_path(r'^', include('calisphere.urls', namespace="calisphere")),
    re_path(r'^exhibitions/', include('exhibits.urls', namespace="exhibits")),
    re_path(r'^for-educators/', include(('exhibits.teacher_urls', 'for-teachers'), namespace="for-teachers")),
    re_path(r'^cal-cultures/', calCultures, name="cal-cultures"),

    re_path(r'^admin/', admin.site.urls),
    re_path(r'^contact/$',
        CalisphereContactFormView.as_view(),
        name='contact_form'),
    re_path(r'^contact/sent/$',
        TemplateView.as_view(
            template_name='django_contact_form/contact_form_sent.html'),
        name='contact_form_sent'),
    re_path(r'^robots.txt$',
        lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")
    ),
    re_path(r'', include('static_sitemaps.urls')),
    re_path(r'^sitemaps/', include('calisphere.urls', namespace="sitemaps")),
    re_path(r'^healthcheck/', include('health_check.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
