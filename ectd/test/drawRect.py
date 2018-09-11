from reportlab.graphics.shapes import Rect
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import PCMYKColor, PCMYKColorSep, Color, black, blue, red

filename = 'alpha.pdf'

red50transparent = Color( 100, 0, 0, alpha=0.5)

c = Canvas(filename,pagesize=(400,200))
c.setFillColor(black)
c.setFont('Helvetica', 10)

c.drawString(25,180, 'solid')
c.setFillColor(blue)
c.rect(25,25,100,100, fill=True, stroke=False)
c.setFillColor(red)
c.rect(100,75,100,100, fill=True, stroke=False)

c.setFillColor(black)
c.drawString(225,180, 'transparent')

c.setFillColor(blue)
c.rect(225,25,100,100, fill=True, stroke=False)
c.setFillColor(red50transparent)
c.rect(300,75,100,100, fill=True, stroke=False)

c.save()