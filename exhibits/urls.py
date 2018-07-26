from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^$', views.exhibitRandom, name='randomExplore'),
    url(r'jarda-related-resources/$', TemplateView.as_view(template_name='exhibits/jarda-related-resources.html'), name='jarda-related-resources'),
    url(r'^search/', views.exhibitSearch, name='exhibitSearch'),
    url(r'^browse/(?P<category>[-\w]+)/$', views.exhibitDirectory, name='exhibitDirectory'),
    url(r'^(?P<exhibit_id>\d+)/(?P<exhibit_slug>[-\w]+)/$', views.exhibitView, name='exhibitView'),
    url(r'^(?P<exhibit_id>\d+)/items/(?P<item_id>.+)/$', views.itemView, name='itemView'),
    url(r'^essay/(?P<essay_id>\d+)/(?P<essay_slug>[-\w]+)/$', views.essayView, name='essayView'),
    url(r'^t(?P<theme_id>\d+)/(?P<theme_slug>[-_\w]+)/$', views.themeView, name='themeView'),
    url(r'^exhibitReport/$', views.exhibitItemView, name='exhibitReport')
]
