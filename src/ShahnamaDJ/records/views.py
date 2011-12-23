# Create your views here.

from django.shortcuts import render_to_response
from ShahnamaDJ.records.models import Chapter, JsonModel, Country, Illustration,\
    Authority, Location, Manuscript, Scene, Reference
import re
import collections
from ShahnamaDJ.datatypes.gregorian import Gregorian
from ShahnamaDJ.datatypes.hijri import Hijri
from ShahnamaDJ.views import recordutils
from ShahnamaDJ.views.recordutils import format_date, wash_notes, refs_tmpl
from ShahnamaDJ.views.stringbuilder import StringPattern


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
    def entry(self, image,url,title,index,text,key,decoration = False):
        return {
            'image': image,
            'url': url,
            'title': title,
            'index': index,
            'text': text,
            'key': key,
            'decoration': decoration
        }
    
    def emit(self):
        return {
            'main': [x for x in sorted(self.galleryData,key = lambda x: x['key']) if not x['decoration']],
            'decorated': sorted(self.galleryData,key = lambda x: x['key'])
        }
    

class AbstractView(object):
    
    model = None
    key = None
    request = None
    json = None
    summary = None
    gallery = None

    
    def __init__(self, request, key=None, model=None):
        self.request = request
        if model is not None:
            self.model = model
        elif key is not None:
            self.key = key
            
    def loadModel(self):
        None
            
    def loadJson(self):
        if self.json is None:
            self.loadModel()
            self.json = JsonModel.safe_to_json(self.model)
            
    class Meta:
        abstract = True
    

re_code = re.compile(r"(-?[0-9]+)(.*)")
    
class ChapterView(AbstractView):
       
    def loadModel(self):
        return Chapter.objects.get(key=self.key)

            
    def render(self):
        return render_to_response("chapter.djt.html", self.summary())
    
    def summary(self,quick = False):
        if self.summary is None:
            allChapters = Chapter.objects.all()
            chapters = []
            gallery = GalleryView()
            for chapter in allChapters:
                
                chapterJson = JsonModel.safe_to_json(chapter)
                code = chapterJson['ChapterCode'].strip()
                chapters.append({
                    'name': chapterJson['ChapterName'],
                    'code': code,
                    'url': "%s/chapter/%s" % (self.request.server_root)
                })
                if self.key is not None and self.key == chapter.key:
                    gallery.galleryData = [ SceneView(self.request, model = x ).gallery() for x in chapter.scenes]
                
            extra = {
                     # this sort should be done in the query above
                'chapters': sorted(chapters,key = lambda x: self._order(x['code'])),
                'gallery': gallery.emit(),
            }
            self.summary = dict(extra.items())
        return self.summary

    def _order(self,s):
        m = re_code.match(s)
        if m:
            return (1,int(m.group(1)),m.group(2))
        else:
            return (0,'',s)
    
    def gallery(self):
        if self.gallery is None:
            self.gallery = dict()
        return self.gallery
    
    
    
re_az = re.compile(r"^[a-z].*$")
class CountryView(AbstractView):

    def render(self):
        return render_to_response("country.djt.html", self.summary())
    
    def summary(self, quick = False):
        if self.summary is None:
            countries = Country.objects.all()    
            countriesMap = collections.defaultdict(list)
            gallery = GalleryView()
            for country in countries:
                name = country.name
                if re_az.match(name.lower()):
                    hkey = name.lower()[0]
                else:
                    hkey = "Other"
                if self.key and self.key == country.key:
                    gallery.galleryData = [LocationView(self.request, model = x).gallery() for x in country.location_set]
                countriesMap[hkey].append({
                    'name': name,
                    'url': "%s/country/%s" % (self.request.server_root,country.key)
                })
            extra = {
                'countries': sorted([{'head': k.upper(), 'body': v} for (k,v) in countries.iteritems()],key = lambda x: (x['head'] == 'Other',x['head'])),
                'gallery': gallery.emit(),
            }
            self.summary = dict(extra.items())
        return self.summary
    
    def gallery(self):
        if self.gallery is None:
            self.gallery = dict()
        return self.gallery
            

class AuthorityView(AbstractView):
    
    name = None
    key = None
    model = None
    
    def __init__(self, request, name, key):
        self.name = name
        self.key = key
    
    def loadModel(self):
        if self.model is None:
            self.model = Authority.objects.get(name=self.name, key=self.key)
            
    def loadJson(self):
        if self.json is None:
            self.loadModel()
            self.json = JsonModel.safe_to_json(self.model)
            
    def json(self):
        self.loadJson()
        return self.json;

class IllustrationView(AbstractView):
    
    painting = None
    
    
    def render(self):
        return render_to_response("illustration.djt.html", self.summary())
    
    def loadObject(self):
        if self.model is None:
            self.model = Illustration.objects.get(key = self.key)
            
    
    def summary(self, request, illustrationObj, quick = False):
        if self.summary is None:
            self.loadJson()
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
                'url': "%s/illustration/%s" % (request.server_root,self.key),
                'form': form_tmpl.apply(self.request,self.json),
                'work': AuthorityView('ms-title', self.json['TitleSerial']).json(),
                'chapter': chapter.json(),
                'chapter-k': AuthorityView('chapter-k', self.json['ChapterSerialK']).json(),
                'chapter-b': AuthorityView('chapter-b', self.json['ChapterSerialB']).json(),
                'chapter-ds': AuthorityView('chapter-ds', self.json['ChapterSerialDS']).json(),
                'date': "%s (%s)" % (Hijri.date(self.json['HijriDate']),Gregorian.date(self.json['GregorianDate'])),
                'status': AuthorityView('record-status', self.json['CompletionStatus']).json(),
                'up_date': recordutils.format_date(self.json['DateUpdated']),
                'painter': painter_tmpl.apply(request,self.json),
                'references': recordutils.refs_tmpl(request,self.json,refmap),
                'notes': recordutils.wash_notes(self.json['NotesVisible']),
                'folio': folio_tmpl.apply(request,self.json),
                'format': AuthorityView('ill-format', self.json['FormatSerial']).json(),
                'prev-url': "%s/illustration/%s" % (request.server_root,self.json['chain-prev-folios-in-ms']) if self.json['chain-prev-folios-in-ms'] else '',
                'next-url': "%s/illustration/%s" % (request.server_root,self.json['chain-next-folios-in-ms']) if self.json['chain-next-folios-in-ms'] else '',
            }
            if not quick:
                manuscript = ManuscriptView(self.request, model=self.model.manuscript)
                location = LocationView(request, self.model.manuscript.location)
                scene = SceneView(request, illustrationObj.scene)
                extra['ms_name'] = manuscript.summary()['AccessionNumber']
                extra['ms_url'] = "%s/manuscript/%s" % (request.server_root,manuscript.summary()['ManuscriptSerial'])
                extra['loc_name'] = location.summary()['FullLocationName']
                extra['loc_url'] = "%s/location/%s" % (request.server_root,location.summary()['LocationSerial'])
                extra['loc_city'] = location.summary()['City']
                extra['cou_name'] = location.summary()['country']
                extra['cou_url'] = "%s/country/%s" % (request.server_root,location.summary()['Country'])
                extra['sc_name'] = scene.summary()['EnglishTitle']
                extra['sc_url'] = "%s/scene/%s" % (request.server_root,scene.summary()['SceneSerial'])
                extra['ch_name'] = scene.summary()['chapter_name']
                extra['ch_url'] = scene.summary()['chapter_url']
            self.summary = dict(self.json.items() + extra.items())
        return self.summary
    
    def loadViewGallery(self):
        if self.gallery is None:
            self.gallery = dict()
        return self.gallery
    
    def loadViewPainting(self):
        if self.painting is None:
            self.loadJson()
            pbase = self.request.get_server_attr('paintings_url')
            if 'Painting' in self.json and self.json['Painting']:
                painting = "%s/Painting/%s.jpg" % (pbase,self.json['Painting'])
            else:
                painting = ''
        return painting






class LocationView(AbstractView):
    
    
    def render(self):
        return render_to_response("location.djt.html", self.summary())
    
    def loadObject(self):
        if self.model is None:
            self.model = Location.objects.get(key = self.key)

        
        
        
    def summary(self, quick = False):
        if self.summary is None:
            self.loadJson()
            photo = ''
            pbase = self.request.get_server_attr('paintings_url')
            if self.json['Image']:
                photo = "%s/Location/%s.jpg" % (pbase,self.json['Image'])
            gallery = GalleryView()
            if not quick:
                gallery.galleryData = [GalleryView.entry(photo,'#',self.json['FullLocationName'],'View of location, go forward for manuscripts','','',True)]
                gallery.galleryData.extend([ ManuscriptView(self.request, x) for x in self.model.manuscripts])
            extra = {
                 'country': AuthorityView('country', self.json['Country']).json(),
                 'gallery': gallery.emit(),
                 'up_date': format_date(self.json['DateUpdated']),
                 'contact': contact_tmpl.apply(self.request,self.locationJson),
                 'address': address_tmpl.apply(self.request,self.flocationJson),
                 'notes': wash_notes(self.json['NotesVisible']),
            }
            self.summary = dict(self.json().items() + extra.items())
        return self.summary
    
    def text(self):
        self.loadJson()
        return "%s, %s" % (self.json['FullLocationName'],self.json['City'])
    
    def gallery(self):
        None
        
        



class ManuscriptView(AbstractView):
    
    
    def render(self):
        return render_to_response("manuscript.djt.html", self.summary())
    
    def loadObject(self):
        if self.model is None:
            self.model = Manuscript.objects.get(key = self.key)


    
    def _image_url(self, type):
        self.loadJson()
        pbase = self.request.get_server_attr('paintings_url')
        return "%s/%s/%s.jpg" % (pbase, type, self.json[type])
    
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
            self.loadJson()
            pbase = self.request.get_server_attr('paintings_url')
            for type in ('Colophon','SamplePage'):
                if self.jsond[type]:
                    return self._image_url(type)
            if len(self.json['illustrations']):
                for d in self.json['illustrations']:        
                    p = IllustrationView(self.request, key=d).painting()
                    if p:
                        self.canon_image = p
                        break
            self.canon_image = ''
        return self.canon_image
    
        
    def summary(self, quick=False):
        if self.summary is None:
            self.loadJson()
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
                if self.json['Colophon']:
                    gallery.galleryData.append(GalleryView.entry(self._image_url(self.request, self.json, 'Colophon'), '#', 'Colophon', self.json['ColophonNumber'], '', ''))
                if self.json['SamplePage']:
                    gallery.galleryData.append(GalleryView.entry(self._image_url(self.request, self.json, 'SamplePage'), '#', 'Sample page from this manuscript', '', '', ''))
                gallery.extend([ IllustrationView(self.request, model=x) for x in self.model.illustration_set])
                loc = locationView.summary(True)
            extra = {
                'gallery': gallery.emit(),
                'size': self._size_expr(self.json['PageWidth'], self.json['PageLength'], self.json['TextWidth'], self.json['TextLength']),
                'text': text_tmpl.apply(self.request, self.json),
                'pages': pages_tmpl.apply(self.request, self.json),
                'state': state_tmpl.apply(self.request, self.json),
                'origin': origin_tmpl.apply(self.frequest, self.json),
                'date': "%s (%s)" % (Hijri.date(self.json['HijriDate']), Gregorian.date(self.json['GregorianDate'])),
                'references': refs_tmpl(self.request, self.json, refmap),
                'notes': wash_notes(self.json['NotesVisible']),
                'status': JsonModel.safe_to_json(Authority.objects.get(name='record-status', key=self.json['CompletionStatus'])),
                'up_date': format_date(self.json['DateUpdated']),
                'canon-image': self._canon_image(self.request, self.json),
                'location_text': locationView.text(),
                'location_url': '%s/location/%s' % (self.request.server_root, self.json['LocationSerial']),
                'country': loc['country'],
                'country_url': '%s/country/%s' % (self.request.server_root, loc['Country']),
                'prev-url': "%s/manuscript/%s" % (self.request.server_root, self.json['chain-prev-date']) if self.json['chain-prev-date'] else '',
                'next-url': "%s/manuscript/%s" % (self.request.server_root, self.json['chain-next-date']) if self.json['chain-next-date'] else '',
            }
            self.summary = dict(self.json.items() + extra.items())
        return self.summary
    
    def gallery(self):
        None
        
        
        


class SceneView(AbstractView):
    
    
    def render(self):
        return render_to_response("scene.djt.html", self.summary())
    
    def loadObject(self):
        if self.model is None:
            self.model = Scene.objects.get(key = self.key)
    
    def loadViewSummary(self, quick = False):
        if self.summary is None:
            self.loadJson()
            refmap = {
                'GeneralRef1': 'General',
                'GeneralRef2': 'General',
                'GeneralRef3': 'General',
            }
            gallery = GalleryView()
            if not quick:
                gallery.galleryData = [ IllustrationView(self.request, model = x) for x in self.model.illustration_set]
            chapter = ChapterView(self.request, self.mode.chapter)
            extra = {
                'gallery': gallery.emit(),
                'up_date': format_date(self.json['DateUpdated']),
                'references': refs_tmpl(self.request,self.json,refmap),
                'notes': wash_notes(self.json['NotesVisible']),
                'chapter_name': chapter.json()['ChapterName'],
                'chapter_url': "%s/chapter/%s" % (self.request.server_root,chapter.json()['ChapterSerial'])
            }
            self.summary = dict(self.json.items() + extra.items())
        return self.summary;
    
    def gallery(self):
        None

class ReferenceView(AbstractView):
    def loadObject(self):
        if self.model is None:
            self.model = Reference.objects.get(key = self.key)

    def sentence_summary(self):
        self.loadJson();
        self.json['bib-class'] = AuthorityView('bib-class', self.json['biblioClassificationID']).json()
        return citation_tmpl.apply(self.request,self.json)

citation_tmpl = StringPattern('citation.stb')


def locationView(request, key):
    return LocationView(request, key = key).render()

def illustrationView(request, key):
    return IllustrationView(request, key = key).render()

def countryView(request, key):
    countryView = CountryView(request, key=key)
    return countryView.render()

def manuscriptView(request, key):
        return ManuscriptView(request, key = key).render()

def sceneView(request, key):
        return SceneView(request, key = key).render()

def chapterView(request, key):
        chapterView = ChapterView(request, key=key)
        return chapterView.render()

