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
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.core.context_processors import csrf
from django.db.backends.sqlite3.base import IntegrityError
from django.views.decorators.http import condition
import time

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
'''
This class implements an iterator that iterates through the messages produced by
the data load operation. When the data load is complete the iterator will raise 
a StopIteration exception. Its important that the code driving the load continues
to iterate through all of the messages otherwise not all the operations will be 
completed.
'''
class DBLoader(object):

    messages = None

    def __init__(self, messageTemplate, startPath, sources, loadData=False):
        self.messageTemplate = messageTemplate
        self.startPath = startPath
        self.sources = sources
        self.loadData = loadData
        self.lastMessage = time.time()

    def _loadFile(self, i):
        toload = self.filesToLoad[i]
        path = toload["path"]
        key = toload["fileName"]
        encoding = toload["encoding"]
        loader = toload["loader"]
        try:
            data = json.load(file("%s/%s" % (path,key)),encoding=encoding)
            dataKey = loader.getKeyFromJson(data)
            obj = loader.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))
            obj.save()
            return self._log("Pass 1 %s of %s " % (i,len(self.filesToLoad)),True)
        except IntegrityError as e:
            return self._log("Pass 1 %s of %s Failed Loading data from %s cause %s" % (i, len(self.filesToLoad), path, e.message))
        except Exception as detail:
            return self._log("Pass 1 %s of %s Failed Loading data from %s cause %s" % (i, len(self.filesToLoad), path, detail))


    def _buildRelationship(self, i):
        objectType = self.objectsToRelate[i]
        for dbobj in objectType.objects.all():
            dbobj.clearErrors()
            dbobj.buildRelationships()
            dbobj.save()
            errors = dbobj.getErrors()
            for e in errors:
                print "Added Errors %s " % e
                self.messages.append(self._log(e))
        return self._log("Pass 2 ........... Done %s of %s " % (i, len(self.objectsToRelate)))

    def _log(self, message, timedMessage = False):
        if timedMessage and (time.time() - self.lastMessage) < 5:
            return ""
        self.lastMessage = time.time()
        return render_to_string(self.messageTemplate, { 'message' : message })

    def __iter__(self):
        return self

    def next(self):
        if self.messages is None:
            self.filesToLoad = []
            self.messages = [self._log("Performing Load in %s " % (self.startPath))]
            if os.path.isdir(self.startPath):
                if self.loadData:
                    for path in os.listdir(self.startPath):
                        if path in self.sources:
                            subdirPath = "%s/%s" % (self.startPath,path)
                            encoding = 'iso-8859-1'
                            try:
                                f = open(os.path.join(subdirPath,'+encoding'),'r')
                                encoding = f.readline()
                                f.close()
                            except:
                                pass
                            n = 0
                            for fileName in os.listdir(subdirPath):
                                if fileName != '+encoding' and len(fileName) and fileName[0] != '.':
                                    n = n + 1
                                    self.filesToLoad.append({
                                            'path': subdirPath,
                                            'fileName' : fileName,
                                            'encoding': encoding,
                                            'loader' : self.sources[path]})
                            self.messages.append(self._log("... %s %s files %s " % (path, n, encoding)))
            objectMap = {}
            for object in self.sources.values():
                if object not in objectMap:
                    objectMap[object] = object
            self.objectsToRelate = objectMap.values()
            self.messages.append(self._log("Will rebuild relationships... "))
            for o in self.objectsToRelate:
                self.messages.append(self._log(".... for %s " % o))
            self.messages.append(self._log("Will load %s files and rebuild for %s relationships " % (len(self.filesToLoad), len(self.objectsToRelate))))
            self.messageIndex = 0
            self.fileIndex = 0
            self.objectIndex = 0
        if self.messageIndex < len(self.messages):
            self.messageIndex = self.messageIndex+1
            return self.messages[self.messageIndex-1]
        if self.fileIndex < len(self.filesToLoad):
            self.fileIndex = self.fileIndex+1
            if ( self.fileIndex == len(self.filesToLoad)):
                self.messages.append(self._log("Phase 1 complete "))
            return self._loadFile(self.fileIndex-1)
        if self.objectIndex < len(self.objectsToRelate):
            self.objectIndex = self.objectIndex+1
            if ( self.objectIndex < len(self.objectsToRelate)):
                    self.messages.append(self._log("Building %s for %s " % (self.objectIndex, self.objectsToRelate[self.objectIndex])))
            else:
                self.messages.append(self._log("Phase 2  complete"))
            return self._buildRelationship(self.objectIndex-1)
        raise StopIteration


'''
This is an output generator that gets messages from the load process and streams them
out to the output stream
'''
def renderLoad_generator(context):
    yield render_to_string("loaddb_pre.djt.html", context )
    dbloader = DBLoader("loaddb_message.djt.html", SOURCE_DATA, SOURCE_DATA_TYPES, False)
    print "loading from DB"
    for message in dbloader:
        yield message
    yield render_to_string("loaddb_post.djt.html", {"assets": STATIC_URL})

'''
The load view which covers both post and get. The no etag condition causes the 
loadDb fuction to stream, bypassing the Django cache. Also A login is required
'''
@login_required
@permission_required('records.loaddb')
@condition(etag_func=None)
def loadDb(request):
    if request.method == "POST":
        c = {"assets" : STATIC_URL}
        c.update(csrf(request))
        print "performing load"
        return  HttpResponse(renderLoad_generator(c), content_type="text/html")
    else:
        requestContext = RequestContext(request)
        print "loading Get Screen"
        return render_to_response("loaddb_form.djt.html", {"assets": STATIC_URL}, context_instance=requestContext)
