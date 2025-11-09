import os
from pathlib import Path
from typing import Optional


def convert_html_dir_to_pdf(
    input_dir: str = "workspace/evagent/outputs",
    output_dir: Optional[str] = None,
    page_css: Optional[str] = None,
    overwrite: bool = True,
) -> list[tuple[Path, Path]]:
    """
    Convert all .html/.htm files in `input_dir` to PDF using WeasyPrint.
    
    Args:
        input_dir: Directory containing HTML files.
        output_dir: Where to place PDFs. Defaults to <input_dir>/pdf.
        page_css: Optional CSS string to control page size/margins.
                  If None, a sensible A4 margin preset is injected.
        overwrite: If False, skip files whose target PDF already exists.

    Returns:
        List of (html_path, pdf_path) for converted files.

    Requires:
        pip install weasyprint
        (Windows 환경에서 폰트/렌더링 이슈 시: MS 폰트 설치 또는 Noto 폰트 권장)
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError as e:
        raise RuntimeError(
            "WeasyPrint가 설치되어 있지 않습니다. `pip install weasyprint` 후 다시 실행하세요."
        ) from e

    in_dir = Path(input_dir).resolve()
    if not in_dir.exists():
        raise FileNotFoundError(f"입력 폴더가 없습니다: {in_dir}")

    out_dir = Path(output_dir).resolve() if output_dir else in_dir / "pdf"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 기본 페이지 CSS(A4, 여백, 페이지넘버 등)
    default_css = """
    @page {
      size: A4;
      margin: 18mm 16mm 20mm 16mm;
    }
    /* 페이지 하단 페이지 번호 */
    @page {
      @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 10px;
      }
    }
    /* 인쇄 미디어 최적화 */
    @media print {
      a { text-decoration: none; color: black; }
    }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans', 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif; }
    """

    css_to_use = page_css if page_css is not None else default_css
    css_objs = [CSS(string=css_to_use)]

    converted: list[tuple[Path, Path]] = []
    for html_path in sorted(in_dir.rglob("*")):
        if html_path.suffix.lower() not in {".html", ".htm"}:
            continue

        pdf_name = html_path.with_suffix(".pdf").name
        target_pdf = out_dir / pdf_name

        if target_pdf.exists() and not overwrite:
            continue

        # base_url을 HTML 파일 디렉토리로 설정해 상대 경로 자원(img/css/js)을 해석
        html_doc = HTML(filename=str(html_path), base_url=str(html_path.parent))
        html_doc.write_pdf(target_pdf, stylesheets=css_objs)
        converted.append((html_path, target_pdf))

    return converted


if __name__ == "__main__":
    results = convert_html_dir_to_pdf(
        input_dir="workspace/evagent/outputs",
        output_dir=None,        # 기본값: <입력>/pdf
        page_css=None,          # 기본 A4 CSS 사용
        overwrite=True          # 이미 있으면 덮어쓰기
    )
    print(f"Converted {len(results)} file(s):")
    for src, dst in results:
        print(f"- {src.name} -> {dst}")

