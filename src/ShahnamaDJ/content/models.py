'''
Created on Jan 10, 2012

@author: ieb
'''
from django.db import models
import json
from django.contrib import admin

class ContentModel(models.Model):
    id = models.CharField(max_length=32,primary_key=True)
    key = models.CharField(max_length=32, null=True)
    errors = []

    def buildRelationships(self):
        None



    def _getReferencedObject(self, field, model, json, linkName):
        if linkName in json and json[linkName] is not None:
            if field is None or field.id != json[linkName]:
                try:
                    return model.objects.get(id=json[linkName])
                except:
                    self.errors.append("Object %s of type %s does not exist from %s %s" % (json[linkName], model, self, self.id))
                    return None
        return field

    def _safeGetProperty(self, json, valueName, default=None):
        if valueName in json:
            return json[valueName]
        return default


    def getErrors(self):
        return self.errors

    def clearErrors(self):
        self.errors = []

    class Meta:
        abstract = True
        
        
'''
Meta data associated with the content, this should be used where a low cost index is required, note no json in this
object.
'''
class ContentMeta(ContentModel):
    PUBLICATION_STATUS = (
                           ('U','Unpublished'),
                           ('P','Published'))
    status = models.CharField(max_length=1, choices=PUBLICATION_STATUS)
    published = models.DateTimeField(auto_now=True)
    thumbnail = models.CharField(max_length=255, null=True)
    short_title = models.CharField(max_length=255, null=True)
    short_text = models.CharField(max_length=1024, null=True)
    priority = models.CharField(max_length=1, default="x")
        
    class Meta:
        ordering = ["priority"]


'''
Extends ContentMeta to include the data
'''
class Content(ContentMeta):
    data = models.TextField()


    @staticmethod
    def getKeyFromJson(dictModel):
        if 'id' in dictModel:
            return dictModel['id']
        return None
    
    @staticmethod
    def createFromJson(data, key):
        dataKey = Content.getKeyFromJson(data)
        if dataKey is None:
            dataKey = key
        return Content.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))

    @staticmethod
    def safe_to_json(obj):
        if obj:
            return obj.to_json()
        return None

    def to_json(self):
        return json.loads(self.data)
    
    def buildRelationships(self):
        json = self.to_json()
        self.thumbnail = self._safeGetProperty(json,"thumbnail")
        self.short_title = self._safeGetProperty(json,"short_title")
        self.short_text = self._safeGetProperty(json,"short_text")
        self.priority = self._safeGetProperty(json,"priority")
    
    class Meta:
        ordering = ["published"]
        
        
class ContentMetaAdmin(admin.ModelAdmin):
    search_fields = ('short_title','short_text')
    list_display = ('id', 'short_title', 'key', 'published', 'status')
    list_filter = ('published', 'status','priority')

class ContentAdmin(admin.ModelAdmin):
    search_fields = ('short_title','short_text')
    list_display = ('id', 'short_title', 'key', 'published', 'status')
    list_filter = ('published', 'status','priority')



admin.site.register(Content, ContentAdmin)
admin.site.register(ContentMeta, ContentMetaAdmin)

