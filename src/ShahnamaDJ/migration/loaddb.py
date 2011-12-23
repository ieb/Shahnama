'''
Created on Dec 23, 2011
This loads data from a tree of Json files into ShahnamaDJ
@author: ieb
'''
import sys
import os
import json
from ShahnamaDJ.settings import SOURCE_DATA, SOURCE_DATA_TYPES
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
    def loadData(self, path, sources):
        ''' Load the data from Json files, the folder name maps to the oject type '''
        for key in os.listdir(path):
            if key in sources:
                self._loadDevData(key, "%s%s/" % (path,key), sources[key] )
        ''' load all the objects in sources and recompute relationships '''
        for (key,object) in sources:
            for dbobj in object.objects.all():
                dbobj.buildRelationships()
                dbobj.save()
                
    '''
    Load all data using the settings configured in the DJango model.
    '''
    def loadUsingSettings(self):
        self.loadData(SOURCE_DATA,SOURCE_DATA_TYPES)