import os
from pathlib import Path
from typing import Optional, Literal


def convert_html_dir_to_image(
    input_dir: str = "workspace/evagent/outputs",
    output_dir: Optional[str] = None,
    overwrite: bool = True,
    format: Literal["png", "jpg", "jpeg"] = "png",
) -> list[tuple[Path, Path]]:
    """
    Convert all .html/.htm files in `input_dir` to images using imgkit/wkhtmltoimage.

    Requires:
      - pip install imgkit
      - wkhtmltoimage installed and accessible via PATH or `WKHTMLTOIMAGE` env var
    """
    try:
        import imgkit  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "imgkit가 설치되어 있지 않습니다. `pip install imgkit` 후 다시 실행하세요."
        ) from e

    in_dir = Path(input_dir).resolve()
    if not in_dir.exists():
        raise FileNotFoundError(f"입력 폴더가 없습니다: {in_dir}")

    out_dir = Path(output_dir).resolve() if output_dir else in_dir / format
    out_dir.mkdir(parents=True, exist_ok=True)

    options = {
        'enable-local-file-access': None,
        'quality': 92,
        'format': format,
        'encoding': 'UTF-8',
        'disable-smart-width': '',
    }

    # wkhtmltoimage 경로 환경변수 처리(선택)
    config = None
    try:
        wkhtmltoimage_path = os.environ.get('WKHTMLTOIMAGE')
        if wkhtmltoimage_path and os.path.isfile(wkhtmltoimage_path):
            config = imgkit.config(wkhtmltoimage=wkhtmltoimage_path)
    except Exception:
        config = None

    converted: list[tuple[Path, Path]] = []
    for html_path in sorted(in_dir.rglob("*")):
        if html_path.suffix.lower() not in {".html", ".htm"}:
            continue

        img_name = html_path.with_suffix(f".{format}").name
        target_img = out_dir / img_name

        if target_img.exists() and not overwrite:
            continue

        try:
            if config:
                imgkit.from_file(str(html_path), str(target_img), options=options, config=config)
            else:
                imgkit.from_file(str(html_path), str(target_img), options=options)
            converted.append((html_path, target_img))
        except Exception as e:
            print(f"[IMG] 변환 실패: {html_path.name}: {str(e)[:100]}")

    return converted


if __name__ == "__main__":
    results = convert_html_dir_to_image(
        input_dir="workspace/evagent/outputs",
        output_dir=None,
        overwrite=True,
        format="png",
    )
    print(f"Converted {len(results)} file(s):")
    for src, dst in results:
        print(f"- {src.name} -> {dst}")

