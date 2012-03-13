'''
Created on Dec 23, 2011
This loads data from a tree of Json files into ShahnamaDJ
@author: ieb
'''
import os
import json
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.core.context_processors import csrf
from django.db.backends.sqlite3.base import IntegrityError
from django.views.decorators.http import condition
from django.conf import settings
import time
import logging

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
            obj = loader.createFromJson(json.load(file("%s/%s" % (path,key)),encoding=encoding), key)
            obj.save()
            return self._log("Pass 1 %s of %s " % (i,len(self.filesToLoad)),True)
        except IntegrityError as e:
            return self._log("Pass 1 %s of %s Failed Loading data from %s cause %s" % (i, len(self.filesToLoad), path, e.message))
        except Exception as detail:
            return self._log("Pass 1 %s of %s Failed Loading data from %s cause %s" % (i, len(self.filesToLoad), path, detail))


    def _buildRelationship(self, i):
        objectType = self.objectsToRelate[i]
        logging.error("WOrking on %s " % objectType)
        for dbobj in objectType.objects.all():
            dbobj.clearErrors()
            dbobj.buildRelationships()
            dbobj.save()
            errors = dbobj.getErrors()
            for e in errors:
                logging.error("Added Errors %s " % e)
                self.messages.append(self._log(e))
        return self._log("Pass 2 ........... Done %s of %s " % (i, len(self.objectsToRelate)))

    def _buildOrderedChain(self, i):
        objectType = self.objectsToChain[i]
        if  hasattr(objectType,"buildOrderedChain"):
            logging.error("Chain Ordering on %s " % objectType)
            objectType.buildOrderedChain()
        else:
            logging.error("No Chain Ordering Required on %s " % objectType)
        return self._log("Pass 3 ........... Done %s of %s " % (i, len(self.objectsToChain)))


    def _log(self, message, timedMessage = False):
        if timedMessage and (time.time() - self.lastMessage) < 5:
            return ""
        self.lastMessage = time.time()
        logging.error("Loader: %s " % message)
        return render_to_string(self.messageTemplate, { 'message' : message })

    def __iter__(self):
        return self

    def next(self):
        '''
        This is a iterator that emits messages as each operation is completed. 
        It perform loading, building relationships and building ordered chains
        The details of each operation for each model type is in the Model class itself
        '''
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
            self.objectsToChain = objectMap.values()
            self.messages.append(self._log("Will rebuild relationships... "))
            for o in self.objectsToRelate:
                self.messages.append(self._log(".... for %s " % o))
            self.messages.append(self._log("Will load %s files and rebuild for %s relationships " % (len(self.filesToLoad), len(self.objectsToRelate))))
            self.messageIndex = 0
            self.fileIndex = 0
            self.objectIndex = 0
            self.chainIndex = 0
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
                    self.messages.append(self._log("Building Relationship %s for %s " % (self.objectIndex, self.objectsToRelate[self.objectIndex])))
            else:
                self.messages.append(self._log("Phase 2  complete"))
            return self._buildRelationship(self.objectIndex-1)
        if self.chainIndex < len(self.objectsToChain):
            self.chainIndex = self.chainIndex+1
            if ( self.chainIndex < len(self.objectsToChain)):
                    self.messages.append(self._log("Ordering %s for %s " % (self.chainIndex, self.objectsToChain[self.chainIndex])))
            else:
                self.messages.append(self._log("Phase 3  complete"))
            return self._buildOrderedChain(self.chainIndex-1)
        raise StopIteration



'''
This is an output generator that gets messages from the load process and streams them
out to the output stream
'''
def renderDbLoad_generator(context, loadData, dataSource, dataStructure):
    yield render_to_string("loaddb_pre.djt.html", context )
    dbloader = DBLoader("loaddb_message.djt.html", dataSource, dataStructure, loadData)
    logging.error("loading from DB")
    for message in dbloader:
        yield message
    yield render_to_string("loaddb_post.djt.html", { 'SOURCE_DATA' : settings.SOURCE_DATA})

'''
The load view which covers both post and get. The no etag condition causes the 
loadDb fuction to stream, bypassing the Django cache. Also A login is required
'''
@login_required
@permission_required('records.loaddb')
@condition(etag_func=None)
def loadDb(request, dataSource, dataStructure):
    if request.method == "POST":
        c = {}
        c.update(csrf(request))
        logging.error("performing load")
        loadData = ('loadData' in request.POST and "Y" == request.POST['loadData'])
        return  HttpResponse(renderDbLoad_generator(c, loadData, dataSource, dataStructure), content_type="text/html")
    else:
        requestContext = RequestContext(request)
        return render_to_response("loaddb_form.djt.html", { 'SOURCE_DATA' : settings.SOURCE_DATA}, context_instance=requestContext)


