from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from ShahnamaDJ.records.views import chapterView, countryView, illustrationView,\
    locationView, manuscriptView, sceneView
from ShahnamaDJ.migration.loaddb import loadDb
from ShahnamaDJ.settings import SOURCE_DATA, DEBUG, MEDIA_URL, MEDIA_ROOT
from ShahnamaDJ.loaddb import RECORDS_SOURCE_DATA, CONTENT_SOURCE_DATA
from ShahnamaDJ.content.views import pageView, pageListView, homeView, pageEdit,\
    pageCreate, pageFramedImageView, pageTrimImageView
admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ShahnamaDJ.views.home', name='home'),
    # url(r'^ShahnamaDJ/', include('ShahnamaDJ.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Load the database with information from a set of json files.
    url(r'^admin/loadDb', loadDb,  {'dataSource' :SOURCE_DATA, 'dataStructure':RECORDS_SOURCE_DATA }),
    url(r'^admin/loadEvents', loadDb, {'dataSource':SOURCE_DATA, 'dataStructure':CONTENT_SOURCE_DATA }),
    url(r'^admin/pages', pageListView),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.djt.html'}),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.djt.html'}),

    
    # application
    url(r'^$', homeView, name='home'),
    url(r'^index.html$', homeView, name='home'),
    url(r'^front.*$', homeView, name='home'),
    url(r'^page/(.*)_new$', pageCreate, {'onsave' : '/page/%s'}),
    url(r'^page/(.*)_edit$', pageEdit, {'onsave' : '/page/%s'}),
    url(r'^page/(.*)_(.*)/framed$', pageFramedImageView, {'onsave' : '/page/%s_%s/framed'}),
    url(r'^page/(.*)_(.*)/trim.json$', pageTrimImageView),
    url(r'^page/(.*)$', pageView),
    url(r'^chapter/(.*)', chapterView, name='chapter'),
    url(r'^country/(.*)', countryView, name='country'),
    url(r'^illustration/(.*)', illustrationView, name='illustration'),
    url(r'^location/(.*)', locationView, name='location'),
    url(r'^manuscript/(.*)', manuscriptView, name='manuscript'),
    url(r'^scene/(.*)', sceneView, name='scene'),
)
if DEBUG:
    from django.views.static import serve
    _media_url = MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns += patterns('',
                                (r'^%s(?P<path>.*)$' % _media_url,
                                serve,
                                {'document_root': MEDIA_ROOT}))
    del(_media_url, serve)
