from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from ShahnamaDJ.records.views import chapterView, countryView, illustrationView,\
    locationView, manuscriptView, sceneView
from ShahnamaDJ.migration import loaddb
from ShahnamaDJ.migration.loaddb import loadDb
from ShahnamaDJ.settings import STATIC_URL
admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ShahnamaDJ.views.home', name='home'),
    # url(r'^ShahnamaDJ/', include('ShahnamaDJ.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Load the database with information from a set of json files.
    url(r'^admin/loaddb', loadDb),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.djt.html', 'extra_context' : {'assets' : STATIC_URL}}),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.djt.html', 'extra_context' : {'assets' : STATIC_URL}}),

    
    # application
    #url(r'^$', 'ShahnamaDJ.views.home', name='home'),
    url(r'^chapter/(.*)', chapterView, name='chapter'),
    url(r'^country/(.*)', countryView, name='country'),
    url(r'^illustration/(.*)', illustrationView, name='illustration'),
    url(r'^location/(.*)', locationView, name='location'),
    url(r'^manuscript/(.*)', manuscriptView, name='manuscript'),
    url(r'^scene/(.*)', sceneView, name='scene'),
)
