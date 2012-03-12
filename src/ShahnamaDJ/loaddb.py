'''
Created on Jan 10, 2012

@author: ieb
'''
from ShahnamaDJ.records.models import Chapter, Country, Location, Manuscript,\
    Scene, Illustration, Authority, Reference
from ShahnamaDJ.content.models import Content

# This the the mapping of folder into Object type for the json data
# eg SOURCE_DATA/chapter contains json files for Chapter objects
RECORDS_SOURCE_DATA = {
        'chapter' : Chapter,
        'country' : Country,
        'location' : Location,
        'manuscript' : Manuscript,
        'scene' : Scene,
        'illustration' : Illustration,
        'reference' : Reference,
        'authority' : Authority,
#        'ms-type' : Authority,
#        'ms-author' : Authority,
#        'ms-status' : Authority,
#        'ms-title' : Authority,
#        'ms-lang' : Authority,
#        'bib-class' : Authority,
#        'record-status' : Authority,
#        'chapter-k' : Authority,
#        'chapter-b' : Authority,
#        'chapter-ds' : Authority,
#        'ill-format' : Authority,
        }

CONTENT_SOURCE_DATA = {
        'content' : Content
        }

