from ectd.PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Rect
from reportlab.lib.colors import PCMYKColor, PCMYKColorSep, Color, black, blue, red
import io

packet = io.BytesIO()
blue50transparent = Color( 0, 0, 255, alpha=0.5)
# create a new PDF with Reportlab
can = canvas.Canvas(packet, pagesize=letter)
can.drawString(10, 100, "Hello world")

can.setFillColor(blue50transparent)
can.rect(300,75,100,100, fill=True, stroke=False)

can.save()

#move to the beginning of the StringIO buffer
packet.seek(0)
new_pdf = PdfFileReader(packet)
#read your existing PDF
existing_pdf = PdfFileReader(open("ectd/test/test.pdf", "rb"))
output = PdfFileWriter()
# add the "watermark" (which is the new pdf) on the existing page
page = existing_pdf.getPage(0)
page.mergePage(new_pdf.getPage(0))
output.addPage(page)
# finally, write "output" to a real file
outputStream = open("destination.pdf", "wb")
output.write(outputStream)
outputStream.close()

def drawBackground(rect, pagesize=letter):
    packet = io.BytesIO
    blue50transparent = Color( 0, 0, 255, alpha=0.5)  #default color blue
    can = canvas.Canvas(packet, pagesize=pagesize)
    x, y, w, h = rect
    can.setFillColor(x, y, w, h, fill=True, stroke=False)
    can.save()
    packet.seek(0)
    return PdfFileReader(packet)

def drasString(x, y, txt, pagesize=letter):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=pagesize)
    can.drawString(x, y, txt)
    can.save()
    packet.seek(0)
    return PdfFileReader(packet)
