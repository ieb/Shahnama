'''
Created on Jan 10, 2012

@author: ieb
'''
from ShahnamaDJ.content.models import Content, ContentMeta
from django.shortcuts import render_to_response
from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required, permission_required



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

    def buildContext(self, data):
        x = data
        print x
        return x

    class Meta:
        abstract = True


class PageView(AbstractContentView):
    
    def render(self):
        return render_to_response("content.djt.html", self.buildContext(self.summary()))
    
    def getPages(self):
        pages = []
        for content in ContentMeta.objects.all():
            pages.append(content)
        return { 'pages' : pages }
        
    
    def summary(self):
        self.loadJson()
        summary = self.getPages()
        if self.json is None:
            return summary
        summary['page'] = self.json
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
@permission_required("content.pageview")
def pageListView(request):
    return PageListView(request).render()


def homeView(request):
        return HomeView(request).render()
