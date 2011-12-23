import datetime,re

from ShahnamaDJ.views import reference


def lcfirst(s):
    if s is not None and s != '':
        return s[0].lower() + s[1:]
    else:
        return s

def ucfirst(s):
    if s is not None and s != '':
        return s[0].upper() + s[1:]
    else:
        return s

def comma_ampersand_list(data):
    if len(data) == 0:
        return ''
    elif len(data) == 1:
        return data[0]
    else:
        return "%s & %s" % (", ".join(data[0:-1]),data[-1])

# XXX dedup
def th(x):
    try:
        x = int(x)
        s = "th"
        if (x%100 < 9 or x%100 > 20) and x%10 < 4:
            s = ['th','st','nd','rd'][x%10]
        return "%d%s" % (x,s)
    except:
        return unicode(x)


re_lz = re.compile(r'#0*')
re_th = re.compile(r'{(.*?)}')
def format_date(d):
    try:
        try:
            out = datetime.datetime.strptime(d,"%Y-%m-%d %H:%M:%S").strftime("#{%d} %B %Y %H:%M")
        except:
            out = datetime.datetime.strptime(d,"%Y-%m-%d %H:%M").strftime("#{%d} %B %Y %H:%M")            
    except:
        out = "no time given"
    out = re_th.sub(lambda x: th(x.group(1)),out)
    out = re_lz.sub('',out)        
    return out

def _general_first(key):
    return (key.find('General')==-1,key)

def refs_tmpl(request,data,refmap):
    refs = {}
    for (name,title) in refmap.iteritems():
        if data[name] is not None and str(data[name]).strip() != '':
            if not data[name] in refs:
                refs[data[name]] = set()
            refs[data[name]].add(title)
    refs_tmpl = []
    for (ref,kd) in refs.iteritems():
        title = comma_ampersand_list(sorted(kd))
        value = reference.sentence_summary(request,ref)
        refs_tmpl.append({'key': title, 'value': value})
    refs_tmpl.sort(key=lambda x: _general_first(x['key']))
    for i in range(len(refs_tmpl)-1,0,-1):
        if refs_tmpl[i-1]['key'] == refs_tmpl[i]['key']:
            refs_tmpl[i]['key'] = ''
    return refs_tmpl

re_p_tag = re.compile("(<p>)+")
def wash_notes(data):
    if not data:
        return ''
    return "".join(["<p>%s</p>" % x for x in re_p_tag.split(data)])

folios = re.compile(r"^([0-9]+)([vr]?)$")
def folio_num_key(k):
    m = folios.match(k)
    if not m:
        return None
    val = int(m.group(1))*2
    if m.group(2) == 'v':
        val += 1
    return val
