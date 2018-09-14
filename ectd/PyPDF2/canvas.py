from .pdf import PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Rect
from reportlab.lib.colors import Color
import io

def drawBackground(rect, pagesize=letter):
    packet = io.BytesIO
    blue50transparent = Color( 0, 0, 255, alpha=0.5)  #default color blue
    can = canvas.Canvas(packet, pagesize=pagesize)
    x, y, w, h = rect
    can.setFillColor(blue50transparent)
    can.rect(x, y, w, h, fill=True, stroke=False)
    can.save()
    packet.seek(0)
    return packet

def drasString(x, y, txt, pagesize=letter):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=pagesize)
    can.drawString(x, y, txt)
    can.save()
    packet.seek(0)
    return PdfFileReader(packet).getPage(0)
