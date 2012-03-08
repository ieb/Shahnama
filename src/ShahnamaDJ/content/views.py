'''
Created on Jan 10, 2012

@author: ieb
'''
from ShahnamaDJ.content.models import Content, ContentMeta
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponseNotFound, \
    HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.template.context import RequestContext
from django.conf import settings
import json
from django.utils.http import urlquote, urlquote_plus, urlencode
import Image
import os
import shutil
import logging

MEDIA_URL, MEDIA_ROOT = (settings.MEDIA_URL, settings.MEDIA_ROOT)

class AbstractContentView(object):
    
    model = None
    id = None
    request = None
    json = None

    
    def __init__(self, request, id=None, model=None):
        self.request = request
        if model is not None:
            self.model = model
        elif id is not None:
            self.id = id
        
            
    def loadModel(self):
        None
            
    def loadJson(self):
        if self.json is None:
            self.loadModel()
            self.json = Content.safe_to_json(self.model)
            
    def makeJsonSafe(self):
        if self.json is None:
            self.json = {}

    def buildContext(self, data, extra = None):
        x = data
        if extra is not None:
            x.update(extra)
        if 'debug' in self.request.REQUEST:
            x.update({'debug' : 1})
        return x

    def buildEditContext(self, data, extra=None):
        x = RequestContext(self.request)
        x.update(data)
        x.update({'postaction' : '#'})
        if extra is not None:
            x.update(extra)
        if 'debug' in self.request.REQUEST:
            x.update({'debug' : 1})
            
        return x

    def safeUpdateField(self, field, requestField = None):
        if requestField is None:
            requestField = field
        if requestField in self.request.POST and self.request.POST[requestField] is not None:
            self.json[field] = self.request.POST[requestField]
            
    def safeGetProperty(self, field, default = None):
        if self.json is None or field not in self.json or self.json[field] is None:
            return default
        return self.json[field]
        
    def saveJson(self):
        self.model.data = json.dumps(self.json)

    class Meta:
        abstract = True


class PageView(AbstractContentView):
    
    def render(self):
        return render_to_response("content.djt.html", self.buildContext(self.summary()))

    def renderEdit(self):
        return render_to_response("edit-content.djt.html", self.buildEditContext(self.summary(editmode=True),{ 'uphere' : "%s_" % urlquote(self.id) }))
    
    def update(self, onsave):
        self.loadModel()
        if self.model is None:
            self.model = Content(id=self.id)
        self.loadJson()
        self.safeUpdateField('title')
        self.safeUpdateField('about')
        self.safeUpdateField('text')
        self.safeUpdateField('image')
        self.safeUpdateField('thumbnail')
        self.safeUpdateField('short_title', 'short-title')
        self.safeUpdateField('short_text', 'short-text')
        self.saveJson();
        self.model.buildRelationships()
        self.model.save()
        return redirect(onsave, self.model.id)

    def updateTrimImage(self, requestImageType):
        self.loadModel()
        if self.model is None:
            self.model = Content(id=self.id)
        self.loadJson()
        
        imageType =  self._getImageType(requestImageType)
        type = "%s_trim" % imageType
        imageTrimInfo = {}
        if os.path.isfile(self._getImageFile(imageType)):
            if type in self.json and self.json[type] is not None:
                imageTrimInfo = self.json[type]
            for f in ( 'x1','y1','x2','y2'):
                if f in self.request.POST and self.request.POST[f] is not None:
                    imageTrimInfo[f] = self.request.POST[f]                    
            self.json[type] = imageTrimInfo
            self.json[imageType] = self._getImageUrl(imageType)
            self.saveJson()
            self.model.save()
            self._trimImage(imageType, imageTrimInfo)
            return HttpResponse("{'result':'ok'}",status=200,content_type="application/json;charset=utf8")
        return HttpResponse("{'result':'no file to crop'}",status=400,content_type="application/json;charset=utf8")


    def viewFramedImage(self, imageType):
        return render_to_response("img-framed.djt.html", 
                                  self.buildEditContext(
                                                        self.summary(editmode=True),
                                                        { 'imagebase' : MEDIA_URL, 
                                                         'img' : self._getImageUrl(self._getImageType(imageType))}))
    
    def viewTrimImageJson(self, imageType):
        self.loadJson()
        type = "%s_trim" % self._getImageType(imageType)
        imageTrimInfo = {}
        
        if type in self.json and self.json[type] is not None:
            imageTrimInfo = self.json[type]
        return HttpResponse(json.dumps(imageTrimInfo), status=200, content_type="application/json;charset=utf8")
    
    def _getImageType(self, imageType):
        if imageType.startswith("thumbnail-"):
            return "thumbnail"
        return "image"
    
    def _getImageFile(self,imageType, croped = False, id = None):
        if id is None:
            id = self.id
        if croped:
            f = "%s%s_%s_croped.jpg" % (MEDIA_ROOT,id,imageType)
        else:
            f = "%s%s_%s.jpg" % (MEDIA_ROOT,id,imageType)
        return f
    
    def _getImageUrl(self,imageType,cropped=False, id = None, nocheck = False):
        if id is None:
            id = self.id
        if cropped:
            f = self._getImageFile(imageType, cropped, id = id)
            if nocheck or os.path.isfile(f):
                return "%s%s_%s_croped.jpg" % ( MEDIA_URL, id, imageType  )
        f = self._getImageFile(imageType, id = id)
        if nocheck or os.path.isfile(f):
            return "%s%s_%s.jpg" % ( MEDIA_URL, id, imageType  )
        return False

    def _getImageUrls(self, id = None, nocheck = False):
        if id is None:
            id = self.id
        return {
            'main' : self._getImageUrl("image", id=id, nocheck=nocheck),
            'main_crop' : self._getImageUrl("image",id=id, cropped=True, nocheck=nocheck),
            'thumbnail' : self._getImageUrl("thumbnail", id=id, nocheck=nocheck),
            'thumbnail_crop' : self._getImageUrl("thumbnail", id=id,cropped=True, nocheck=nocheck),
            }

    def _trimImage(self, imageType, imageTrimInfo):
        f = self._getImageFile(imageType)
        croped = self._getImageFile(imageType,True)
        if os.path.isfile(croped):
            os.remove(croped)
        if os.path.isfile(f):
            shutil.copy(f, croped)
            if imageTrimInfo is not None:
                try:
                    im = Image.open(f)
                    im = im.crop((int(imageTrimInfo['x1']),int(imageTrimInfo['y1']),int(imageTrimInfo['x2']),int(imageTrimInfo['y2'])))
                    im.save(self._getImageFile(imageType,True))
                except Exception as e:
                    logging.getLogger(__name__).exception(
                            "Trim Image %s failed" % (f))
                    return False
        return True

    
    
    def updateImage(self, requestImageType, onsave):
        if self.request.FILES is not None and "file" in self.request.FILES:
            self.loadJson()
            f = self.request.FILES['file']
            imageType = self._getImageType(requestImageType)
            targetFile = self._getImageFile(imageType)
            destination = open(targetFile, 'wb+')
            for chunk in f.chunks():
                destination.write(chunk)
            destination.close()
            trimInfoName = "%s_trim" % imageType
            imageTrimInfo = None
            if self.json is not None and trimInfoName in self.json and self.json[trimInfoName] is not None:
                imageTrimInfo = self.json[trimInfoName]
            self._trimImage(imageType, imageTrimInfo)               
        return redirect(onsave, self.id, requestImageType)
    
    def getPages(self):
        pages = []
        for content in ContentMeta.objects.all():
            pages.append({ 'meta' : content, 'pageimages' : self._getImageUrls(id=content.id)})
        return { 'pages' : pages }
        
    
    def summary(self, editmode=False):
        self.loadJson()
        summary = self.getPages()
        if self.json is None:
            return summary
        page = { 'id' : self.model.id }
        page.update(self.json)
        summary['page'] = page
        summary['pageimages'] = self._getImageUrls(nocheck=editmode)
        return summary
    
    def loadModel(self):
        if self.model is None:
            self.model = Content.objects.get(id=self.id)
        

class PageListView(AbstractContentView):
    
    def render(self):
        return render_to_response("contentlist.djt.html", self.buildContext(self.summary()))
    
    def summary(self):
        pages = []
        for content in ContentMeta.objects.all():
            pages.append(content)
        return { 'pages' : pages }
    
class HomeView(AbstractContentView):
    def loadObject(self):
        None
        
    def render(self):
        return render_to_response("front.djt.html", self.buildContext(PageView(self.request).getPages()))

    
def pageView(request, id):
    pageView = PageView(request,id=id)
    pageView.loadJson()
    if pageView.model is None:
        if request.user.has_perm("content.createpage") :
            return pageView.createPage()  
        return HttpResponseNotFound()
    return pageView.render()

@login_required
@permission_required("content.pageedit")
def pageEdit(request, id, onsave=None):
    pageView = PageView(request,id=id)
    if "POST" == request.method:
        return pageView.update(onsave)
    else:
        pageView.loadJson()
        if pageView.model is None:
            if request.user.has_perm("content.createpage") :
                return pageView.createPage()  
            return HttpResponseNotFound()
        return pageView.renderEdit()

@login_required
@permission_required("content.createpage")
def pageCreate(request, id, onsave=None):
    pageView = PageView(request,id=id)
    if "POST" == request.method:
        return pageView.update(onsave)
    else:
        pageView.loadJson()
        if pageView.model is None:
            return pageView.renderEdit()
        return HttpResponseBadRequest()
    

@login_required
@permission_required("content.pageview")
def pageListView(request):
    return PageListView(request).render()


@login_required
@permission_required("content.imageupload")
def pageFramedImageView(request, id, imageType, onsave=None):
    pageView = PageView(request, id=id)
    if "POST" == request.method:
        return pageView.updateImage(imageType, onsave) 
    else:
        return pageView.viewFramedImage(imageType)

@login_required
@permission_required("content.imageupload")
def pageTrimImageView(request, id, imageType):        
    pageView = PageView(request, id=id)
    if "POST" == request.method:
        return pageView.updateTrimImage(imageType)
    else:
        return pageView.viewTrimImageJson(imageType)

def homeView(request):
        return HomeView(request).render()
