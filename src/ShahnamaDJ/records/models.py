from django.db import models
import json
# Create your models here.
'''
This model is based on the model developed by Dan to translate the relational tables used in the original
MySQL Shahnama data base into a model that could be stored in Berkley DB, hence it is not fully relational
and needs some explanation. This is probably best done by looking at the configuration in Migrate.py, copied
here for completeness.

The structure below defines the translation from the MySQL relational DB into Json files.
The key is the name of the MySQL table eg 'Illustration', 'MsType', etc.
'dir' is the file system dir where the record is serialized, and 'serial' is the name of the field that
represents the ID of the record.
'fixes' represents a set of fixed to data which was applied in translating from MySQL to Json.
'build' builds a link and adds the field names
'authority' means the record is pushed into a single authority table with a type constant as specified 'ms-type',
   'serial' is the name of the ID field in mysql in the table eg MsType.MsTypeSerial is the ID of the authority
   appearing in the json as 'serial'
   'value' is the name of the mysql field where the authority is contained.
   'order' adds a order field to the json based on the required ordering.

So the authority table forms a dictionary of authority types indexed by type and serial. Unfortunately the serials do clash so they can't
be used as a ID. The code would probably benefit from being able to load the entire authority file into memory. That is, I guess, what
Dan was trying to do with BDB and maps and eliminate the overhead of performing a SQL operation for each lookup. It should be possible
to tell Django to simply cache the values in the reference table which will have the same effect.

tables = {
    'Illustration': {'dir': 'illustration', 'serial': 'IllustrationSerial',
                     'fixes': { 'GregorianDate': { 'late 18th c.': '18th/Cla//', 'ca. 1440': '1440/Yca//', '17th century': '17th/C//', 'early 15th c.': '15th/Cea//',
                                                    '1648 December 18': '1648/---/Dec/18', '15th c., late': '15th/Cla//' },
                                'HijriDate': { '0868/Thh/06': '0868/Dhh/06', '27 Safar 1010': '1010/Saf/27' },
                                'AttributionPainter': { 1681572333: '' },
                                'AttributionStyle': { 1681572333: '' }} },
    'Location': {'dir': 'location', 'serial': 'LocationSerial',
                 'build': [{ 'authority': 'country', 'from': 'Country' }] },
    'Reference': {'dir': 'reference', 'serial': 'ReferenceSerial' },
    'Manuscript': {'dir': 'manuscript', 'serial': 'ManuscriptSerial',
                   'fixes': { 'GregorianDate': { '18th c. late': '18th/Cla//', '17th century': '17th/C//', '1576-77':'1576/Y+1//', '1440 c.': '1440/Yca//',
                                                 '1600 - 1602': '1600/Y02//' },
                              'IllustrationReference' : {0: ''},
                              'HijriDate': { '0983/Thk/': '0983/Dhk/' } }},
    'MsType': {'authority': 'ms-type', 'serial': 'MsTypeSerial', 'value': 'MsType' },
    'MsAuthor': {'authority': 'ms-author', 'serial': 'MsAuthorSerial', 'value': 'MsAuthor' },
    'MsStatus': {'authority': 'ms-status', 'serial': 'MsStatusSerial', 'value': 'MsStatus' },
    'zTitleOfWork': {'authority': 'ms-title', 'serial': 'TitleSerial', 'value': 'TitleOfWork' },
    'Language': {'authority': 'ms-lang', 'serial': 'LanguageSerial', 'value': 'Language' },
    'tbl_Bibliography_Classification': { 'authority': 'bib-class', 'serial': 'biblioClassificationID', 'value': 'BiblioClassification'},
    'zRecordStatus': {'authority': 'record-status', 'serial': 'RecordStatusSerial', 'value': 'RecordStatus' },
    'ChaptersMohl': { 'dir': 'chapter', 'serial': 'ChapterSerial' },
    'ChaptersK': { 'authority': 'chapter-k', 'serial': 'ChapterSerial', 'value': 'ChapterName', 'order': 'ChapterCode' },
    'ChaptersB': { 'authority': 'chapter-b', 'serial': 'ChapterSerial', 'value': 'ChapterName', 'order': 'ChapterCode' },
    'ChaptersDS': { 'authority': 'chapter-ds', 'serial': 'ChapterSerial', 'value': 'ChapterName', 'order': 'ChapterCode' },
    'zSceneFormat': {'authority': 'ill-format', 'serial': 'FormatSerial', 'value': 'Category' },
    'IllustrationTitles': { 'dir': 'scene', 'serial': 'SceneSerial',
                             'has': { 'chapter': { 'table': 'ChaptersMohl', 'key': 'ChapterCode', 'capture': 'ChapterSerial', 'from': 'Chapter', 'single': True },  }  },
}


'''
import logging


class JsonModel(models.Model):
    id = models.IntegerField(primary_key=True)
    key = models.CharField(max_length=32, null=True, blank=True)
    data = models.TextField()
    errors = []

    def buildRelationships(self):
        None

    def to_json(self):
        return json.loads(self.data)


    def _getReferencedObject(self, field, model, json, linkName):
        if linkName in json and json[linkName] is not None:
            if field is None or field.id != json[linkName]:
                try:
                    return model.objects.get(id=json[linkName])
                except:
                    self.errors.append("Object %s of type %s does not exist from %s %s" %(json[linkName], model, self, self.id))
                    return None
        return field

    def _safeGetProperty(self, json, valueName, default = None):
        if valueName in json:
            return json[valueName]
        return default

    @staticmethod
    def safe_to_json(obj):
        if obj:
            return obj.to_json()
        return None
    
    

    def getErrors(self):
        return self.errors

    def clearErrors(self):
        self.errors = []

    class Meta:
        abstract = True




class Chapter(JsonModel):
    '''
    Sample Json
    {
    "ChapterName": "Other epics",
    "Gen_NotesVisible": 0,
    "NotesVisible": "This is a temporary catch-all category for sections of other epcis interpolated into manuscripts of the Shahnama",
    "ChapterSerial": 1099084114,
    "ChapterCode": "-2"
    }
    '''
    name = models.CharField(max_length=64, null=True, blank=True)

    @staticmethod
    def getKeyFromJson(dictObject):
        return dictObject["ChapterSerial"]

    def buildRelationships(self):
        json = self.to_json()
        self.name = self._safeGetProperty(json, "ChapterName")

    @staticmethod
    def createFromJson(data, key):
        dataKey = Chapter.getKeyFromJson(data)
        if dataKey is None:
            dataKey = key
        return Chapter.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))

    class Meta:
        ordering = ['name']


class Reference(JsonModel):
    '''
    Sample Json
    {
    "PublishedCountry": null,
    "PublishedCity": null,
    "UniformTranslator": null,
    "biblioClassificationID": 1058543753,
    "UniformEditor": null,
    "InTitle2": null,
    "InTitle1": "Apollo",
    "SerialYear": null,
    "PublishedYear": 1931,
    "DateUpdated": null,
    "DatabaseUser": null,
    "UniformAuthor": "Minorsky, V.",
    "VolumeNumber": "13",
    "ProjectNotes": null,
    "ReferenceSerial": -1475450901,
    "FullTitle": "Two Unknow Persian Manuscripts",
    "ElectronicAddress": null,
    "Gen_ElectronicAddress": null,
    "Pages": "71-75",
    "UniformTitle": "Two Unknow Persian Manuscripts",
    "PublisherName": null
     }
    '''
    name = models.CharField(max_length=64, null=True, blank=True)

    @staticmethod
    def getKeyFromJson(dictObject):
        return dictObject["ReferenceSerial"]

    @staticmethod
    def createFromJson(data, key):
        dataKey = Reference.getKeyFromJson(data)
        if dataKey is None:
            dataKey = key
        return Reference.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))

    def buildRelationships(self):
        json = self.to_json()
        self.name = self._safeGetProperty(json, "UniformTitle")

    class Meta:
        ordering = ['name']




class Country(JsonModel):
    # stored as value
    '''
    Sample Json
    {
    "serial": 8,
    "type": "country",
    "value": "Russia"
    }
    '''
    name = models.CharField(max_length=64, null=True, blank=True)

    @staticmethod
    def getKeyFromJson(dictObject):
        return dictObject["serial"]
    
    @staticmethod
    def createFromJson(data, key):
        dataKey = Country.getKeyFromJson(data)
        if dataKey is None:
            dataKey = key
        return Country.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))

    def buildRelationships(self):
        json = self.to_json()
        self.name = self._safeGetProperty(json, "value")
        self.key = self._safeGetProperty(json, "value")


    class Meta:
        ordering = ['name']

class Location(JsonModel):
    # stored as Country in the original json
    '''
    Sample JSON
    {
    "TelephoneNumber": null,
    "City": "Sheikhupoora",
    "DatabaseUser": null,
    "InImageCopyright": null,
    "FullLocationName": "Mir Val Library",
    "Country": 7,
    "Image": null,
    "LocationSerial": 1253945785,
    "ProjectNotes": null,
    "FaxNumber": null,
    "DateUpdated": null,
    "StreetAddress": null,
    "Watermark": null,
    "Location": "SHEIKHUPOORA",
    "CopyrightDetails": "<A9> ",
    "NotesVisible": null,
    "NameContact": null,
    "Email": null,
    "Website": null
    }
    '''
    country = models.ForeignKey(Country,  blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=64, null=True, blank=True)


    @staticmethod
    def getKeyFromJson(dictObject):
        return dictObject["LocationSerial"]
    
    @staticmethod
    def createFromJson(data, key):
        dataKey = Location.getKeyFromJson(data)
        if dataKey is None:
            dataKey = key
        return Location.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))

    def buildRelationships(self):
        json = self.to_json()
        self.name = self._safeGetProperty(json, "FullLocationName")
        self.country = self._getReferencedObject(self.country, Country, json, "Country")




class Manuscript(JsonModel):
    '''
    Sample JSON for Manuscript
    {
    "AccessionNumber": "H. 1494",
    "TitleSerial": 1,
    "AttributionEstimate": 977261121,
    "LocationSerial": 841770509,
    "ManuscriptSerial": 1122734076,
    "PageLength": null,
    "OtherDescription": null,
    "EstimatedNumberFolios": null,
    "HijriDate": null,
    "Note": "Imported from Farhad's Excel worksheet - Check for errors",
    "FolioNoSamplePage": null,
    "LanguageSerial": 1,
    "GeneralRef3": null,
    "OtherNumber": null,
    "NotesVisible": null,
    "TextLength": null,
    "DatabaseUser": "charles",
    "PageWidth": 215,
    "SamplePage": "{9D6D02A8-3400-81BE-7015-275E238578C1}",
    "Script": "Nasta'liq",
    "Gen_Note": null,
    "SamplePageLink": null,
    "CopyrightDetails": "(c) Topkapi Saray Palace Library",
    "Gen_NotesVisible": null,
    "SamplePageURL": null,
    "Barzunama": null,
    "NumberColumns": 4,
    "Ownership": null,
    "NumberExtantFolios": 591,
    "IllustrationReference": 977261121,
    "ColophonLink": null,
    "GeneralRef1": -1313456105,
    "Frontispieces": 3,
    "Garshaspnama": null,
    "CompletionStatus": -438597461,
    "ProjectNotes": null,
    "TotalNumber": 77,
    "Glossary": null,
    "TextWidth": 115,
    "Preface": null,
    "NumFieldsEmpty": 16,
    "Gen_Ownership": null,
    "MsStatusSerial": 1,
    "NumberRows": 23,
    "AttributionDate": 977261121,
    "NumberOtherColophons": null,
    "PlaceOrigin": null,
    "DateUpdated": "2008-11-03 00:00:00",
    "GeneralRef2": null,
    "GregorianDate": "1520/yca/   /",
    "FinisPieces": 2,
    "Illuminations": null,
    "ColophonNumber": "-",
    "MsTypeSerial": -1687705554,
    "Colophon": null,
    "Patron": null,
    "Shahnama": 72,
    "ColophonURL": null,
    "MsAuthorSerial": 1,
    "Calligrapher": null,
    "AttributionOrigin": null
    }
    '''
    location = models.ForeignKey(Location,  blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=64, null=True, blank=True)

    @staticmethod
    def getKeyFromJson(dictObject):
        return dictObject["ManuscriptSerial"]
    
    @staticmethod
    def createFromJson(data, key):
        dataKey = Manuscript.getKeyFromJson(data)
        if dataKey is None:
            dataKey = key
        return Manuscript.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))

    def buildRelationships(self):
        json = self.to_json()
        self.name = self._safeGetProperty(json, "FullLocationName")# this is not right, but there is nothing else.
        self.location = self._getReferencedObject(self.location, Location, json, "LocationSerial")

    class Meta:
        ordering = ['name']


class Scene(JsonModel):
    '''
    Sample Json

    {
    "MohlStart": "545",
    "SceneKey": 843,
    "WarnerPage": null,
    "SceneSerial": 154622915,
    "MohlEnd": "660",
    "BertelsVolume": null,
    "Kh_M": "NA",
    "WarnerEnd": null,
    "DatabaseUser": null,
    "KEnd": null,
    "Page": 1546,
    "KPage": null,
    "EndVerse": 660,
    "MTVolume": null,
    "MohlVolume": "22",
    "NotesVisible": null,
    "Chapter": "22",
    "ProjectNotes": null,
    "BertelsStart": null,
    "KStart": null,
    "Warner": "Vol. VI, 286ff",
    "BertelsPage": null,
    "Bertels": "NA",
    "MTStart": null,
    "MTPage": null,
    "WarnerStart": null,
    "DateUpdated": null,
    "MTEnd": null,
    "GeneralRef2": null,
    "GeneralRef3": null,
    "BertelsEnd": null,
    "GeneralRef1": null,
    "chapter": -10675995,
    "StartVerse": 545,
    "PersianTitle": "",
    "WarnerVolume": null,
    "MohlPage": "1546",
    "KVolume": null,
    "EnglishTitle": "Ardashir cedes the throne to Shapur",
    "Mohl": "(Tome V, 302ff)",
    "OldPersianTitle": "0843"
    }
    '''
    chapter = models.ForeignKey(Chapter,  blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=64, null=True, blank=True)

    @staticmethod
    def getKeyFromJson(dictObject):
        return dictObject['SceneSerial']

    @staticmethod
    def createFromJson(data, key):
        dataKey = Scene.getKeyFromJson(data)
        if dataKey is None:
            dataKey = key
        return Scene.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))

    def buildRelationships(self):
        json = self.to_json()
        self.name = self._safeGetProperty(json, "EnglishTitle")
        self.chapter = self._getReferencedObject(self.chapter, Chapter, json, 'chapter')

    class Meta:
        ordering = ['name']

class Illustration(JsonModel):
    '''
    Sample JSON

    {
    "AccessionNumber": "Per 104.079",
    "BreakLineBbefore": 112,
    "TitleSerial": -608630224,
    "LocationSerial": 2054618353,
    "ManuscriptSerial": 1018871634,
    "SceneSerial": 1821271132,
    "Note": null,
    "BreakLineMafter": null,
    "ReconstructedFolioNum": "315r",
    "NotesVisible": null,
    "CompletionStatus": 203935646,
    "GeneralReferences1": null,
    "GeneralReferences2": null,
    "FirstLineM": 88,
    "FirstLineK": null,
    "Gen_NotesVisible": null,
    "AttributionPainter": null,
    "FirstLineB": 84,
    "NamePainter": null,
    "GregorianDate": "1300/Yca/---/--",
    "LastLineB": 139,
    "TitlePersian": null,
    "BreakLineBafter": null,
    "LastLineK": null,
    "IllustrationVisible": 1,
    "PaintingURL": null,
    "SceneFouchecourNumber": null,
    "LastLineM": 144,
    "BreakLineKbefore": null,
    "ProjectNotes": null,
    "ChapterSerialB": -1236631107,
    "SchoolPainting": "Baghdad",
    "NumFieldsEmpty": 15,
    "ChapterSerialM": 2094713340,
    "ChapterSerialK": null,
    "DatabaseUser": "charles",
    "BreakLineDSbefore": null,
    "FirstLineDS": null,
    "Length": 45,
    "GeneralReferences3": null,
    "BreakLineKafter": null,
    "DateUpdated": "0000-00-00 00:00:00",
    "HijriDate": null,
    "Painting": "{8574AA6F-99A5-1380-C53C-39914BC87A5B}",
    "Gen_Note": null,
    "CopyrightDetails": "(c) The Chester Beatty Library, Dublin",
    "FormatSerial": 1,
    "LastLineDS": null,
    "AttributionDate": 792153451,
    "BreakLineDSafter": null,
    "Width": 123,
    "PaintingLink": null,
    "AttributionStyle": 792153451,
    "FolioNumber": "079",
    "TitleEnglish": "Khusrau Parviz answering to the charges brought by his son, Shiruy",
    "BreakLineMbefore": 117,
    "ChapterSerialDS": 2094713340,
    "IllustrationSerial": 1226486543
    }
    '''
    ## cant have this without a link chapter = models.ForeignKey(Chapter,  blank=True, null=True, on_delete=models.SET_NULL)
    manuscript = models.ForeignKey(Manuscript,  blank=True, null=True, on_delete=models.SET_NULL)
    scene = models.ForeignKey(Scene,  blank=True, null=True, on_delete=models.SET_NULL)
    location = models.ForeignKey(Location, blank=True, null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=64, null=True, blank=True)

    @staticmethod
    def getKeyFromJson(dictObject):
        return dictObject['IllustrationSerial']

    @staticmethod
    def createFromJson(data, key):
        dataKey = Illustration.getKeyFromJson(data)
        if dataKey is None:
            dataKey = key
        return Illustration.objects.create(id=dataKey, key=dataKey, data = json.dumps(data))

    def buildRelationships(self):
        json = self.to_json()

        self.name = self._safeGetProperty(json, "EnglishTitle")
        self.manuscript = self._getReferencedObject(self.manuscript, Manuscript, json, 'ManuscriptSerial')
        self.scene = self._getReferencedObject(self.scene, Scene, json, 'SceneSerial')
        self.location = self._getReferencedObject(self.location, Location, json, 'LocationSerial')


    class Meta:
        ordering = ['name']

class Authority(models.Model):
    '''
    {
    "serial": 1057400490,
    "type": "chapter-k",
    "order": 9,
    "value": "Zav-i Tahmasp (156)"
    }
    '''
    namekey = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=32, db_index=True)
    key = models.IntegerField(db_index=True)
    
    order = models.CharField(max_length=10,default="0")
    data = models.TextField()
    errors = []

    @staticmethod
    def getKeyFromJson(dictObject):
        return dictObject['serial']


    @staticmethod
    def createFromJson(data, key):
        dataKey = Authority.getKeyFromJson(data)
        type = data['type']
        if dataKey is None:
            dataKey = key
            namekey = key
        else:
            namekey = "%s:%s" % (type, dataKey)
        logging.error("Creating %s %s %s " % (namekey, dataKey, type))
        return Authority.objects.create(namekey=namekey, key=dataKey, name=type, data=json.dumps(data))

    def _safeGetProperty(self, json, valueName, default = None):
        if valueName in json:
            return json[valueName]
        return default

    def buildRelationships(self):
        json = self.to_json()
        self.order = self._safeGetProperty(json, "order", default = "0")
        
    def to_json(self):
        return json.loads(self.data)

    def getErrors(self):
        return self.errors

    def clearErrors(self):
        self.errors = []


    class Meta:
        ordering = ['order','name']



