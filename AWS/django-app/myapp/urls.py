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
    url(r'^filter_data_time/(?P<time_filter>[\w-]+)$', views.filter_data_time, name ='filter_data_time'),
    url(r'^download/(?P<time_filter>[\w-]+)$', views.download, name='download'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^forgot/$', views.forgot, name='forgot'),
    url(r'^login/$', views.login, name='login'),
    url(r'^confirm/$', views.confirm, name='confirm'),
    url(r'^confirmemail/$', views.confirmemail, name='confirmemail'),
    url(r'^accounts/logout/$', views.logout, name='logout'),
    url(r'^np/$', views.newpassword, name='newpassword'),
    url(r'^checkemail/$', views.checkemail, name='checkemail'),
    url(r'^cp/$', views.changepassword, name='changepassword'),
 )
