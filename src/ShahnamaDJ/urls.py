from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from ShahnamaDJ.records.views import ChapterView, CountryView, IllustrationView,\
    LocationView, ManuscriptView, SceneView
admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ShahnamaDJ.views.home', name='home'),
    # url(r'^ShahnamaDJ/', include('ShahnamaDJ.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    
    
    # application
    url(r'^$', 'ShahnamaDJ.views.home', name='home'),
    url(r'^chapter/(.*)', ChapterView.view, name='chapter'),
    url(r'^country/(.*)', CountryView.view, name='country'),
    url(r'^illustration/(.*)', IllustrationView.view, name='illustration'),
    url(r'^location/(.*)', LocationView.view, name='location'),
    url(r'^manuscript/(.*)', ManuscriptView.view, name='manuscript'),
    url(r'^scene/(.*)', SceneView.view, name='scene'),
)
