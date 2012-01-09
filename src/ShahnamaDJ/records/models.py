from django.db import models
import json
# Create your models here.


class JsonModel(models.Model):
    id = models.AutoField(primary_key=True)
    key = models.TextField(max_length=32)
    data = models.TextField()
    
    def buildRelationships(self):
        None

    def to_json(self):
        return json.load(self.data)

    @staticmethod
    def safe_to_json(obj):
        if obj:
            return obj.to_json()
        return None
            
    
    class Meta:
        abstract = True
        
        
        
        
class Chapter(JsonModel):
    None

class Reference(JsonModel):
    None


class Country(JsonModel):
    name = models.CharField(max_length=64)
    class Meta:
        ordering = ['name']
    
class Location(JsonModel):    
    location = models.ForeignKey(Country,  blank=True, null=True, on_delete=models.SET_NULL)
    def buildRelationships(self):
        None
    

class Manuscript(JsonModel):
    name = models.CharField(max_length=64)
    location = models.ForeignKey(Location,  blank=True, null=True, on_delete=models.SET_NULL)
    class Meta:
        ordering = ['name']
    def buildRelationships(self):
        None


class Scene(JsonModel):
    chapter = models.ForeignKey(Chapter,  blank=True, null=True, on_delete=models.SET_NULL)
    def buildRelationships(self):
        None

class Illustration(JsonModel):
    chapter = models.ForeignKey(Chapter,  blank=True, null=True, on_delete=models.SET_NULL)
    manuscript = models.ForeignKey(Manuscript,  blank=True, null=True, on_delete=models.SET_NULL)
    scene = models.ForeignKey(Scene,  blank=True, null=True, on_delete=models.SET_NULL)
    def buildRelationships(self):
        
        None
    
class Authority(models.Model):
    name = models.CharField(max_length=16)
    key = models.CharField(max_length=64)
    
