"""Generate presentation/helper.html (the glossary page) from helper.md.

    python scripts/build_helper_page.py

Re-run after editing helper.md. The page is static and works offline: fonts and KaTeX
are read from presentation/assets.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pdf import ROOT, md_to_html  # noqa: E402

SRC = ROOT / "helper.md"
OUT = ROOT / "presentation" / "helper.html"


def main():
    body = md_to_html(SRC.read_text(encoding="utf-8"), paper=False)
    # Each glossary entry ("#### term : meaning" + explanation) becomes one searchable block.
    body = re.sub(r"(<h4[^>]*>.*?</h4>)(\s*<p>.*?</p>)?",
                  lambda m: f'<article class="entry">{m.group(1)}{m.group(2) or ""}</article>',
                  body, flags=re.S)
    # The paper link in the intro points to the repository file, one level up.
    body = body.replace('href="paper.fa.md"', 'href="../paper.fa.md"')
    n = body.count('class="entry"')
    OUT.write_text(f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>راهنمای اصطلاحات مقاله</title>
<link rel="stylesheet" href="assets/katex/katex.min.css">
<link rel="stylesheet" href="glossary.css">
</head>
<body>
<header class="bar">
  <a class="back" href="index.html">→ بازگشت به ارائه</a>
  <label class="search" for="q"><span>جستجو</span>
    <input id="q" type="search" placeholder="مثلاً LRU، کوله‌پشتی یا φ" autocomplete="off">
  </label>
  <span class="count" id="count">{n} مدخل</span>
</header>
<main class="doc" id="doc">
{body}
<p class="empty" id="empty" hidden>موردی پیدا نشد. عبارت دیگری را امتحان کنید.</p>
</main>
<script src="assets/katex/katex.min.js"></script>
<script src="assets/katex/contrib/auto-render.min.js"></script>
<script src="glossary.js"></script>
</body>
</html>
""", encoding="utf-8")
    print(f"wrote {OUT} ({n} entries)")


if __name__ == "__main__":
    main()
