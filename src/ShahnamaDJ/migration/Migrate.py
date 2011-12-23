#!/usr/bin/env python
#
# This script dumps the MySQL Shahnama database into json files on disk that act as a source for the new data.
#
if __name__ != '__main__':
    return

import json
import MySQLdb
import collections
from ShahnamaDJ.settings import SOURCE_DATA


base = SOURCE_DATA

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

full_authorities = set(['country'])

conn = MySQLdb.connect (host = "localhost",
                        user = "root",
                        passwd = "",
                        db = "shahnama")

authorities = {}
built = collections.defaultdict(dict)
serials = collections.defaultdict(lambda: 1)
for (table,d) in tables.iteritems():
    print "Processing table '%s'" % table
    cursor = conn.cursor (MySQLdb.cursors.DictCursor)
    cursor.execute ("SELECT * FROM %s" % table)
    result_set = cursor.fetchall ()
    for row in result_set:
        if 'authority' in d:
            data = { 'value': row[d['value']], 'serial': row[d['serial']], 'type': d['authority'] }
            if 'order' in d:
                data['order'] = row[d['order']]
            authorities[(d['authority'],row[d['serial']])] = data            
        else:
            out = open("%s/%s/%s" % (base,d['dir'],row[d['serial']]),"w")
            if 'has' in d:
                for (key,d2) in d['has'].iteritems():
                    cursor2 = conn.cursor (MySQLdb.cursors.DictCursor)
                    index = d2['from'] if 'from' in d2 else d['serial']
                    result_set2 = cursor2.fetchall ()
                    v = []
                    for row2 in result_set2:
                        v.append(row2[d2['capture']])
                    if 'single' in d2 and d2['single']:
                        v = v[0] if len(v) else None
                    row[key] = v
                    cursor2.close()
            if 'build' in d:
                for b in d['build']:
                    if row[b['from']] in built[b['authority']]:
                        id = built[b['authority']][row[b['from']]]
                    else:
                        id = serials[b['authority']]
                        built[b['authority']][row[b['from']]] = id
                        serials[b['authority']] += 1
                    row[b['from']] = id
            if 'fixes' in d:
                for (field,maps) in d['fixes'].iteritems():
                    if row[field] in maps:
                        row[field] = maps[row[field]]
            json.dump(row,out,ensure_ascii = False)
            out.close()
    cursor.close()
print "Processing authorities"
for (auth,v) in built.iteritems():
    for (value,id) in v.iteritems():
        authorities[(auth,id)] = { 'value': value, 'serial': id, 'type': auth }
for ((auth,serial),data) in authorities.iteritems():
    if auth in full_authorities:
        out = open("%s/%s/%s" % (base,auth,serial),"w")
    else:
        out = open("%s/authority/%s--%s" % (base,auth,serial),"w")
    json.dump(data,out,ensure_ascii = False)
    out.close()
