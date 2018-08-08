from xhtml2pdf import pisa
from io import StringIO

"""
Generates a PDF from given content. 
See http://flask.pocoo.org/snippets/68/. 
"""
def gen_pdf(content):
    pdf = StringIO()
    pisa.CreatePDF(StringIO(content.encode('utf-8')), pdf)
    resp = pdf.getvalue()
    pdf.close()
    return resp