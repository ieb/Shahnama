from ShahnamaDJ.records.models import Authority, Reference, JsonModel
from ShahnamaDJ.views.stringbuilder import StringPattern

def sentence_summary(request,id):
    data = JsonModel.safe_to_json(Reference.objects.get(id=id))
    data['bib-class'] = JsonModel.safe_to_json(Authority.objects.get(name='bib-class', key=data['biblioClassificationID']))
    return citation_tmpl.apply(request,data)

citation_tmpl = StringPattern('citation.stb')
