"""Build print-ready PDFs of the Persian documents.

    python scripts/build_pdf.py                 # -> paper.fa.pdf
    python scripts/build_pdf.py helper          # -> helper.pdf
    python scripts/build_pdf.py paper helper    # both

Pipeline: Markdown -> HTML (Python-Markdown; math kept for KaTeX) -> PDF printed by
headless Microsoft Edge -> page numbers stamped with pypdf/reportlab.
KaTeX and fonts are read from presentation/assets, so building works offline.
"""

import io
import re
import subprocess
import sys
from pathlib import Path

import markdown
from pymdownx import slugs
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
KATEX = "presentation/assets/katex"          # relative to the repository root (the HTML's <base>)

CSS = r"""
@font-face { font-family: "Vazirmatn"; src: url("presentation/assets/fonts/Vazirmatn-wght.woff2") format("woff2"); font-weight: 100 900; }
@font-face { font-family: "Plex Mono"; src: url("presentation/assets/fonts/ibm-plex-mono-500.woff2") format("woff2"); }
@page { size: A4; margin: 22mm 20mm 24mm 20mm; }
:root { --ink: #1a1d23; --muted: #5b6270; --rule: #d5d9e0; --accent: #1f4e79; --code-bg: #f2f3f5; --code-line: #cfd3da; --thm-bg: #f5f8fc; }
html { font-size: 10.5pt; }
body { font-family: "Vazirmatn", Tahoma, sans-serif; color: var(--ink); line-height: 1.95; margin: 0; text-align: justify; }
p { margin: 0 0 .7em; }
strong { font-weight: 700; }
a { color: var(--accent); text-decoration: none; }

/* title block */
h1 { font-size: 21pt; line-height: 1.5; text-align: center; color: var(--accent); margin: 0 0 14pt; font-weight: 800; text-wrap: balance; }
.authors { text-align: center; font-size: 10.5pt; line-height: 1.9; margin-bottom: 4pt; }
.authors p { margin: 0; text-align: center; }
.code-link { text-align: center; font-size: 9pt; color: var(--muted); }

h2 { font-size: 14.5pt; color: var(--accent); margin: 22pt 0 8pt; padding-bottom: 4pt; border-bottom: 1.2pt solid var(--accent); font-weight: 800; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14pt 0 6pt; font-weight: 700; break-after: avoid; }
hr { border: 0; border-top: .6pt solid var(--rule); margin: 14pt 0; }

/* abstract */
.abstract { background: var(--thm-bg); border: .6pt solid var(--rule); border-radius: 4pt; padding: 10pt 14pt; margin: 6pt 0 10pt; }
.abstract h2 { border: 0; margin: 0 0 4pt; padding: 0; font-size: 12pt; }

/* theorem-like blocks */
blockquote { margin: 10pt 0; padding: 8pt 12pt; background: var(--thm-bg); border-right: 3pt solid var(--accent); border-radius: 3pt; break-inside: avoid; }
blockquote p { margin: 0 0 .4em; }
blockquote p:last-child { margin-bottom: 0; }

/* code: always LTR, grey box */
pre { direction: ltr; text-align: left; unicode-bidi: isolate; background: var(--code-bg); border: .7pt solid var(--code-line); border-radius: 4pt; padding: 8pt 10pt; margin: 8pt 0 12pt; font-family: "Plex Mono", Consolas, "Courier New", monospace; font-size: 8.2pt; line-height: 1.5; white-space: pre-wrap; word-break: break-word; break-inside: avoid; }
pre code { background: none; border: 0; padding: 0; font-size: inherit; }
code { direction: ltr; unicode-bidi: isolate; font-family: "Plex Mono", Consolas, monospace; font-size: 8.6pt; background: var(--code-bg); border: .5pt solid var(--code-line); border-radius: 2pt; padding: 0 3pt; }

/* tables */
.tbl { overflow: hidden; margin: 8pt 0 12pt; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; font-size: 8.4pt; line-height: 1.55; }
th, td { border-bottom: .5pt solid var(--rule); padding: 3pt 5pt; text-align: center; vertical-align: middle; unicode-bidi: plaintext; }
thead th { background: #e9edf3; font-weight: 700; border-bottom: .9pt solid #9aa4b2; }
td:first-child, th:first-child { text-align: right; }
.ltr-table table, .ltr-table { direction: ltr; }
.ltr-table td:first-child, .ltr-table th:first-child { text-align: left; }
.ltr-table table { font-size: 7.4pt; }

/* figures */
p.figure { text-align: center; margin: 10pt 0 4pt; break-inside: avoid; break-after: avoid; }
p.figure img { max-width: 100%; max-height: 95mm; }
p.caption { font-size: 9pt; color: var(--muted); text-align: center; margin-bottom: 12pt; }

/* math */
.katex { direction: ltr; unicode-bidi: isolate; font-size: 1.05em; }
.katex-display { direction: ltr; margin: 8pt 0; overflow: hidden; }

/* references: LTR list */
.refs { direction: ltr; text-align: left; font-size: 8.6pt; line-height: 1.6; }
.refs ol { padding-left: 18pt; margin: 0; }
.refs li { margin-bottom: 3pt; }

ul, ol { padding-right: 18pt; padding-left: 0; margin: 0 0 .7em; }
li { margin-bottom: 3pt; }
h2, h3 { page-break-after: avoid; }
p.keep { break-after: avoid; page-break-after: avoid; font-weight: 500; }
p.ragged { text-align: right; }
.authors br + br { display: none; }

/* glossary entries (helper.md): "#### term : meaning" followed by a short explanation */
h4 { font-size: 10.6pt; font-weight: 700; color: var(--ink); margin: 11pt 0 2pt; padding-right: 8pt; border-right: 2.5pt solid var(--accent); line-height: 1.7; break-after: avoid; page-break-after: avoid; }
h4 + p { margin: 0 0 4pt; padding-right: 10.5pt; color: #2e333b; font-size: 9.8pt; }
h2 + p a, ol a { color: var(--accent); }
"""


def preprocess(md: str, paper: bool = True) -> str:
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)                 # authoring notes
    md = re.sub(r"</?div[^>]*>", "", md)                            # direction wrappers (CSS handles it)
    md = re.sub(r"</?details>|<summary>.*?</summary>", "", md)      # expand collapsibles
    if paper:
        # Author block (between the title and the first rule): keep each line on its own line.
        head, sep, rest = md.partition("\n---\n")
        title, _, authors = head.partition("\n\n")
        authors = "\n".join(l.rstrip() + "<br>" if l.strip() else l for l in authors.strip().splitlines())
        md = title + "\n\n" + authors + "\n" + sep + rest
    # Display math on a blockquote line must be its own paragraph for arithmatex.
    md = re.sub(r"^> \$\$(.*)\$\$\s*$", lambda m: ">\n> $$\n> " + m.group(1) + "\n> $$\n", md, flags=re.M)
    md = re.sub(r"^\$\$(.*)\$\$\s*$", lambda m: "\n$$\n" + m.group(1) + "\n$$\n", md, flags=re.M)
    # Latin labels ending in a neutral symbol keep their order inside Persian text.
    md = md.replace("DENSITY\\*", '<span dir="ltr">DENSITY*</span>')
    return md


def postprocess(html: str, paper: bool = True) -> str:
    if paper:
        # Title block: everything between the title and the first <hr> is the author block.
        html = re.sub(r"(</h1>)(.*?)(<hr\s*/?>)", lambda m: m.group(1) + '<div class="authors">' + m.group(2) + "</div>" + m.group(3),
                      html, count=1, flags=re.S)
    # Abstract box: from the abstract heading to the next <hr>.
    html = re.sub(r"(<h2[^>]*>چکیده</h2>.*?)(<hr\s*/?>)", r'<div class="abstract">\1</div>\2', html, count=1, flags=re.S)
    # Figures: a paragraph holding only an image, and the bold caption paragraph after it.
    html = re.sub(r"<p>(<img [^>]+>)</p>\s*<p>(<strong>شکل[^<]*</strong>.*?)</p>",
                  r'<p class="figure">\1</p><p class="caption">\2</p>', html, flags=re.S)
    # Tables: wrap; tables whose header row is English (appendix data dumps) are set LTR.
    def wrap(m):
        t = m.group(0)
        head = re.search(r"<thead>(.*?)</thead>", t, flags=re.S)
        persian = head and re.search(r"[\u0600-\u06FF]", head.group(1))
        return f'<div class="tbl{"" if persian else " ltr-table"}">{t}</div>'
    html = re.sub(r"<table>.*?</table>", wrap, html, flags=re.S)
    # Keep a caption or label paragraph on the same page as the table that follows it.
    html = re.sub(r"<p>((?:(?!</p>).)*)</p>(\s*<div class=\"tbl)", r'<p class="keep">\1</p>\2', html, flags=re.S)
    # Paragraphs with inline code: right-aligned instead of justified (long LTR tokens).
    html = re.sub(r"<p>((?:(?!</p>).)*<code>)", r'<p class="ragged">\1', html, flags=re.S)
    # References: the ordered list right after the references heading is LTR.
    html = re.sub(r"(<h2[^>]*>مراجع</h2>\s*)(<ol>.*?</ol>)", r'\1<div class="refs">\2</div>', html, count=1, flags=re.S)
    return html


def md_to_html(md: str, paper: bool = True) -> str:
    """Markdown -> HTML body. Math is left as \\( \\) / \\[ \\] for KaTeX; headings get
    GitHub-style Unicode ids so in-document links (e.g. a table of contents) work."""
    md = preprocess(md, paper)
    body = markdown.markdown(
        md, extensions=["tables", "fenced_code", "pymdownx.arithmatex", "toc"],
        extension_configs={"pymdownx.arithmatex": {"generic": True},
                           "toc": {"slugify": slugs.slugify(case="lower")}})
    return postprocess(body, paper)


DOCS = {
    "paper": dict(src="paper.fa.md", out="paper.fa.pdf", paper=True,
                  title="ایجنت چه چیزی را باید فراموش کند؟",
                  meta="What Should an Agent Forget? (Persian version)"),
    "helper": dict(src="helper.md", out="helper.pdf", paper=False,
                   title="راهنمای اصطلاحات، مخفف‌ها و فرمول‌های مقاله",
                   meta="Glossary: What Should an Agent Forget?"),
}


def build_html(doc: dict) -> Path:
    body = md_to_html((ROOT / doc["src"]).read_text(encoding="utf-8"), doc["paper"])
    html = ROOT / "build" / (Path(doc["src"]).stem + ".html")
    html.parent.mkdir(exist_ok=True)
    html.write_text(f"""<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><base href="../">
<title>{doc["title"]}</title>
<link rel="stylesheet" href="{KATEX}/katex.min.css">
<style>{CSS}</style></head><body>
{body}
<script src="{KATEX}/katex.min.js"></script>
<script src="{KATEX}/contrib/auto-render.min.js"></script>
<script>renderMathInElement(document.body, {{delimiters: [
  {{left: "\\\\[", right: "\\\\]", display: true}}, {{left: "\\\\(", right: "\\\\)", display: false}}],
  throwOnError: false}});</script>
</body></html>""", encoding="utf-8")
    return html


def print_pdf(html: Path, tmp: Path):
    subprocess.run([str(EDGE), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=30000", "--run-all-compositor-stages-before-draw",
                    f"--user-data-dir={ROOT / 'build' / 'edge-profile'}",
                    f"--print-to-pdf={tmp}", html.resolve().as_uri()],
                   check=True, capture_output=True, timeout=180)


def stamp_page_numbers(src: Path, dst: Path, meta_title: str):
    reader, writer = PdfReader(str(src)), PdfWriter()
    n = len(reader.pages)
    for i, page in enumerate(reader.pages, 1):
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(w, h))
        c.setFillColor(HexColor("#5b6270"))
        c.setFont("Helvetica", 8.5)
        c.drawCentredString(w / 2, 30, f"{i} / {n}")
        c.setStrokeColor(HexColor("#d5d9e0"))
        c.setLineWidth(.5)
        c.line(57, 44, w - 57, 44)
        c.save()
        buf.seek(0)
        page.merge_page(PdfReader(buf).pages[0])
        writer.add_page(page)
    writer.add_metadata({"/Title": meta_title, "/Author": "Amir Hossein Khalifeh, Mehdi Gholami"})
    with open(dst, "wb") as f:
        writer.write(f)
    return n


if __name__ == "__main__":
    for name in (sys.argv[1:] or ["paper"]):
        doc = DOCS[name]
        html = build_html(doc)
        tmp = ROOT / "build" / (Path(doc["out"]).stem + ".raw.pdf")
        print_pdf(html, tmp)
        out = ROOT / doc["out"]
        pages = stamp_page_numbers(tmp, out, doc["meta"])
        print(f"wrote {out} ({pages} pages)")
