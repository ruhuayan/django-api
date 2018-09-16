from .pdf import PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Rect
from reportlab.lib.colors import Color
import io

def drawBackground(page, rect):
    page_w = page.mediaBox.getWidth()
    page_h = page.mediaBox.getHeight()
    packet = io.BytesIO
    blue50transparent = Color( 0, 0, 255, alpha=0.5)  #default color blue
    can = canvas.Canvas(packet, pagesize=(page_w, page_h))
    # x, y, w, h = rect
    x1, y1, x2, y2 = rect
    w = x2 - x1
    h = y2 - y1
    can.setFillColor(blue50transparent)
    can.rect(x1, y1, w, h, fill=True, stroke=False)
    can.save()
    packet.seek(0)
    page.mergePage(PdfFileReader(packet))
    return page

def drasString(page, x, y, txt):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=pagesize)
    can.drawString(x, y, txt)
    can.save()
    packet.seek(0)
    return PdfFileReader(packet).getPage(0)
