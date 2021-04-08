from django.conf.urls import patterns, include, url
from django.views.static import serve
from django.views.generic.base import RedirectView
import sys, os
sys.path.append(os.path.abspath("myapp"))
print(os.path.abspath("myapp"))
import views
# from .views import *
# from .views import home_page

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = patterns('',
    url(r'^$',  views.home_page, name ='home_page'),
    url(r'^dashboard/$', views.dashboard_home, name = 'dashboard_home'),
    url(r'^filter_data/(?P<asset_filter>[\w-]+)$', views.filter_data, name ='filter_data'),
    #url(r'^filter_data_item/(?P<item_filter>[\w-]+)$', views.filter_data_item, name ='filter_data_item'),
    url(r'^filter_data_time/(?P<time_filter>[\w-]+)$', views.filter_data_time, name ='filter_data_time'),

    url(r'^signup/$', views.signup, name='signup'),
    url(r'^forgot/$', views.forgot, name='forgot'),
    url(r'^login/$', views.login, name='login'),
    url(r'^confirm/$', views.confirm, name='confirm'),
    url(r'^confirmemail/$', views.confirmemail, name='confirmemail'),
 )
