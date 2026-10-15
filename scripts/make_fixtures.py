"""Create deterministic digital, multipage and scanned PDFs for comparison."""
from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from PIL import Image, ImageDraw, ImageFont, JpegImagePlugin  # register JPEG writer explicitly

out = Path(__file__).resolve().parents[1] / 'tests/fixtures'
writer = PdfWriter()
for title, lines in [
    ('Test Document', ['Experience', 'Software Engineer 2020-2024', 'Built reliable document processing systems.', 'Skills', 'Python, SQL, Linux']),
    ('Second Page', ['Education', 'University Example 2016-2020', 'Bachelor of Computer Science.', 'References available on request.'])
]:
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    commands = ['BT /F1 24 Tf 50 730 Td (' + title + ') Tj']
    for line in lines:
        commands.append('0 -50 Td /F1 12 Tf (' + line + ') Tj')
    commands.append('ET')
    stream.set_data(('\n'.join(commands)).encode('ascii'))
    page[NameObject('/Contents')] = writer._add_object(stream)
writer.write(out / 'digital-multipage.pdf')
image = Image.new('RGB', (1200, 1600), 'white')
draw = ImageDraw.Draw(image)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
for y, line in enumerate(['Scanned document', 'Work Experience', 'Software engineer at Example Corporation.', 'Built PDF extraction systems.', 'Education', 'Bachelor of Science, Computer Science.']):
    draw.text((90, 140+y*120), line, fill='black', font=font)
image.save(out / 'scanned.pdf', resolution=150)
