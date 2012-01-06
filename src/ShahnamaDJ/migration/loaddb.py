'''
Created on Dec 23, 2011
This loads data from a tree of Json files into ShahnamaDJ
@author: ieb
'''
import sys
import os
import json
from ShahnamaDJ.settings import SOURCE_DATA, STATIC_URL
from ShahnamaDJ.records.models import Chapter, Country, Location, Manuscript,\
    Scene, Illustration, Authority
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.core.context_processors import csrf

# This the the mapping of folder into Object type for the json data
# eg SOURCE_DATA/chapter contains json files for Chapter objects
SOURCE_DATA_TYPES = {
        'chapter' : Chapter,
        'country' : Country,
        'location' : Location,
        'manuscript' : Manuscript,
        'scene' : Scene,
        'illustration' : Illustration,
        'ms-type' : Authority,
        'ms-author' : Authority,
        'ms-status' : Authority,
        'ms-title' : Authority,
        'ms-lang' : Authority,
        'bib-class' : Authority,
        'record-status' : Authority,
        'chapter-k' : Authority,
        'chapter-b' : Authority,
        'chapter-ds' : Authority,
        'ill-format' : Authority
        }
class DBLoader(object):
    '''
    Load the data from files into the object model
    '''
    def _loadDevData(self,name,path,loader):
        ''' work out what he encoding is of the json by reading he +encoding file '''
        encoding = 'UTF-8'
        try:
            f = open(os.path.join(path,'+encoding'),'r')
            encoding = f.readline()
            f.close()
        except:
            pass
        print >>sys.stderr,"encoding="+encoding
        ''' iterate through all files, loading each one in turn into the database, the name of the file is the key, 
            the contents are the data '''
        for key in os.listdir(path):
            if key != '+encoding' and len(key) and key[0] != '.':
                data = json.load(file("%s/%s" % (path,key)),encoding=encoding)
                obj = loader.objects.create(key=key, data = data)
                obj.save()
    
    '''
    Load all the data in a sub path using the directory names to map to object types, and then 
    reconnect all relationships for all objects.
    '''
    def loadData(self, path, sources, feedback):
        ''' Load the data from Json files, the folder name maps to the object type '''
        feedback.log({ 'message' : "Performing Load" })
        if os.path.isdir(path):
            for key in os.listdir(path):
                if key in sources:
                    feedback.log({ 'message' : "Loading data from %s%s" % (path,key) })
                    self._loadDevData(key, "%s%s/" % (path,key), sources[key] )
            ''' load all the objects in sources and recompute relationships '''
            for (key,object) in sources:
                feedback.log({ 'message' : "Building relationships for %s " % (key) })
                for dbobj in object.objects.all():
                    dbobj.buildRelationships()
                    dbobj.save()
        else:
            feedback.log({ 'message' : "Load Directory does not exists %s " % path})
        feedback.log({ 'message' : "Loading complete" })
                
    '''
    Load all data using the settings configured in the DJango model.
    '''
    def loadUsingSettings(self, feedback):
        self.loadData(SOURCE_DATA,SOURCE_DATA_TYPES, feedback)

class FeedBackHandler(object):
    response = None
    template = None
    def __init__(self, response, template):
        self.response = response
        self.template = template
        
    def log(self,message):
        s = render_to_string(self.template,message)
        print s
        self.response.write(s)
    
@login_required
def loadDb(request):
    if request.method == "POST":
        print "performing load"
        dbloader = DBLoader()
        c = {"assets" : STATIC_URL}
        c.update(csrf(request))
        response =  HttpResponse(render_to_string("loaddb_pre.djt.html", c ),content_type="text/html")
        response.flush()
        dbloader.loadUsingSettings(FeedBackHandler(response,"loaddb_message.djt.html"))        
        response.write(render_to_string("loaddb_post.djt.html", {"assets": STATIC_URL}))
        response.flush()
        return response
    else:
        requestContext = RequestContext(request)
        print "loading Get Screen"
        return render_to_response("loaddb_form.djt.html", {"assets": STATIC_URL}, context_instance=requestContext)
