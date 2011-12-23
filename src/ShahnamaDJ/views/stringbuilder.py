import re
from xml.etree.ElementTree import ElementTree
from xml.sax.saxutils import escape
from django.template import loader
from ShahnamaDJ.records.views import AuthorityView

def _th(x):
    try:
        x = int(x)
        s = "th"
        if (x%100 < 9 or x%100 > 20) and x%10 < 4:
            s = ['th','st','nd','rd'][x%10]
        return "%d%s" % (x,s)
    except:
        return unicode(x)

def comma_ampersand_list(data):
    data = [x.strip() for x in data]
    if len(data) == 0:
        return ''
    elif len(data) == 1:
        return data[0]
    else:
        return "%s & %s" % (", ".join(data[0:-1]),data[-1])

def _ucfirst(s):
    if s is not None and s != '':
        return s[0].upper() + s[1:]
    else:
        return s

re_ws = re.compile(r"\s+")
def ws(data):
    return re_ws.sub(' ',data)

re_rpunc = re.compile(r"\s+([\.,;:])")

class StringPattern:
    def __init__(self,filename):
        self._xml = ElementTree()
        (source, origin) = loader.find_template(filename)
        self._xml.parse(source)

    def _apply_text(self,node,text):
        return escape(unicode(text))

    def _subvalue(self,node,request,model):
        contents = ""
        if node.text:
            contents += self._apply_text(node,node.text)
        for child in node:
            contents += self._apply_node(child,request,model)
            if child.tail:
                contents += self._apply_text(node,child.tail)
        return contents

    def _apply_node(self,node,request,model):
        if node.tag == 'value':
            v = ''
            k = node.attrib['key'] if 'key' in node.attrib else None
            if k and k in model and model[k]:
                v = model[k]
            if v and 'authority' in node.attrib:
                v = AuthorityView(node.attrib['authority'],v)
            return escape(unicode(v))
        elif node.tag == 'join':
            out = [self._apply_node(x,request,model) for x in node]
            out = [x for x in out if x and x.strip() != '']
            sep = node.attrib['separator'] if 'separator' in node.attrib else ', '
            return sep.join(out)
        elif node.tag == 'text':
            out = self._subvalue(node,request,model)
            left = set(node.attrib['left'].split(',')) if 'left' in node.attrib else set()
            right = set(node.attrib['right'].split(',')) if 'right' in node.attrib else set()            
            if 'chop' in left:
                out = out.lstrip()
            if 'chop' in right:
                out = out.rstrip()
            if 'tail' in node.attrib and out.strip():
                out += node.attrib['tail']
            if 'nodot' in right:
                out = out.rstrip()
                out = out.rstrip(".")
            if 'lc' in left or 'lc' in right:
                out = out.lower()
            if 'ucfirst' in left or 'ucfirst' in right:
                out = _ucfirst(out)
            if 'punc' in right:
                out = re_rpunc.sub(r'\1',out)
            return out
        elif node.tag == 'singular' or node.tag == 'plural':
            k = node.attrib['key'] if 'key' in node.attrib else None
            if k and k in model:
                v = model[k]
            v = unicode(v)
            sub = unicode(self._subvalue(node,request,model))
            try:
                if int(v.strip()) > 1 and node.tag == 'plural':
                    return sub
                elif int(v.strip()) == 1 and node.tag == 'singular':
                    return sub
                return ''
            except:
                return ''
        elif node.tag == 'each':
            v = []
            k = node.attrib['key'] if 'key' in node.attrib else None
            if k and k in model:
                v = model[k]
            if len(v):
                out = []
                for x in v:
                    submodel = dict(model)
                    submodel[k] = x
                    out.append(self._subvalue(node,request,submodel))
                out = comma_ampersand_list(out)
                out += node.attrib['tail'] if 'tail' in node.attrib else ''
                return out
            return ''
        elif node.tag == 'if':
            ks = node.attrib['key'] if 'key' in node.attrib else None
            for k in ks.split("|"):        
                if k and k in model and model[k]:
                    return self._subvalue(node,request,model)
            return ''
        elif node.tag == 'condition':
            v = ''
            k = node.attrib['key'] if 'key' in node.attrib else None
            if k and k in model:
                v = model[k]
            re_c = re.compile(node.attrib['expression'])
            match = True if re_c.search(unicode(v)) else False
            looking_for = True if 'match' in node.attrib and node.attrib['match'].lower() == 'true' else False
            if (match and looking_for) or ((not match) and (not looking_for)):
                return self._subvalue(node,request,model)
            else:
                return ''         
        elif node.tag == 'th':
            return _th(self._subvalue(node,request,model))
        elif node.tag == 'container':
            return self._subvalue(node,request,model)
        else:
            attrs = ['%s="%s"' % (k,v) for (k,v) in node.attrib.iteritems()] 
            if len(attrs):
                attrs = " " + attrs
            contents = "<%s%s>%s</%s>" % (node.tag," ".join(attrs),self._subvalue(node,request,model),node.tag)            
            return contents

    def apply(self,request,model):
        return unicode(ws(self._apply_node(self._xml.getroot(),request,model)).strip())
