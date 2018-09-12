from ectd.PyPDF2 import PdfFileWriter, PdfFileReader

from ectd.PyPDF2.PyPDF2Highlight import createHighlight, addHighlightToPage

pdfInput = PdfFileReader(open("ectd/test/test.pdf", "rb"))
pdfOutput = PdfFileWriter()

page1 = pdfInput.getPage(0)

highlight = createHighlight(100, 400, 400, 500, {})

addHighlightToPage(highlight, page1, pdfOutput)

pdfOutput.addPage(page1)

outputStream = open("test1.pdf", "wb")
pdfOutput.write(outputStream)
