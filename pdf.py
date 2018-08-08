from xhtml2pdf import pisa
from io import BytesIO

"""
Generates a PDF from given content. 
See http://flask.pocoo.org/snippets/68/. 
"""
def gen_pdf(content):
    print('IO')
    pdf = BytesIO()
    print('CreatePDF')
    pisa.CreatePDF(BytesIO(content.encode('utf-8')), pdf)
    print('GetValue')
    resp = pdf.getvalue()
    pdf.close()
    return resp