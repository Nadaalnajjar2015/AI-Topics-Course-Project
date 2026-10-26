"""Build the team guide PDFs from the Markdown sources in this folder.

Usage (from this folder):  python build_pdfs.py
Needs: pip install markdown, and Microsoft Edge (or set BROWSER to a Chrome path).
"""
import os
import subprocess
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent
BROWSER = os.environ.get(
    "BROWSER", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Calibri, Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #15252c; }
h1, h2, h3, h4 { color: #0b5f56; line-height: 1.25; page-break-after: avoid; }
h1 { font-size: 22pt; margin: 0 0 6pt; }
h2 { font-size: 15pt; border-bottom: 2px solid #cfe3df; padding-bottom: 3pt; margin-top: 22pt; }
h3 { font-size: 12.5pt; margin-top: 16pt; }
h4 { font-size: 11pt; margin-top: 12pt; color: #15252c; }
p, li { orphans: 3; widows: 3; }
ul, ol { padding-left: 20pt; }
li { margin: 2pt 0; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.2pt; background: #eef4f4; padding: 0 3px; border-radius: 3px; }
pre { background: #f2f6f6; border: 1px solid #d4e0e0; border-radius: 6px; padding: 8pt 10pt; font-size: 8.8pt; line-height: 1.4; white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: inherit; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0; font-size: 9.5pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background: #0b5f56; color: #fff; text-align: left; padding: 5pt 6pt; }
td { border-bottom: 1px solid #d4e0e0; padding: 4pt 6pt; vertical-align: top; }
tr:nth-child(even) td { background: #f6fafa; }
blockquote { margin: 10pt 0; padding: 8pt 12pt; background: #fff6e5; border-left: 4px solid #d08a00; border-radius: 4px; page-break-inside: avoid; }
blockquote p { margin: 2pt 0; }
.cover { border: 2px solid #0b5f56; border-radius: 10px; padding: 18pt 20pt; margin-bottom: 18pt; background: #f2f9f8; }
.cover .eyebrow { font-size: 9pt; letter-spacing: .12em; text-transform: uppercase; color: #0b5f56; font-weight: 600; }
.cover h1 { margin-top: 6pt; }
.cover .sub { font-size: 12pt; color: #3c5058; margin: 4pt 0 10pt; }
.cover table { margin-top: 10pt; }
.toc { border: 1px solid #d4e0e0; border-radius: 6px; padding: 8pt 14pt; margin: 10pt 0 14pt; font-size: 9.8pt; }
.toc ul { padding-left: 14pt; margin: 2pt 0; }
.toc > ul { padding-left: 4pt; list-style: none; }
.toc a { color: #15252c; text-decoration: none; }
.pb { page-break-before: always; }
a { color: #0b5f56; }
"""

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>{css}</style></head><body>{body}</body></html>"""


def build(md_path: Path) -> Path:
    text = md_path.read_text(encoding="utf-8")
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "toc", "sane_lists", "md_in_html", "attr_list"],
        extension_configs={"toc": {"toc_depth": "2-2", "title": "Contents"}},
    )
    body = md.convert(text)
    title = md_path.stem
    html_path = HERE / f"_{md_path.stem}.html"
    html_path.write_text(TEMPLATE.format(title=title, css=CSS, body=body), encoding="utf-8")
    pdf_path = OUT_DIR / f"{md_path.stem}.pdf"
    subprocess.run(
        [
            BROWSER, "--headless", "--disable-gpu", "--no-pdf-header-footer",
            "--print-to-pdf-no-header", f"--print-to-pdf={pdf_path}", html_path.as_uri(),
        ],
        check=True, capture_output=True,
    )
    html_path.unlink()
    return pdf_path


if __name__ == "__main__":
    targets = sys.argv[1:] or sorted(p.name for p in HERE.glob("[0-9][0-9]-*.md"))
    for name in targets:
        print("built", build(HERE / name))
