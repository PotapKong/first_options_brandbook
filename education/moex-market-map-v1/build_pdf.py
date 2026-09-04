from __future__ import annotations

import base64
import html
import re
from pathlib import Path

import markdown
from bs4 import BeautifulSoup
from weasyprint import HTML

ROOT = Path('/home/hughie/work/first_options_brandbook')
OUT = ROOT / 'education' / 'moex-market-map-v1'
MD_COPY = OUT / 'Первая_карта_российского_опционного_рынка_MO_обновлено.md'
SOURCE = MD_COPY
HTML_OUT = OUT / 'Первая_карта_российского_опционного_рынка_дизайн-макет.html'
PDF_OUT = OUT / 'Первая_карта_российского_опционного_рынка_дизайн-макет.pdf'

LOGO = ROOT / 'assets' / 'logo' / 'dual-delta-production.png'
PATTERN = ROOT / 'assets' / 'patterns' / 'scenario-field.png'
MANROPE = OUT / 'fonts' / 'Manrope-VariableFont_wght.ttf'
JETBRAINS = OUT / 'fonts' / 'JetBrainsMono-VariableFont_wght.ttf'

OUT.mkdir(parents=True, exist_ok=True)


def data_uri(path: Path) -> str:
    mime_by_suffix = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.ttf': 'font/ttf',
    }
    mime = mime_by_suffix[path.suffix.lower()]
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode('ascii')


raw = SOURCE.read_text(encoding='utf-8')
lines = raw.splitlines()
# Cover duplicates the document title, subtitle and metadata. Body starts at section 1.
body_start = next(i for i, line in enumerate(lines) if line.startswith('# 1. '))
body_md = '\n'.join(lines[body_start:])
body_html = markdown.markdown(
    body_md,
    extensions=['tables', 'fenced_code', 'sane_lists', 'attr_list'],
    output_format='html5',
)
soup = BeautifulSoup(body_html, 'html.parser')

# Stable anchors for the table of contents.
for idx, h1 in enumerate(soup.find_all('h1'), start=1):
    h1['id'] = f'section-{idx}'

# Remove markdown separators: chapter rhythm is controlled by the layout.
for hr in soup.find_all('hr'):
    hr.decompose()

# Wrap top-level sections to manage pagination and section headers.
for h1 in list(soup.find_all('h1')):
    section = soup.new_tag('section')
    section['class'] = ['chapter']
    h1.insert_before(section)
    node = h1
    while node:
        nxt = node.next_sibling
        if node is not h1 and getattr(node, 'name', None) == 'h1':
            break
        section.append(node.extract())
        node = nxt

# Semantic styling hooks.
for table in soup.find_all('table'):
    table['class'] = ['data-table']
for block in soup.find_all('blockquote'):
    block['class'] = ['key-quote']
for code in soup.find_all('code'):
    code['class'] = ['token']

# Internal design notes. They stay visible by request and are intentionally
# visually separate from student-facing content.
notes = {
    1: ('Роль разворота', 'Сразу отделить карту рынка от торговых сигналов. Образ: навигация и проверка маршрута, без свечей, ракет, быков и «золотых» обещаний.'),
    2: ('Ключевая схема', 'Собрать сравнение США / MOEX как развилку из двух колонок. Красным не пугать: ошибка здесь методическая, а не катастрофическая. Акцент — на действии «проверить контракт».'),
    3: ('Два мира', 'Фьючерсные опционы вести синим контуром, акционные — зелёным. Цвет помогает различать механику, но не заменяет подписи «маржируемый / премиальный» и «American / European».'),
    4: ('Данные и честность', 'Рядом с таблицей всегда держать дату среза. Не рисовать псевдостакан и не добавлять «живые» цифры вручную. Для финальной публикации — только реальный скрин выбранной серии.'),
    5: ('Инфографика OI ≠ ликвидность', 'Подойдёт простая связка: слева высокий OI как накопленный след, справа текущий bid/ask и сделки как проверка выхода. Не использовать объёмные 3D-графики и декоративные терминалы.'),
    6: ('Карточки серий', 'Каждую серию показывать одинаковым модулем: SECID → база → тип → лот → шаг → исполнение → expiry. Скриншоты ISS и стакана брать в один день и подписывать время.'),
    7: ('Чек-лист', 'Сделать эту страницу пригодной для печати и отдельной раздачи. Четыре блока A–D должны читаться без предыдущих глав; финальный стоп-сигнал выделить рамкой.'),
    8: ('Ошибки', 'Пять ошибок — не красная «стена запретов». Каждая карточка строится одинаково: заблуждение → механизм риска → проверяемое действие.'),
    9: ('Маршрут', 'Показать шесть шагов как последовательность с воротами контроля. Стратегия стоит последней, чтобы визуальная иерархия не возвращала ученика к американскому шаблону.'),
    10: ('Домашнее задание', 'Оставить реальные поля для заполнения от руки. Не ужимать таблицы ради количества страниц; пустое место здесь функционально.'),
    11: ('Сценарий для Сэма', 'Экранные материалы перечислены как производственный список. Все примеры рынка обновлять в день записи; устаревший стакан подписывать как исторический.'),
    12: ('Источники', 'URL и SECID набирать моноширинным шрифтом. В публичной версии можно добавить QR на MOEX ISS, но только после проверки конечной ссылки.'),
    13: ('Финальный кадр', 'Закончить одним правилом и шестью вопросами. Не добавлять CTA к покупке курса внутрь учебного вывода: здесь важнее закрепить процедуру проверки.'),
}
for idx, section in enumerate(soup.select('section.chapter'), start=1):
    title, text = notes[idx]
    aside = soup.new_tag('aside')
    aside['class'] = ['design-note']
    label = soup.new_tag('div')
    label['class'] = ['design-note-label']
    label.string = f'Комментарий дизайнеру · {idx:02d}'
    heading = soup.new_tag('strong')
    heading.string = title
    para = soup.new_tag('p')
    para.string = text
    aside.extend([label, heading, para])
    section.find('h1').insert_after(aside)

# Make the two architecture sections into clearly comparable cards.
for h2 in soup.find_all('h2'):
    text = h2.get_text(' ', strip=True)
    if text.startswith('Мир 1.'):
        h2['class'] = ['world-title', 'world-futures']
    elif text.startswith('Мир 2.'):
        h2['class'] = ['world-title', 'world-stocks']
    elif text.startswith('Ошибка '):
        h2['class'] = ['mistake-title']
    elif text.startswith('Задание '):
        h2['class'] = ['homework-title']

# Label dynamically changing market sections.
for h1 in soup.find_all('h1'):
    if h1.get_text(strip=True).startswith(('4.', '6.', '12.')):
        badge = soup.new_tag('span')
        badge['class'] = ['freshness-badge']
        badge.string = 'ДАННЫЕ МЕНЯЮТСЯ'
        h1.append(badge)

sections = ''.join(str(x) for x in soup.contents)

toc_items = [
    'Зачем этот материал ученику',
    'Главный слом мышления: MOEX ≠ американский рынок',
    'Два разных мира опционов MOEX',
    'Где на российском рынке сейчас есть жизнь',
    'Почему OI не равен ликвидности',
    'Разбор живых серий из карты',
    'Боевой чек-лист перед любой сделкой',
    'Типовые ошибки новичка на MOEX',
    'Практический маршрут ученика',
    'Домашнее задание для ученика',
    'Формат урока для Сэма',
    'Где проверять данные',
    'Финальная рамка для ученика',
]
toc = ''.join(
    f'<li><a href="#section-{i}"><span>{i:02d}</span>{html.escape(title)}</a></li>'
    for i, title in enumerate(toc_items, start=1)
)

css = f"""
@font-face {{ font-family: Manrope; src: url('{data_uri(MANROPE)}') format('truetype'); font-weight: 200 800; }}
@font-face {{ font-family: JetBrains; src: url('{data_uri(JETBRAINS)}') format('truetype'); font-weight: 100 800; }}
@page {{
  size: A4;
  margin: 18mm 16mm 17mm 16mm;
  @top-left {{ content: 'ПЕРВЫЙ ОПЦИОННЫЙ · УЧЕБНЫЙ МАТЕРИАЛ'; font: 600 7.5pt JetBrains; color: #5f6b82; letter-spacing: .08em; }}
  @top-right {{ content: 'MOEX · 04.09.2026'; font: 600 7.5pt JetBrains; color: #5f6b82; }}
  @bottom-left {{ content: 'Не является торговой рекомендацией'; font: 500 7pt Manrope; color: #7d8799; }}
  @bottom-right {{ content: counter(page); font: 700 8pt JetBrains; color: #0b1020; }}
}}
@page cover {{ margin: 0; @top-left {{ content: none }} @top-right {{ content: none }} @bottom-left {{ content: none }} @bottom-right {{ content: none }} }}
@page front {{ margin: 18mm 16mm; @top-left {{ content: none }} @top-right {{ content: none }} @bottom-left {{ content: none }} }}
@page closing {{ margin: 0; @top-left {{ content: none }} @top-right {{ content: none }} @bottom-left {{ content: none }} @bottom-right {{ content: none }} }}

:root {{
  --navy: #071022; --navy2: #0d1833; --ink: #101827; --muted: #647086;
  --paper: #f6f8fc; --white: #ffffff; --line: #dce3ef;
  --blue: #1768ff; --blue2: #0b46b8; --green: #1fce69; --green2: #0d8b49;
  --note: #ff754a; --note-bg: #fff4ef;
}}
* {{ box-sizing: border-box; }}
html {{ font-family: Manrope, sans-serif; color: var(--ink); font-size: 9.4pt; line-height: 1.52; }}
body {{ margin: 0; background: var(--paper); }}
a {{ color: inherit; text-decoration: none; }}

.cover {{ page: cover; height: 297mm; padding: 22mm 18mm 18mm; color: white; position: relative; overflow: hidden; background: var(--navy); }}
.cover::before {{ content: ''; position: absolute; inset: 0; background: url('{data_uri(PATTERN)}') center/cover no-repeat; opacity: .25; }}
.cover::after {{ content: ''; position: absolute; inset: 0; background: linear-gradient(125deg, rgba(7,16,34,.20), rgba(7,16,34,.92) 68%); }}
.cover-inner {{ position: relative; z-index: 2; height: 100%; display: flex; flex-direction: column; }}
.cover-kicker {{ font: 700 8pt JetBrains; color: var(--green); letter-spacing: .13em; margin-bottom: 25mm; }}
.cover h1 {{ margin: 0; width: 138mm; font-size: 35pt; line-height: 1.03; letter-spacing: -.035em; }}
.cover .subtitle {{ width: 126mm; margin-top: 9mm; font-size: 15pt; line-height: 1.32; color: #dce7ff; }}
.cover .rule {{ width: 76mm; height: 1.2mm; margin-top: 11mm; background: linear-gradient(90deg,var(--blue) 0 51%,var(--green) 51%); border-radius: 2mm; }}
.cover-logo {{ position: absolute; right: 0; bottom: 22mm; width: 58mm; border-radius: 8mm; box-shadow: 0 12px 42px rgba(0,0,0,.35); }}
.cover-meta {{ margin-top: auto; width: 112mm; display: grid; grid-template-columns: 1fr 1fr; gap: 4mm 8mm; font: 550 8pt JetBrains; color: #afbdd8; }}
.cover-meta b {{ display: block; margin-bottom: 1.5mm; color: white; font-family: Manrope; font-size: 8.6pt; }}
.cover-status {{ position: absolute; right: 0; top: 0; border: .25mm solid rgba(255,117,74,.6); color: #ffb59e; border-radius: 99px; padding: 2.2mm 4mm; font: 700 7pt JetBrains; letter-spacing: .06em; }}

.front {{ page: front; break-before: page; min-height: 250mm; }}
.front h2 {{ font-size: 24pt; margin: 0 0 8mm; }}
.front-lead {{ font-size: 11.2pt; max-width: 150mm; color: #354056; }}
.toc {{ list-style: none; padding: 0; margin: 12mm 0 0; columns: 2; column-gap: 10mm; }}
.toc li {{ break-inside: avoid; margin: 0 0 4.1mm; }}
.toc a {{ display: grid; grid-template-columns: 10mm 1fr; gap: 2.5mm; align-items: baseline; border-bottom: .2mm solid var(--line); padding-bottom: 2mm; }}
.toc span {{ font: 700 8pt JetBrains; color: var(--green2); }}
.legend {{ margin-top: 10mm; background: var(--note-bg); border-left: 1.2mm solid var(--note); padding: 5mm; border-radius: 0 3mm 3mm 0; }}
.legend strong {{ color: #a83517; }}

main {{ counter-reset: chapter; }}
.chapter {{ break-before: page; counter-increment: chapter; }}
.chapter > h1 {{ margin: 0 0 5mm; font-size: 23pt; line-height: 1.08; letter-spacing: -.025em; color: var(--navy); padding-right: 28mm; position: relative; }}
.chapter > h1::before {{ content: 'РАЗДЕЛ ' counter(chapter, decimal-leading-zero); display: block; margin-bottom: 3mm; font: 750 7.5pt JetBrains; color: var(--green2); letter-spacing: .08em; text-transform: uppercase; }}
.chapter h2 {{ margin: 7mm 0 3mm; font-size: 14pt; line-height: 1.2; color: #14254a; break-after: avoid; }}
.chapter h3 {{ margin: 5mm 0 2.5mm; font-size: 10pt; text-transform: uppercase; letter-spacing: .055em; color: var(--green2); break-after: avoid; }}
p {{ margin: 0 0 3mm; orphans: 3; widows: 3; }}
ul, ol {{ margin: 2mm 0 4mm; padding-left: 6mm; }}
li {{ margin: 0 0 1.6mm; }}
li::marker {{ color: var(--blue); font-weight: 800; }}
strong {{ font-weight: 750; }}

.design-note {{ break-inside: avoid; margin: 0 0 6mm; padding: 4mm 5mm; border: .35mm dashed #f29a7e; background: var(--note-bg); border-radius: 3mm; color: #5a2919; }}
.design-note-label {{ margin-bottom: 1.5mm; font: 750 7pt JetBrains; text-transform: uppercase; letter-spacing: .09em; color: #c64a25; }}
.design-note strong {{ display: block; margin-bottom: 1mm; font-size: 10pt; color: #8f2c11; }}
.design-note p {{ margin: 0; font-size: 8.4pt; line-height: 1.4; }}
.freshness-badge {{ display: inline-block; vertical-align: middle; margin-left: 3mm; padding: 1.2mm 2.2mm; border-radius: 99px; background: #fff0eb; color: #b83e1b; font: 750 6.5pt JetBrains; letter-spacing: .04em; }}

.key-quote {{ break-inside: avoid; margin: 5mm 0; padding: 5mm 6mm 5mm 7mm; border: 0; border-left: 1.5mm solid var(--green); border-radius: 0 3mm 3mm 0; background: #eefaf3; color: #0b5130; font-size: 11pt; line-height: 1.42; }}
.key-quote p {{ margin: 0; }}
.token {{ font: 650 .88em JetBrains; color: #0b46b8; background: #eef3ff; border: .2mm solid #d7e2ff; padding: .3mm 1mm; border-radius: 1.2mm; white-space: nowrap; }}

.data-table {{ width: 100%; margin: 4mm 0 6mm; border-collapse: separate; border-spacing: 0; font-size: 8.1pt; line-height: 1.34; border: .25mm solid var(--line); border-radius: 2.5mm; overflow: hidden; }}
.data-table thead {{ display: table-header-group; }}
.data-table tr {{ break-inside: avoid; }}
.data-table th {{ padding: 2.8mm 3mm; background: var(--navy2); color: white; font: 700 7.4pt JetBrains; text-align: left; vertical-align: bottom; }}
.data-table td {{ padding: 2.6mm 3mm; border-top: .2mm solid var(--line); vertical-align: top; }}
.data-table tbody tr:nth-child(even) td {{ background: #f1f5fb; }}
.data-table th:nth-child(n+3), .data-table td:nth-child(n+3) {{ font-variant-numeric: tabular-nums; }}

.world-title {{ padding: 3.2mm 4mm; border-radius: 2.5mm; color: white !important; }}
.world-futures {{ background: linear-gradient(90deg,var(--blue2),var(--blue)); }}
.world-stocks {{ background: linear-gradient(90deg,var(--green2),var(--green)); }}
.mistake-title {{ padding: 3mm 4mm; background: #f2f5fb; border-left: 1.2mm solid var(--blue); border-radius: 0 2mm 2mm 0; }}
.homework-title {{ padding: 3mm 4mm; background: #eefaf3; border-left: 1.2mm solid var(--green); border-radius: 0 2mm 2mm 0; }}
.chapter:nth-child(3) {{ font-size: 8.7pt; line-height: 1.40; }}
.chapter:nth-child(3) h2 {{ margin: 4mm 0 2mm; font-size: 12.5pt; }}
.chapter:nth-child(3) ul {{ margin-bottom: 2.5mm; }}
.chapter:nth-child(3) li {{ margin-bottom: .9mm; }}
.chapter:nth-child(3) .design-note {{ padding: 3mm 4mm; margin-bottom: 4mm; }}
.chapter:nth-child(3) .key-quote {{ margin: 3mm 0; padding: 3.5mm 5mm; font-size: 9.8pt; }}
.chapter:nth-of-type(7) ol {{ columns: 1; }}
.chapter:nth-of-type(10) .data-table td:last-child {{ min-width: 60mm; height: 8mm; }}
.chapter:nth-of-type(10) .data-table {{ font-size: 8.4pt; }}

.production-footer {{ page: closing; break-before: page; background: var(--navy); color: #dce7ff; padding: 24mm 18mm; height: 297mm; display: flex; flex-direction: column; justify-content: center; }}
.production-footer h2 {{ margin: 0 0 6mm; color: white; font-size: 24pt; }}
.production-footer .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; }}
.production-footer .card {{ border: .25mm solid #24385f; border-radius: 3mm; padding: 5mm; background: #0d1833; }}
.production-footer .num {{ color: var(--green); font: 750 8pt JetBrains; }}
.production-footer p {{ margin: 1.5mm 0 0; }}
.small {{ font-size: 8pt; color: #8490a5; }}
"""

html_doc = f"""<!doctype html>
<html lang="ru">
<head><meta charset="utf-8"><title>Первая карта российского опционного рынка — дизайн-макет</title><style>{css}</style></head>
<body>
<section class="cover">
  <div class="cover-inner">
    <div class="cover-status">РЕДАКЦИОННО-ДИЗАЙНЕРСКИЙ МАКЕТ · V1</div>
    <div class="cover-kicker">ОПЦИОНЫ С НУЛЯ · MOEX · 2026</div>
    <h1>Первая карта российского опционного рынка</h1>
    <div class="subtitle">Где искать сделки, что проверять и какие американские правила здесь не работают</div>
    <div class="rule"></div>
    <div class="cover-meta">
      <div><b>Проект</b>Михалыч × Сэм Шарипов</div>
      <div><b>Рынок</b>Российские опционы / MOEX</div>
      <div><b>Исходный срез</b>03.09.2026 · 20:44 МСК</div>
      <div><b>Контрольная сверка</b>04.09.2026</div>
    </div>
    <img class="cover-logo" src="{data_uri(LOGO)}" alt="Фирменный знак проекта">
  </div>
</section>

<section class="front">
  <h2>Как читать этот макет</h2>
  <p class="front-lead">Ученический текст сохранён по последней обновлённой версии. Оранжевые блоки — служебные дизайнерские комментарии: они задают смысл визуала, требования к реальным рыночным данным и ограничения против декоративной «финтех-мишуры».</p>
  <ol class="toc">{toc}</ol>
  <div class="legend"><strong>Статус:</strong> макет с комментариями. Перед публичной выдачей ученикам служебные блоки можно скрыть отдельной сборкой, не меняя основной текст.</div>
</section>

<main>{sections}</main>

<section class="production-footer">
  <div class="num">ПРОИЗВОДСТВЕННЫЙ ЧЕК · 04 ПУНКТА</div>
  <h2>Перед финальной ученической версией</h2>
  <div class="grid">
    <div class="card"><b>01 · Обновить рынок</b><p>Переснять стакан, сделки, OI и ГО в день записи или публикации.</p></div>
    <div class="card"><b>02 · Проверить контракт</b><p>Сверить SECID, базовый актив, лот, UNIT, шаг, тип исполнения и expiry.</p></div>
    <div class="card"><b>03 · Убрать служебный слой</b><p>Скрыть оранжевые комментарии только после того, как визуальные задачи реализованы и проверены.</p></div>
    <div class="card"><b>04 · Прогнать QA</b><p>Проверить переносы таблиц, читаемость кода, номера страниц, ссылки и отсутствие выдуманных рыночных данных.</p></div>
  </div>
  <p class="small" style="margin-top:12mm">Учебный материал. Не является индивидуальной инвестиционной рекомендацией.</p>
</section>
</body></html>"""

HTML_OUT.write_text(html_doc, encoding='utf-8')
HTML(filename=str(HTML_OUT), base_url=str(OUT)).write_pdf(str(PDF_OUT))
print(PDF_OUT)
