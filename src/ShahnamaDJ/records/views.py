# Create your views here.

from django.shortcuts import render_to_response
from django.conf import settings
from ShahnamaDJ.records.models import Chapter, JsonModel, Country, Illustration,\
    Authority, Location, Manuscript, Scene, Reference
import re
import collections
from ShahnamaDJ.datatypes.gregorian import Gregorian
from ShahnamaDJ.datatypes.hijri import Hijri
from ShahnamaDJ.views import recordutils
from ShahnamaDJ.views.recordutils import format_date, wash_notes
from ShahnamaDJ.views.stringbuilder import StringPattern
import json
from ShahnamaDJ.content.models import ContentMeta
import logging
import traceback

MANUSCRIPT_URL, LOCATION_URL, ILLUSTRATION_URL, PAINTINGS_URL, SERVER_ROOT_URL = (
        settings.MANUSCRIPT_URL, 
        settings.LOCATION_URL,
        settings.ILLUSTRATION_URL, 
        settings.PAINTINGS_URL,
        settings.SERVER_ROOT_URL)

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
        pages = []
        for page in ContentMeta.objects.all():
            pages.append({ 'page_url' : "/page/%s" % page.key, 'about' : 'the %s ' % page.key })
            if ( len(pages) >= 3 ):
                break;
        x.update({"top_pages": pages})
        return x
    
    def getSafeProperty(self, name, default='', map = None):
        self.loadJson()
        if map is None:
            map = self.json
        try:
            return map[name]
        except:
            return default

    class Meta:
        abstract = True
    

re_code = re.compile(r"(-?[0-9]+)(.*)")
    
class ChapterView(AbstractView):
    
    def loadModel(self):
        if self.model is None and self.id is not None and self.id != '':
            self.model = Chapter.objects.get(id=self.id)


            
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
    
    def loadModel(self):
        if self.model is None and self.id is not None and self.id != '':
            try:
                self.model = Country.objects.get(id=self.id)
            except:
                logging.error("Failed to load country %s " % self.id)
  
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
    
    def getValue(self):
        v = self.getSafeProperty("value")
        return v

    def gallery(self):
        None

class AuthorityView(AbstractView):
    
    name = None
    
    def __init__(self, request, name, id):
        self.name = name
        self.id = id
    
    def loadModel(self):
        if self.model is None and self.id is not None and self.id != '':
            try:
                self.model = Authority.objects.get(name=self.name, key=self.id)
            except:
                logging.error(" Error Loaded Authority %s %s " % (self.name, self.id))
                self.model = None
            
    def loadJson(self):
        if self.json is None:
            self.loadModel()
            self.json = JsonModel.safe_to_json(self.model)
            
    def asJson(self):
        self.loadJson()
        return self.json;
    
    def getValue(self):
        return self.getSafeProperty("value")

class IllustrationView(AbstractView):
    
    
    def render(self):
        return render_to_response("illustration.djt.html", self.buildContext(self.summary()))
    
    def loadModel(self):
        if self.model is None and self.id is not None and self.id != '':
            self.model = Illustration.objects.get(id = self.id)
            
    
    def summary(self, quick = False):
        self.loadJson()
        if self.summaryMap is None:
            self.loadJson()
            if self.json is not None:
                refmap = {
                    'GeneralReferences1': 'General',
                    'GeneralReferences2': 'General',
                    'GeneralReferences3': 'General',
                    'AttributionPainter': 'Painter',
                    'AttributionStyle': 'Style',
                    'AttributionDate': 'Date',
                }
                extra = {
                    'painting_url': self.painting(),
                    'url': "%s/illustration/%s" % (SERVER_ROOT_URL,self.id),
                    'form': form_tmpl.apply(self.request,self.json),
                    'chapter' : {},
                    'work': AuthorityView(self.request, 'ms-title', self.getSafeProperty('TitleSerial')).getValue(),
                    'chapter-k': AuthorityView(self.request, 'chapter-k', self.getSafeProperty('ChapterSerialK')).getValue(),
                    'chapter-b': AuthorityView(self.request, 'chapter-b', self.getSafeProperty('ChapterSerialB')).getValue(),
                    'chapter-ds': AuthorityView(self.request, 'chapter-ds', self.getSafeProperty('ChapterSerialDS')).getValue(),
                    'date': "%s (%s)" % (Hijri.date(self.getSafeProperty('HijriDate')),Gregorian.date(self.getSafeProperty('GregorianDate'))),
                    'status': AuthorityView(self.request, 'record-status', self.getSafeProperty('CompletionStatus')).getValue(),
                    'up_date': recordutils.format_date(self.getSafeProperty('DateUpdated')),
                    'painter': painter_tmpl.apply(self.request,self.json),
                    'references': ReferenceView.refs_tmpl(self.request,self.json,refmap),
                    'notes': recordutils.wash_notes(self.getSafeProperty('NotesVisible')),
                    'folio': folio_tmpl.apply(self.request,self.json),
                    'format': AuthorityView(self.request, 'ill-format', self.getSafeProperty('FormatSerial')).getValue(),
                    'prev_url': "%s/illustration/%s" % (SERVER_ROOT_URL,self.json['chain-prev-folios-in-ms']) if 'chain-prev-folios-in-ms' in self.json else '',
                    'next_url': "%s/illustration/%s" % (SERVER_ROOT_URL,self.json['chain-next-folios-in-ms']) if 'chain-next-folios-in-ms' in self.json else '',
                }
                ''' 
                Illustration does not have a chapter serial,
                '''
                if self.model is not None and self.model.scene is not None and self.model.scene.chapter is not None:
                    chapterV = ChapterView(self.request, model=self.model.scene.chapter)
                    chapterV.loadJson()
                    extra.update({'chapter': chapterV.json})
                if not quick:
                    if self.model.manuscript is not None:
                        manuscript = ManuscriptView(self.request, model=self.model.manuscript)
                        location = LocationView(self.request, model=self.model.manuscript.location)
                        ls = location.summary()
                        logging.error("Location %s " % ls)
                        extra['ms_name'] = manuscript.getSafeProperty('AccessionNumber')
                        extra['ms_url'] = "%s/manuscript/%s" % (SERVER_ROOT_URL,manuscript.getSafeProperty('ManuscriptSerial'))
                        extra['loc_name'] = location.getSafeProperty('FullLocationName')
                        extra['loc_url'] = "%s/location/%s" % (SERVER_ROOT_URL,location.getSafeProperty('LocationSerial'))
                        extra['loc_city'] = location.getSafeProperty('City')
                        extra['cou_name'] = self.getSafeProperty('country', map = ls)
                        extra['cou_url'] = "%s/country/%s" % (SERVER_ROOT_URL,location.getSafeProperty('Country'))
                    if self.model.scene is not None:
                        scene = SceneView(self.request, model=self.model.scene)
                        ss = scene.summary()
                        extra['sc_name'] = scene.getSafeProperty('EnglishTitle')
                        extra['sc_url'] = "%s/scene/%s" % (SERVER_ROOT_URL,scene.getSafeProperty('SceneSerial'))
                        extra['ch_name'] = self.getSafeProperty('chapter_name', map = ss)
                        extra['ch_url'] = self.getSafeProperty('chapter_url', map = ss)
                self.summaryMap = dict(self.json.items() + extra.items())
                logging.error("Rendering form with %s " % json.dumps(self.summaryMap, indent=4))
            else:
                self.summaryMap = {}
        return self.summaryMap
    
    def gallery(self,key=None):
        self.loadJson()
        return GalleryView.entry(self.painting(),
                                 "%s/illustration/%s" % (SERVER_ROOT_URL,self.id),
                                 self.getSafeProperty('TitleEnglish'),
                                 self.getSafeProperty('FolioNumber'),
                                 ManuscriptView(self.request,model=self.model.manuscript)._text(),
                                 self.getSafeProperty(key))
        

    
    def painting(self):
        self.loadJson()
        if 'Painting' in self.json and self.json['Painting'] is not None:
            return "%s/%s.jpg" % (ILLUSTRATION_URL,self.json['Painting'])
        else:
            return ''
    
    



class LocationView(AbstractView):
    
    cannon_image = None
    
    def render(self):
        return render_to_response("location.djt.html", self.buildContext(self.summary()))
    
    def loadModel(self):
        if self.model is None and self.id is not None and self.id != '':
            self.model = Location.objects.get(id = self.id)

        
        
        
    def summary(self, quick = False):
        if self.summaryMap is None:
            self.loadJson()
            if self.json is not None:
                photo = ''
                if self.json is not None and 'Image' in self.json and self.json['Image'] is not None:
                    photo = "%s/%s.jpg" % (LOCATION_URL,self.json['Image'])
                gallery = GalleryView()
                if not quick:
                    gallery.galleryData = [GalleryView.entry(photo,'#',self.getSafeProperty('FullLocationName'),'View of location, go forward for manuscripts','','',True)]
                    gallery.galleryData.extend([ ManuscriptView(self.request, x).gallery() for x in self.model.manuscript_set.all()])
                extra = {
                     'country': CountryView(self.request, id=self.getSafeProperty('Country')).getValue(),
                     'gallery': gallery.emit(),
                     'up_date': format_date(self.getSafeProperty('DateUpdated')),
                     'contact': contact_tmpl.apply(self.request,self.json),
                     'address': address_tmpl.apply(self.request,self.json),
                     'notes': wash_notes(self.getSafeProperty('NotesVisible')),
                }
                self.summaryMap = dict(self.json.items() + extra.items())
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
                self.cannon_image = ''
                if 'Image' in self.json and self.json['Image'] is not None:
                    self.cannon_image = "%s/%s.jpg" % (LOCATION_URL,self.json['Image'])
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
        if self.model is None and self.id is not None and self.id != '':
            self.model = Manuscript.objects.get(id = self.id)


    
    def _image_url(self, type):
        try:
            self.loadJson()
            return "%s/%s/%s.jpg" % (MANUSCRIPT_URL, type, self.getSafeProperty(type))
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
                if self.json is not None:
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
                    locationView = LocationView(self.request, model=self.model.location)
                    loc = { 'Country': '', 'country': '' }
                    if not quick:
                        if 'Colophon' in self.json  and self.json['Colophon'] is not None:
                            gallery.galleryData.append(GalleryView.entry(self._image_url('Colophon'), '#', 'Colophon', self.json['ColophonNumber'], '', ''))
                        if 'SamplePage' in self.json and self.json['SamplePage'] is not None:
                            gallery.galleryData.append(GalleryView.entry(self._image_url('SamplePage'), '#', 'Sample page from this manuscript', '', '', ''))
                        gallery.galleryData.extend([ IllustrationView(self.request, model=x).gallery() for x in self.model.illustration_set.all()])
                        loc = locationView.summary(True)
                    extra = {
                        'gallery': gallery.emit(),
                        'size': self._size_expr(self.getSafeProperty('PageWidth'), self.getSafeProperty('PageLength'), self.getSafeProperty('TextWidth'), self.getSafeProperty('TextLength')),
                        'text': text_tmpl.apply(self.request, self.json),
                        'pages': pages_tmpl.apply(self.request, self.json),
                        'state': state_tmpl.apply(self.request, self.json),
                        'origin': origin_tmpl.apply(self.request, self.json),
                        'date': "%s (%s)" % (Hijri.date(self.getSafeProperty('HijriDate')), Gregorian.date(self.getSafeProperty('GregorianDate'))),
                        'references': ReferenceView.refs_tmpl(self.request, self.json, refmap),
                        'notes': wash_notes(self.getSafeProperty('NotesVisible')),
                        'status': AuthorityView(self.request, 'record-status', self.getSafeProperty('CompletionStatus')).getValue(),
                        'up_date': format_date(self.getSafeProperty('DateUpdated')),
                        'canon-image': self._canon_image(),
                        'location_text': locationView.text(),
                        'location_url': '%s/location/%s' % (SERVER_ROOT_URL, self.getSafeProperty('LocationSerial')),
                        'country': self.getSafeProperty('country', map = loc  ),
                        'country_url': '%s/country/%s' % (SERVER_ROOT_URL, locationView.getSafeProperty('Country')),
                        'prev_url': "%s/manuscript/%s" % (SERVER_ROOT_URL, self.json['chain-prev-date']) if 'chain-prev-date' in self.json else '',
                        'next_url': "%s/manuscript/%s" % (SERVER_ROOT_URL, self.json['chain-next-date']) if 'chain-next-date' in self.json else '',
                    }
                    self.summaryMap = dict(self.json.items() + extra.items())
                else:
                    self.summaryMap = {}
            except:
                logging.error("Failed to generate summary map %s " % traceback.format_exc())
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
                                     '--missing--','',self._text(),'')
    
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
        if self.model is None and self.id is not None and self.id != '':
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
        if self.model is None and self.id is not None and self.id != '':
            try:
                self.model = Reference.objects.get(id = self.id)
            except Reference.DoesNotExist:
                logging.error("No refernce with id %s " % self.id)

    def sentence_summary(self):
        try:
            self.loadJson()
            self.json['bib-class'] = AuthorityView(self.request, 'bib-class', self.json['biblioClassificationID']).getValue()
            return citation_tmpl.apply(self.request,self.json)
        except:
            logging.error(traceback.format_exc())
            logging.error("FAILED")
            return citation_tmpl.apply(self.request,{})

    @staticmethod
    def refs_tmpl(request,data, refmap):
        refs = {}
        for (name,title) in refmap.iteritems():
            try:
                if data[name] is not None and str(data[name]).strip() != '':
                    if not data[name] in refs:
                        refs[data[name]] = set()
                    refs[data[name]].add(title)
            except KeyError:
                logging.error("Missed %s " % name)
                pass
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

    
