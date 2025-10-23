# -*- coding: utf-8 -*-
"""
PDF utilities

- Convert Markdown text to PDF, preferring HTML rendering via WeasyPrint.
- Falls back to a minimal ReportLab text renderer if WeasyPrint/markdown are not available.
"""
from __future__ import annotations

from typing import Optional
import os


def md_to_pdf(md_text: str, pdf_path: str) -> bool:
    """Render Markdown to PDF.

    Tries the following in order:
    1) markdown + weasyprint (HTML -> PDF)
    2) reportlab (plain text paragraphs)

    Returns True on success, False if no renderer is available or an error occurred.
    """
    # Option 1: markdown -> HTML -> WeasyPrint
    try:
        import markdown  # type: ignore
        from weasyprint import HTML  # type: ignore

        html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
        html = f"""
        <html>
          <head>
            <meta charset='utf-8'/>
            <style>
              body {{ font-family: Arial, Helvetica, sans-serif; font-size: 12pt; line-height: 1.5; }}
              h1, h2, h3 {{ color: #222; }}
              pre, code {{ font-family: Consolas, Menlo, monospace; font-size: 10pt; }}
              table {{ border-collapse: collapse; width: 100%; }}
              th, td {{ border: 1px solid #ddd; padding: 6px; }}
            </style>
          </head>
          <body>
            {html_body}
          </body>
        </html>
        """
        # Use base_url for local images (file paths)
        HTML(string=html, base_url=os.getcwd()).write_pdf(pdf_path)
        return True
    except Exception:
        pass

    # Option 2: ReportLab (very basic text rendering)
    try:
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  # type: ignore
        from reportlab.lib.units import mm  # type: ignore
        from reportlab.pdfbase import pdfmetrics  # type: ignore
        from reportlab.pdfbase.ttfonts import TTFont  # type: ignore

        doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        # Try to register a Korean-capable font (Windows: Malgun Gothic)
        font_path = os.getenv("PDF_FONT_PATH")
        if not font_path:
            for cand in [
                os.path.join(os.environ.get("WINDIR", r"C:\\Windows"), "Fonts", "malgun.ttf"),
                os.path.join(os.environ.get("WINDIR", r"C:\\Windows"), "Fonts", "malgunbd.ttf"),
            ]:
                if cand and os.path.isfile(cand):
                    font_path = cand
                    break
        if font_path and os.path.isfile(font_path):
            try:
                pdfmetrics.registerFont(TTFont("KFont", font_path))
                base_font = "KFont"
            except Exception:
                base_font = "Helvetica"
        else:
            base_font = "Helvetica"

        styles = getSampleStyleSheet()
        style = styles["BodyText"]
        style.fontName = base_font
        story = []
        for line in md_text.splitlines():
            story.append(Paragraph(line.replace("  ", "&nbsp;&nbsp;"), style))
            story.append(Spacer(1, 4))
        doc.build(story)
        return True
    except Exception:
        pass

    return False
