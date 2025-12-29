import os, uuid
import markdown2
import pdfkit

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def markdown_to_html(md_text: str) -> str:
    # simple, clean HTML from Markdown
    return markdown2.markdown(md_text, extras=["tables","fenced-code-blocks","strike"])

def html_to_pdf(html: str, filename_hint: str = "notes") -> str:
    # pick a deterministic-ish filename
    stem = f"{filename_hint}-{uuid.uuid4().hex[:8]}"
    html_path = os.path.join(DOWNLOAD_DIR, f"{stem}.html")
    pdf_path = os.path.join(DOWNLOAD_DIR, f"{stem}.pdf")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(_wrap_html(html))

    # find wkhtmltopdf
    wkhtml = os.getenv("WKHTMLTOPDF_PATH")
    cfg = pdfkit.configuration(wkhtmltopdf=wkhtml) if wkhtml else None

    # basic options; add margins for readability
    opts = {
        "quiet": "",
        "enable-local-file-access": "",
        "margin-top": "10mm",
        "margin-right": "10mm",
        "margin-bottom": "12mm",
        "margin-left": "10mm",
        "print-media-type": "",
        "dpi": 300
    }
    pdfkit.from_file(html_path, pdf_path, options=opts, configuration=cfg)
    return pdf_path

def _wrap_html(body: str) -> str:
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Study Notes</title>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; line-height: 1.5; color: #111; }}
    h1,h2,h3 {{ margin-top: 1.2em; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    ul {{ padding-left: 1.2em; }}
    .cite {{ color: #444; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""
