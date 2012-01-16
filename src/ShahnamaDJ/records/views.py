# Create your views here.

from django.shortcuts import render_to_response
from ShahnamaDJ.records.models import Chapter, JsonModel, Country, Illustration,\
    Authority, Location, Manuscript, Scene, Reference
import re
import collections
from ShahnamaDJ.datatypes.gregorian import Gregorian
from ShahnamaDJ.datatypes.hijri import Hijri
from ShahnamaDJ.views import recordutils
from ShahnamaDJ.views.recordutils import format_date, wash_notes
from ShahnamaDJ.views.stringbuilder import StringPattern
from ShahnamaDJ.settings import PAINTINGS_URL, SERVER_ROOT_URL
from django.template.context import RequestContext
import json


state_tmpl = StringPattern('ms-state.stb')
text_tmpl = StringPattern('ms-text.stb')
origin_tmpl = StringPattern('ms-origin.stb')
pages_tmpl = StringPattern('ms-pages.stb')
form_tmpl = StringPattern('ill-form.stb')
painter_tmpl = StringPattern('ill-painter.stb')
folio_tmpl = StringPattern('ill-folio.stb')
contact_tmpl = StringPattern('loc-contact.stb')
address_tmpl = StringPattern('loc-address.stb')




class GalleryView(object):
    galleryData = []
    
    @staticmethod
    def entry(image,url,title,index,text,id,decoration = False):
        return {
            'image': image,
            'url': url,
            'title': title,
            'index': index,
            'text': text,
            'id': id,
            'decoration': decoration
        }
    
    def emit(self):
        return {
            'main': [x for x in sorted(self.galleryData,key = lambda x: x['id']) if not x['decoration']],
            'decorated': sorted(self.galleryData,key = lambda x: x['id'])
        }
    

class AbstractView(object):
    
    model = None
    id = None
    request = None
    json = None
    summaryMap = None

    
    def __init__(self, request, id=None, model=None):
        self.request = request
        if model is not None:
            self.model = model
            self.id = model.id
        elif id is not None:
            self.id = id
            
    def loadModel(self):
        None
            
    def loadJson(self):
        if self.json is None:
            if self.model is None:
                self.loadModel()
            self.json = JsonModel.safe_to_json(self.model)
            
    def makeJsonSafe(self):
        if self.json is None:
            self.json = {}

    def buildContext(self, data):
        x = data
        if 'debug' in self.request.REQUEST:
            x.update({'debug' : 1})
        return x
    
    def getSafeProperty(self, name, default=''):
        self.loadJson()
        if name in self.json and self.json[name] is not None:
            return self.json[name]
        return default

    class Meta:
        abstract = True
    

re_code = re.compile(r"(-?[0-9]+)(.*)")
    
class ChapterView(AbstractView):
    
    def loadModel(self):
        if self.model is None:
            return Chapter.objects.get(id=self.id)

            
    def render(self):
        return render_to_response("chapter.djt.html", self.buildContext(self.summary()))
    
    def summary(self,quick = False):
        if self.summaryMap is None:
            allChapters = Chapter.objects.all()
            chapters = []
            gallery = GalleryView()
            for chapter in allChapters:
                
                chapterJson = JsonModel.safe_to_json(chapter)
                code = chapterJson['ChapterCode'].strip()
                chapters.append({
                    'name': chapterJson['ChapterName'],
                    'code': code,
                    'url': "%s/chapter/%s" % (SERVER_ROOT_URL, chapter.id)
                })
                if self.id is not None and str(self.id) == str(chapter.id):
                    gallery.galleryData = [ SceneView(self.request, model = x ).gallery() for x in chapter.scene_set.all()]
                
            extra = {
                     # this sort should be done in the query above
                'chapters': sorted(chapters,key = lambda x: self._order(x['code'])),
                'gallery': gallery.emit(),
            }
            self.summaryMap = dict(extra.items())
        return self.summaryMap

    def _order(self,s):
        m = re_code.match(s)
        if m:
            return (1,int(m.group(1)),m.group(2))
        else:
            return (0,'',s)
    
    def gallery(self):
        None
    
    
    
re_az = re.compile(r"^[a-z].*$")
class CountryView(AbstractView):

    def render(self):
        return render_to_response("country.djt.html", self.buildContext(self.summary()))
    
    def summary(self, quick = False):
        if self.summaryMap is None:
            countries = Country.objects.all()
            if countries:
                countriesMap = collections.defaultdict(list)
                gallery = GalleryView()
                for country in countries:
                    name = country.name
                    if re_az.match(name.lower()):
                        hkey = name.lower()[0]
                    else:
                        hkey = "Other"
                    if self.id is not None and str(self.id) == str(country.id):
                        gallery.galleryData = [LocationView(self.request, model = x).gallery("FullLocationName") for x in country.location_set.all()]
                    countriesMap[hkey].append({
                        'name': name,
                        'url': "%s/country/%s" % (SERVER_ROOT_URL,country.id)
                    })
                extra = {
                    'countries': sorted([{'head': k.upper(), 'body': v} for (k,v) in countriesMap.iteritems()],key = lambda x: (x['head'] == 'Other',x['head'])),
                    'gallery': gallery.emit(),
                }
                self.summaryMap = dict(extra.items())
            else:
                self.summaryMap = {}
        return self.summaryMap
    
    def gallery(self):
        None

class AuthorityView(AbstractView):
    
    name = None
    
    def __init__(self, request, name, id):
        self.name = name
        self.id = id
    
    def loadModel(self):
        if self.model is None:
            self.model = Authority.objects.get(name=self.name, id=self.id)
            
    def loadJson(self):
        if self.json is None:
            self.loadModel()
            self.json = JsonModel.safe_to_json(self.model)
            
    def json(self):
        self.loadJson()
        return self.json;

class IllustrationView(AbstractView):
    
    
    def render(self):
        return render_to_response("illustration.djt.html", self.buildContext(self.summary()))
    
    def loadModel(self):
        if self.model is None:
            self.model = Illustration.objects.get(id = self.id)
            
    
    def summary(self, quick = False):
        self.loadJson()
        if self.summaryMap is None:
            self.loadJson()
            if self.json:
                refmap = {
                    'GeneralReferences1': 'General',
                    'GeneralReferences2': 'General',
                    'GeneralReferences3': 'General',
                    'AttributionPainter': 'Painter',
                    'AttributionStyle': 'Style',
                    'AttributionDate': 'Date',
                }
                chapter = ChapterView(self.request, model=self.model.chapter)
                extra = {
                    'painting_url': self.painting(),
                    'url': "%s/illustration/%s" % (SERVER_ROOT_URL,self.id),
                    'form': form_tmpl.apply(self.request,self.json),
                    'work': AuthorityView('ms-title', self.getSafeProperty('TitleSerial')).json(),
                    'chapter': chapter.json(),
                    'chapter-k': AuthorityView('chapter-k', self.getSafeProperty('ChapterSerialK')).json(),
                    'chapter-b': AuthorityView('chapter-b', self.getSafeProperty('ChapterSerialB')).json(),
                    'chapter-ds': AuthorityView('chapter-ds', self.getSafeProperty('ChapterSerialDS')).json(),
                    'date': "%s (%s)" % (Hijri.date(self.getSafeProperty('HijriDate')),Gregorian.date(self.getSafeProperty('GregorianDate'))),
                    'status': AuthorityView('record-status', self.getSafeProperty('CompletionStatus')).json(),
                    'up_date': recordutils.format_date(self.getSafeProperty('DateUpdated')),
                    'painter': painter_tmpl.apply(self.request,self.json),
                    'references': ReferenceView.refs_tmpl(self.request,self.json,refmap),
                    'notes': recordutils.wash_notes(self.getSafeProperty('NotesVisible')),
                    'folio': folio_tmpl.apply(self.request,self.json),
                    'format': AuthorityView('ill-format', self.getSafeProperty('FormatSerial')).json(),
                    'prev-url': "%s/illustration/%s" % (SERVER_ROOT_URL,self.json['chain-prev-folios-in-ms']) if self.json['chain-prev-folios-in-ms'] else '',
                    'next-url': "%s/illustration/%s" % (SERVER_ROOT_URL,self.json['chain-next-folios-in-ms']) if self.json['chain-next-folios-in-ms'] else '',
                }
                if not quick:
                    manuscript = ManuscriptView(self.request, model=self.model.manuscript)
                    location = LocationView(self.request, self.model.manuscript.location)
                    scene = SceneView(self.request, self.model.scene)
                    extra['ms_name'] = manuscript.summary()['AccessionNumber']
                    extra['ms_url'] = "%s/manuscript/%s" % (SERVER_ROOT_URL,manuscript.summary()['ManuscriptSerial'])
                    extra['loc_name'] = location.summary()['FullLocationName']
                    extra['loc_url'] = "%s/location/%s" % (SERVER_ROOT_URL,location.summary()['LocationSerial'])
                    extra['loc_city'] = location.summary()['City']
                    extra['cou_name'] = location.summary()['country']
                    extra['cou_url'] = "%s/country/%s" % (SERVER_ROOT_URL,location.summary()['Country'])
                    extra['sc_name'] = scene.summary()['EnglishTitle']
                    extra['sc_url'] = "%s/scene/%s" % (SERVER_ROOT_URL,scene.summary()['SceneSerial'])
                    extra['ch_name'] = scene.summary()['chapter_name']
                    extra['ch_url'] = scene.summary()['chapter_url']
                self.summaryMap = dict(self.json.items() + extra.items())
            else:
                self.summaryMap = {}
        return self.summaryMap
    
    def gallery(self,key=None):
        self.loadJson()
        return GalleryView.entry(self.painting(),
                                 self.getSafeProperty('url'),
                                 self.getSafeProperty('TitleEnglish'),
                                 self.getSafeProperty('FolioNumber'),
                                 ManuscriptView(self.request,model=self.model.manuscript)._text(),
                                 self.getSafeProperty(key))
        

    
    def painting(self):
        self.loadJson()
        pbase = PAINTINGS_URL
        if 'Painting' in self.json and self.json['Painting'] is not None:
            return "%s/Painting/%s.jpg" % (pbase,self.json['Painting'])
        else:
            return ''
    
    



class LocationView(AbstractView):
    
    cannon_image = None
    
    def render(self):
        return render_to_response("location.djt.html", self.buildContext(self.summary()))
    
    def loadModel(self):
        if self.model is None:
            self.model = Location.objects.get(id = self.id)

        
        
        
    def summary(self, quick = False):
        if self.summaryMap is None:
            self.loadJson()
            if self.json:
                photo = ''
                pbase = PAINTINGS_URL
                if self.json and 'Image' in self.json and self.json['Image'] is not None:
                    photo = "%s/Location/%s.jpg" % (pbase,self.json['Image'])
                gallery = GalleryView()
                if not quick:
                    gallery.galleryData = [GalleryView.entry(photo,'#',self.getSafeProperty('FullLocationName'),'View of location, go forward for manuscripts','','',True)]
                    gallery.galleryData.extend([ ManuscriptView(self.request, x) for x in self.model.manuscripts])
                extra = {
                     'country': AuthorityView('country', self.getSafeProperty('Country')).json(),
                     'gallery': gallery.emit(),
                     'up_date': format_date(self.getSafeProperty('DateUpdated')),
                     'contact': contact_tmpl.apply(self.request,self.locationJson),
                     'address': address_tmpl.apply(self.request,self.flocationJson),
                     'notes': wash_notes(self.getSafeProperty('NotesVisible')),
                }
                self.summaryMap = dict(self.json().items() + extra.items())
            else:
                self.summaryMap = {}
        return self.summaryMap
    
    def text(self):
        try:
            self.loadJson()
            return "%s, %s" % (self.getSafeProperty('FullLocationName'),self.getSafeProperty('City'))
        except:
            return "-missing-"
    
    def gallery(self, key=None):
        try:
            self.loadJson()
            return GalleryView.entry(self._canon_image(),
                                "%s/location/%s" % (SERVER_ROOT_URL,self.model.id),
                                "%s, %s" % (self.getSafeProperty('FullLocationName'), self.getSafeProperty('City')),
                                '',
                                '',
                                self.getSafeProperty(key))
        except:
            return GalleryView.entry(self._canon_image(),
                                "%s/location/%s" % (SERVER_ROOT_URL,self.id),
                                "--missing--",
                                '',
                                '',
                                self.getSafeProperty(key))
        
        
    def _canon_image(self):
        if self.cannon_image is None:
            try:
                self.loadJson()
                pbase = PAINTINGS_URL
                self.cannon_image = ''
                if 'Image' in self.json and self.json['Image'] is not None:
                    self.cannon_image = "%s/Location/%s.jpg" % (pbase,self.json['Image'])
                    return self.cannon_image
                for manuscript in self.model.manuscript_set.all():
                    ms = ManuscriptView(self.request, model=manuscript).gallery('AccessionNumber')
                    if 'image' in ms and ms['image'] is not None:
                        self.cannon_image = ms['image']
                        return self.cannon_image
            except:
                return None
        return self.cannon_image



class ManuscriptView(AbstractView):
    
    canon_image = None
    
    def render(self):
        return render_to_response("manuscript.djt.html", self.buildContext(self.summary()))
    
    def loadModel(self):
        if self.model is None:
            self.model = Manuscript.objects.get(id = self.id)


    
    def _image_url(self, type):
        try:
            self.loadJson()
            pbase = PAINTINGS_URL
            return "%s/%s/%s.jpg" % (pbase, type, self.getSafeProperty(type))
        except:
            return None
    
    def _size_expr(self, pw, ph, tw, th):
        out = []
        if ph or pw:
            if not ph: ph = ''
            if not pw: pw = ''        
            out.append("page %s x %s mm" % (str(pw), str(ph)))
        if th or tw:
            if not th: th = ''
            if not tw: tw = ''        
            out.append("text %s x %s mm" % (str(tw), str(th)))
        return ", ".join(out)
    

    def _canon_image(self):
        if self.canon_image is None:
            try:
                self.loadJson()
                self.canon_image = ''
                for type in ('Colophon','SamplePage'):
                    if type in self.json and self.json[type] is not None:
                        self.canon_image = self._image_url(type)
                        return self.canon_image
                for illustration in self.model.illustration_set.all():
                    p = IllustrationView(self.request, model=illustration).painting()
                    if p is not None:
                        self.canon_image = p
                        break
            except:
                return None
        return self.canon_image
    
        
    def summary(self, quick=False):
        if self.summaryMap is None:
            try:
                self.loadJson()
                if self.json:
                    # references
                    refmap = {
                        'GeneralRef1': 'General',
                        'GeneralRef2': 'General',
                        'GeneralRef3': 'General',
                        'IllustrationReference': 'Illustrations',
                        'AttributionEstimate': 'Folio count',
                        'AttributionOrigin': 'Origin',
                        'AttributionDate': 'Date',
                    }
                    gallery = GalleryView()
                    locationView = LocationView(self.request, self.model.location)
                    loc = { 'Country': '', 'country': '' }
                    if not quick:
                        if 'Colophon' in self.json  and self.json['Colophon'] is not None:
                            gallery.galleryData.append(GalleryView.entry(self._image_url(self.request, self.json, 'Colophon'), '#', 'Colophon', self.json['ColophonNumber'], '', ''))
                        if 'SamplePage' in self.json and self.json['SamplePage'] is not None:
                            gallery.galleryData.append(GalleryView.entry(self._image_url(self.request, self.json, 'SamplePage'), '#', 'Sample page from this manuscript', '', '', ''))
                        gallery.extend([ IllustrationView(self.request, model=x) for x in self.model.illustration_set.all()])
                        loc = locationView.summary(True)
                    extra = {
                        'gallery': gallery.emit(),
                        'size': self._size_expr(self.getSafeProperty('PageWidth'), self.getSafeProperty('PageLength'), self.getSafeProperty('TextWidth'), self.getSafeProperty('TextLength')),
                        'text': text_tmpl.apply(self.request, self.json),
                        'pages': pages_tmpl.apply(self.request, self.json),
                        'state': state_tmpl.apply(self.request, self.json),
                        'origin': origin_tmpl.apply(self.frequest, self.json),
                        'date': "%s (%s)" % (Hijri.date(self.getSafeProperty('HijriDate')), Gregorian.date(self.getSafeProperty('GregorianDate'))),
                        'references': ReferenceView.refs_tmpl(self.request, self.json, refmap),
                        'notes': wash_notes(self.getSafeProperty('NotesVisible')),
                        'status': JsonModel.safe_to_json(Authority.objects.get(name='record-status', id=self.getSafeProperty('CompletionStatus'))),
                        'up_date': format_date(self.getSafeProperty('DateUpdated')),
                        'canon-image': self._canon_image(self.request, self.json),
                        'location_text': locationView.text(),
                        'location_url': '%s/location/%s' % (SERVER_ROOT_URL, self.getSafeProperty('LocationSerial')),
                        'country': loc['country'],
                        'country_url': '%s/country/%s' % (SERVER_ROOT_URL, loc['Country']),
                        'prev-url': "%s/manuscript/%s" % (SERVER_ROOT_URL, self.json['chain-prev-date']) if self.json['chain-prev-date'] else '',
                        'next-url': "%s/manuscript/%s" % (SERVER_ROOT_URL, self.json['chain-next-date']) if self.json['chain-next-date'] else '',
                    }
                    self.summaryMap = dict(self.json.items() + extra.items())
                else:
                    self.summaryMap = {}
            except:
                self.summaryMap = {}
        return self.summaryMap
    
    def gallery(self, key=None):
        try:
            self.loadJson()
            return GalleryView.entry(self._canon_image(),
                                     "%s/manuscript/%s" % (SERVER_ROOT_URL,self.model.id),
                                     self.getSafeProperty('AccessionNumber'),'',self._text(),self.getSafeProperty(key))
        except:
            return GalleryView.entry(self._canon_image(),
                                     "%s/manuscript/%s" % (SERVER_ROOT_URL,self.id),
                                     '--missing--','',self._text(),self.getSafeProperty(key))
    
    def _text(self):
        try:
            self.loadJson()
            loc = LocationView(self.request, model=self.model.location).text()
            return "%s, %s" % (self.getSafeProperty('AccessionNumber'),loc)
        except:
            return "--missing--"

        
        


class SceneView(AbstractView):
    
    canon_image = None
    
    def render(self):
        return render_to_response("scene.djt.html", self.buildContext(self.summary()))
    
    def loadModel(self):
        if self.model is None:
            self.model = Scene.objects.get(id = self.id)
    
    def summary(self, quick = False):
        if self.summaryMap is None:
            try:
                self.loadJson()
                if self.json is not None:
                    refmap = {
                        'GeneralRef1': 'General',
                        'GeneralRef2': 'General',
                        'GeneralRef3': 'General',
                    }
                    gallery = GalleryView()
                    if not quick:
                        gallery.galleryData = [ IllustrationView(self.request, model = x).gallery() for x in self.model.illustration_set.all()]
                    chapter = ChapterView(self.request, model=self.model.chapter)
                    extra = {
                        'gallery': gallery.emit(),
                        'up_date': format_date(self.getSafeProperty('DateUpdated')),
                        'references': ReferenceView.refs_tmpl(self.request,self.json,refmap),
                        'notes': wash_notes(self.getSafeProperty('NotesVisible')),
                        'chapter_name': chapter.getSafeProperty('ChapterName'),
                        'chapter_url': "%s/chapter/%s" % (SERVER_ROOT_URL,chapter.getSafeProperty('ChapterSerial'))
                    }
                    self.summaryMap = dict(self.json.items() + extra.items())
                    self.summaryMap.update({ 'record' : self.json})
                else:
                    self.summaryMap = {'summary' : 'isempty', 'view' : self.model, 'id': self.id}
            except:
                self.summaryMap = {'summary' : 'isempty', 'view' : self.model, 'id': self.id}
        return self.summaryMap;
    
    def gallery(self, key=None):
        try:
            self.loadJson()
            return GalleryView.entry(self._canon_image(),
                                     "%s/scene/%s" % (SERVER_ROOT_URL,self.model.id),
                                     '',self.getSafeProperty('EnglishTitle'),'',self.getSafeProperty(key))
        except:
            return GalleryView.entry(self._canon_image(),
                                     "%s/scene/%s" % (SERVER_ROOT_URL,self.id),
                                     '',"--missing--",'',self.getSafeProperty(key))
    def _canon_image(self):
        if self.canon_image is None:
            try:
                self.loadJson()
                for type in ('Colophon','SamplePage'):
                    if type in self.json and self.json[type] is not None:
                        return self._image_url(type)
                self.canon_image= ''
                for illustration in self.model.illustration_set.all():
                    p = IllustrationView(self.request, model = illustration).gallery("FolioNumber")
                    if p['image'] is not None:
                        self.canon_image = p['image']
                        break;
            except:
                return None
        return self.canon_image


class ReferenceView(AbstractView):
    
    def loadModel(self):
        if self.model is None:
            self.model = Reference.objects.get(id = self.id)

    def sentence_summary(self):
        try:
            self.loadJson()
            self.json['bib-class'] = AuthorityView('bib-class', self.json['biblioClassificationID']).json()
            return citation_tmpl.apply(self.request,self.json)
        except:
            return citation_tmpl.apply(self.request,{})

    @staticmethod
    def refs_tmpl(request,data, refmap):
        refs = {}
        for (name,title) in refmap.iteritems():
            if data[name] is not None and str(data[name]).strip() != '':
                if not data[name] in refs:
                    refs[data[name]] = set()
                refs[data[name]].add(title)
        refs_tmpl = []
        for (ref,kd) in refs.iteritems():
            title = recordutils.comma_ampersand_list(sorted(kd))
            value = ReferenceView(request,id=ref).sentence_summary()
            refs_tmpl.append({'key': title, 'value': value})
        refs_tmpl.sort(key=lambda x: recordutils._general_first(x['key']))
        for i in range(len(refs_tmpl)-1,0,-1):
            if refs_tmpl[i-1]['key'] == refs_tmpl[i]['key']:
                refs_tmpl[i]['key'] = ''
        return refs_tmpl

citation_tmpl = StringPattern('citation.stb')


    
    
def locationView(request, id):
    return LocationView(request, id = id).render()

def illustrationView(request, id):
    return IllustrationView(request, id = id).render()

def countryView(request, id):
    countryView = CountryView(request, id=id)
    return countryView.render()

def manuscriptView(request, id):
        return ManuscriptView(request, id = id).render()

def sceneView(request, id):
        return SceneView(request, id = id).render()

def chapterView(request, id):
        chapterView = ChapterView(request, id=id)
        return chapterView.render()

    
