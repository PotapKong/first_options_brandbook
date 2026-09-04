from pathlib import Path
from bs4 import BeautifulSoup
from pypdf import PdfReader
import fitz
from PIL import Image, ImageDraw
import re

base = Path(__file__).parent
pdf = base / 'Первая_карта_российского_опционного_рынка_дизайн-макет.pdf'
html = base / 'Первая_карта_российского_опционного_рынка_дизайн-макет.html'
reader = PdfReader(pdf)
texts = [page.extract_text() or '' for page in reader.pages]
full = '\n'.join(texts)
html_text = html.read_text(encoding='utf-8')
soup = BeautifulSoup(html_text, 'html.parser')

assert len(reader.pages) >= 15
assert all(text.strip() for text in texts)
assert full.upper().count('КОММЕНТАРИЙ ДИЗАЙНЕРУ') == 13
assert 'Не торгуем название' in full
assert len(soup.select('section.chapter')) == 13
assert len(soup.select('aside.design-note')) == 13
assert len(soup.select('table.data-table')) >= 5
assert not re.search(r'(?:file://|/home/|cache/documents)', html_text)

# Render every page and make a contact sheet for visual inspection.
doc = fitz.open(pdf)
thumbs = []
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(0.46, 0.46), alpha=False)
    im = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
    im.thumbnail((260, 370))
    card = Image.new('RGB', (274, 404), 'white')
    card.paste(im, ((274 - im.width) // 2, 25))
    ImageDraw.Draw(card).text((9, 8), str(i + 1), fill='black')
    thumbs.append(card)
cols = 4
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new('RGB', (cols * 274, rows * 404), (225, 228, 234))
for i, image in enumerate(thumbs):
    sheet.paste(image, ((i % cols) * 274, (i // cols) * 404))
contact = base / 'qa-contact-sheet.jpg'
sheet.save(contact, quality=90)
print(f'pages={len(reader.pages)} nonempty={sum(bool(t.strip()) for t in texts)} notes=13 tables={len(soup.select("table.data-table"))}')
print(contact)
