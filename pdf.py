# http://flask.pocoo.org/snippets/68/

from xhtml2pdf import pisa
from cStringIO import StringIO

def gen_pdf(content):
    pdf = StringIO()
    pisa.CreatePDF(StringIO(content.encode('utf-8')), pdf)
    resp = pdf.getvalue()
    pdf.close()
    return resp