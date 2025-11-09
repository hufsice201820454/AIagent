# -*- coding: utf-8 -*-
"""
ReportWriterAgent - OEM별 개별 보고서 생성
"""
from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional, TypedDict

# 추가: 일괄 변환 유틸 불러오기
try:
    from evagent.tools.convert_html_dir_to_pdf import (
        convert_html_dir_to_pdf as _batch_convert_html_dir_to_pdf,
    )
except Exception:
    _batch_convert_html_dir_to_pdf = None  # 선택적 의존성

_HAS_LANGCHAIN = False
try:
    from langchain_openai import ChatOpenAI
    _HAS_LANGCHAIN = True
except Exception:
    pass


def _outputs_dir() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(base_dir, "..", "outputs"))
    return os.path.abspath(out)


def _file_uri(p: str) -> str:
    ap = os.path.abspath(p)
    return "file:///" + ap.replace("\\", "/")


# ===== 프롬프트 =====
PROMPT_SYSTEM = """당신은 전문 시장 분석 보고서 작성자입니다.

중요 규칙:
1. 표(Table) 사용 필수: 수치 데이터는 반드시 표로 정리 (Markdown 코드블록 금지)
2. 출처 표기: 모든 데이터에 (Tech), (ESG), (Stock), (JIT), (ValueChain) 명시
3. 섹션 번호 정확히: 3.1, 3.2, 4.0, 4.1 형식 준수, 섹션 5와 6 반드시 포함
4. 이미지 마커: [이미지:설명] 형식으로 표시
5. 한국어 사용, 과장/추측 금지. 제공된 데이터만 근거로 작성
6. 코드블록 출력 금지. 순수 본문만 출력
"""

PROMPT_USER_TEMPLATE = """전기차 시장 분석 보고서 본문을 작성하세요.

# 입력 데이터
{data_summary}

# 대상 회사
{target_company}

# 출력 구조

## 1. 전기차 시장 트렌드 분석 레포트

## 2. 요약 (Executive Summary)
- 5-7문장으로 핵심 내용 요약
- 주요 수치와 출처 명시

## 3. 시장 분석

### 3.1 전기차 산업 개요
- 4-6문단으로 글로벌 시장 현황 서술

### 3.2 정부 ESG 정책
표 형식으로 정리

### 3.3 글로벌 생산 거점 분석
[이미지:지도] 글로벌 OEM & 공급사 위치
JIT 관점 분석 (2-3문단)

### 3.4 소결
3.1~3.3 핵심 내용 3-4줄 정리

## 4. 개별 OEM 분석

### 4.0 협력사 주식 근황
[이미지:배터리] 배터리 공급사 가격 지수
[이미지:HVAC] HVAC 공급사 가격 지수
(2-3문단 해설)

### 4.1 {target_company} 분석

#### 4.1.1 공급망 경쟁력 (JIT)
표 형식

#### 4.1.2 Value Chain 위치
66km/140km 이내 공급사 개수

#### 4.1.3 기술 수준
표 형식 (TRL, MRL, OTA, ISSB, Materiality, CRAAP)

#### 4.1.4 주가 동향
표 형식
[이미지:주가] {target_company} 주가 차트 (90일)

#### 4.1.5 ESG 대응
표 형식

#### 4.1.6 종합 평가
강점/약점 및 종합 점수

## 5. 종합 결론

### 5.1 현재 시장 상황
### 5.2 미래 전망
### 5.3 종합 순위
표 형식
### 5.4 최종 결론

## 6. Appendix
참조 자료 목록

---
체크리스트:
- [ ] 모든 수치는 표 형식
- [ ] 섹션 4.0에 배터리/HVAC 차트
- [ ] 섹션 4.1.4에 {target_company} 주가 차트
- [ ] 출처 표기 누락 없음
- [ ] 5장, 6장 반드시 생성
"""


def _compose_user_prompt(summary: Dict[str, Any], images: Dict[str, Any], target_company: str) -> str:
    """프롬프트 조합"""
    def dumps(x: Any) -> str:
        return json.dumps(x, ensure_ascii=False, indent=2)
    
    tech = summary.get("tech", {}) or {}
    esg = summary.get("esg", {}) or {}
    valuechain = summary.get("valuechain", {}) or {}
    stock = summary.get("stock", {}) or {}

    # 해당 회사만 필터링
    filtered_tech = tech.get(target_company, {}) if isinstance(tech, dict) else {}
    filtered_valuechain = {target_company: valuechain.get(target_company, {})} if isinstance(valuechain, dict) else {}
    filtered_stock = {target_company: stock.get(target_company, {})} if isinstance(stock, dict) else {}
    filtered_esg = {target_company: esg.get(target_company, {})} if isinstance(esg, dict) else {}

    # config에서 전체 OEM 리스트
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "config", "allowed_companies.json")
    all_oems = []
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_oems = [c["name"] for c in data.get("companies", []) if c.get("category") == "OEM"]
        except Exception:
            pass

    data_summary = f"""
## 분석 대상
전체 OEM: {dumps(all_oems)}
이번 보고서 대상: {target_company}

## 전체 데이터 개요
- ValueChain: {dumps(summary.get("valuechain", {}))}
- ESG: {dumps(summary.get("esg", {}))}
- Stock: {dumps(summary.get("stock", {}))}
- Tech: {dumps(summary.get("tech", {}))}

## {target_company} 상세 데이터
- ValueChain: {dumps(filtered_valuechain)}
- ESG: {dumps(filtered_esg)}
- Stock: {dumps(filtered_stock)}
- Tech: {dumps(filtered_tech)}

## 사용 가능 이미지
- 지도: {images.get("map", "없음")}
- 배터리: {images.get("battery_chart", "없음")}
- HVAC: {images.get("hvac_chart", "없음")}
- {target_company} 주가: {images.get("oem_charts_by_company", {}).get(target_company, "없음")}
"""
    
    return PROMPT_USER_TEMPLATE.format(
        data_summary=data_summary,
        target_company=target_company
    )


def _collect_images(summary: Dict[str, Any]) -> Dict[str, Any]:
    """이미지 수집"""
    import glob
    out_dir = _outputs_dir()
    out: Dict[str, Any] = {}
    
    # 지도
    map_png = os.path.join(out_dir, "map_oem_suppliers.png")
    out["map"] = _file_uri(map_png) if os.path.isfile(map_png) else ""
    
    # 배터리/HVAC
    battery_files = glob.glob(os.path.join(out_dir, "stock_Battery_merged_*.png"))
    hvac_files = glob.glob(os.path.join(out_dir, "stock_HVAC_merged_*.png"))
    out["battery_chart"] = _file_uri(battery_files[-1]) if battery_files else ""
    out["hvac_chart"] = _file_uri(hvac_files[-1]) if hvac_files else ""
    
    # OEM 차트
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "config", "allowed_companies.json")
    ticker_map = {}
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for c in data.get("companies", []):
                if c.get("category") == "OEM":
                    ticker_map[c["name"]] = c["ticker"]
        except Exception:
            pass
    
    oem_charts = {}
    oem_files = glob.glob(os.path.join(out_dir, "stock_OEM_*_*.png"))
    for filepath in oem_files:
        filename = os.path.basename(filepath)
        parts = filename.split("_")
        if len(parts) >= 3:
            ticker = parts[2]
            company_name = next((name for name, t in ticker_map.items() if t == ticker), None)
            if company_name:
                oem_charts[company_name] = _file_uri(filepath)
    
    out["oem_charts_by_company"] = oem_charts
    return out


def _text_to_html(text: str, images: Dict[str, Any]) -> str:
    """LLM 텍스트를 HTML로 변환"""
    lines = text.splitlines()
    html_lines: List[str] = []
    buf: List[str] = []

    def flush_table():
        nonlocal buf
        if not buf:
            return
        try:
            rows = []
            for ln in buf:
                cells = [c.strip() for c in ln.strip().strip('|').split('|')]
                rows.append(cells)
            header = rows[0]
            body = rows[2:] if len(rows) > 2 else []
            html_lines.append('<table class="tbl">')
            html_lines.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in header) + '</tr></thead>')
            if body:
                html_lines.append('<tbody>')
                for r in body:
                    html_lines.append('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>')
                html_lines.append('</tbody>')
            html_lines.append('</table>')
        except Exception:
            for ln in buf:
                html_lines.append(f'<p>{ln}</p>')
        buf = []

    def img_tag(kind: str, current_company: Optional[str] = None) -> str:
        src = ''
        if '지도' in kind:
            src = images.get('map', '')
        elif '배터리' in kind:
            src = images.get('battery_chart', '')
        elif 'HVAC' in kind or '공조' in kind:
            src = images.get('hvac_chart', '')
        elif '주가' in kind and current_company:
            src = images.get('oem_charts_by_company', {}).get(current_company, '')
            if not src:
                print(f"[WARNING] OEM 차트 누락: {current_company}")
        return f'<img alt="{kind}" src="{src}" style="max-width: 100%; height: auto; margin: 10px 0;" />' if src else ''

    current_company = None
    
    for raw in lines:
        ln = raw.strip()
        if not ln:
            flush_table()
            html_lines.append('<br/>')
            continue
        
        # 회사명 추적
        if ln.startswith('### 4.1') and '분석' in ln:
            match = re.search(r"^###\s+4\.1\s+(.+?)\s+분석", ln)
            if match:
                company_candidate = match.group(1).strip()
                oem_list = list(images.get('oem_charts_by_company', {}).keys())
                if company_candidate in oem_list:
                    current_company = company_candidate
                    print(f"[INFO] 회사 섹션: {current_company}")
                else:
                    for oem in oem_list:
                        if oem in company_candidate or company_candidate in oem:
                            current_company = oem
                            print(f"[INFO] 회사 섹션 (매칭): {current_company}")
                            break
        
        if ln.startswith('|'):
            buf.append(ln)
            continue
        else:
            flush_table()

        if ln.startswith('#### '):
            html_lines.append(f'<h4>{ln[5:]}</h4>')
        elif ln.startswith('### '):
            html_lines.append(f'<h3>{ln[4:]}</h3>')
        elif ln.startswith('## '):
            html_lines.append(f'<h2>{ln[3:]}</h2>')
        elif ln.startswith('# '):
            html_lines.append(f'<h1>{ln[2:]}</h1>')
        elif '[이미지:' in ln or '[그림:' in ln:
            kind = ln.replace('[이미지:', '').replace('[그림:', '').replace(']', '').strip()
            tag = img_tag(kind, current_company)
            if tag:
                html_lines.append(tag)
        else:
            html_lines.append(f'<p>{ln}</p>')

    flush_table()

    css = """
    <style>
      body { 
        font-family: 'Malgun Gothic', Arial, sans-serif; 
        line-height: 1.6; 
        max-width: 1200px; 
        margin: 0 auto; 
        padding: 20px;
        color: #333;
      }
      h1, h2, h3, h4 { margin: 1em 0 0.5em; color: #222; }
      h1 { font-size: 2em; border-bottom: 3px solid #333; padding-bottom: 10px; }
      h2 { font-size: 1.6em; border-bottom: 2px solid #666; padding-bottom: 8px; margin-top: 1.5em; }
      h3 { font-size: 1.3em; color: #444; margin-top: 1.2em; }
      h4 { font-size: 1.1em; color: #555; margin-top: 1em; }
      p { margin: 0.5em 0; }
      .tbl { 
        border-collapse: collapse; 
        margin: 1em 0; 
        width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      }
      .tbl th, .tbl td { 
        border: 1px solid #ddd; 
        padding: 8px 12px; 
        text-align: left;
      }
      .tbl th { background-color: #f5f5f5; font-weight: bold; }
      .tbl tr:nth-child(even) { background-color: #fafafa; }
      .titlepage { 
        text-align: center; 
        margin: 60px 0 40px;
        padding: 40px 0;
        border-bottom: 3px solid #333;
      }
      .subtitle { color: #666; }
      img { 
        max-width: 100%; 
        height: auto;
        display: block;
        margin: 15px auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      }
    </style>
    """
    
    title_page = """
      <div class="titlepage">
        <h2 style="color: #666;">AI Market Intelligence</h2>
        <h1>EV Market Trend Analysis Report</h1>
        <h3 class="subtitle">전기차 시장 동향 분석 보고서</h3>
        <h4 class="subtitle">AI-Driven Multi-Agent Analysis System</h4>
      </div>
    """
    
    head = f"<head><meta charset='utf-8'><title>EV Market Report</title>{css}</head>"
    body = "\n".join([title_page] + html_lines)
    return f"<!DOCTYPE html><html lang='ko'>{head}<body>{body}</body></html>"


def _render_html(text: str, images: Dict[str, Any], html_path: str) -> str:
    """HTML 파일 생성"""
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    html = _text_to_html(text, images)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[HTML] ✓ {os.path.basename(html_path)}")
    return html_path


def _html_to_pdf_weasyprint(html_path: str, pdf_path: str) -> bool:
    """사용 중지(WeasyPrint 제거 경로). 항상 False 반환."""
    return False


def _html_to_pdf_pyhtml2pdf(html_path: str, pdf_path: str) -> bool:
    """pyhtml2pdf 기반 HTML→PDF 변환 (직접 변환)

    요구 사항:
      - pip install pyhtml2pdf
      - 내부적으로 wkhtmltopdf가 필요할 수 있음
    """
    try:
        from pyhtml2pdf import converter  # type: ignore
    except Exception:
        print("[PDF] pyhtml2pdf 미설치")
        return False

    try:
        file_url = _file_uri(html_path)
        converter.convert(file_url, pdf_path)
        print(f"[PDF] ✓ pyhtml2pdf: {os.path.basename(pdf_path)}")
        return True
    except Exception as e:
        print(f"[PDF] pyhtml2pdf 실패: {str(e)[:100]}")
        return False


def _html_to_pdf_pdfkit(html_path: str, pdf_path: str) -> bool:
    """wkhtmltopdf 기반 pdfkit 변환 (대안 경로)

    요구 사항:
      - wkhtmltopdf 설치 (시스템 PATH에 포함)
        다운로드: https://wkhtmltopdf.org/downloads.html
      - pip install pdfkit
    """
    try:
        import pdfkit  # type: ignore
    except Exception:
        print("[PDF] pdfkit 미설치")
        return False


def _html_to_image_imgkit(html_path: str, img_path: str) -> bool:
    """wkhtmltoimage 기반 imgkit 변환 (HTML -> 이미지)

    요구 사항:
      - wkhtmltoimage 설치 (시스템 PATH 포함)
        다운로드: https://wkhtmltopdf.org/downloads.html
      - pip install imgkit
    """
    try:
        import imgkit  # type: ignore
    except Exception:
        print("[IMG] imgkit 미설치")
        return False


def _image_to_pdf_reportlab(img_path: str, pdf_path: str) -> bool:
    """이미지(PNG/JPG)를 단일 페이지 PDF로 저장 (ReportLab 사용)"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.units import mm
    except Exception:
        print("[PDF] ReportLab 미설치")
        return False


def _html_to_pdf_playwright(html_path: str, pdf_path: str) -> bool:
    """Playwright(Chromium)으로 HTML → PDF 변환.

    요구 사항:
      - pip install playwright
      - playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        print("[PDF] playwright 미설치")
        return False

    file_url = _file_uri(html_path)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            page = context.new_page()
            page.goto(file_url, wait_until="load")
            page.emulate_media(media="print")
            page.pdf(
                path=pdf_path,
                format="A4",
                margin={"top": "18mm", "right": "16mm", "bottom": "20mm", "left": "16mm"},
                print_background=True,
            )
            browser.close()
        print(f"[PDF] ✓ playwright: {os.path.basename(pdf_path)}")
        return True
    except Exception as e:
        print(f"[PDF] playwright 실패: {str(e)[:120]}")
        return False

    try:
        c = canvas.Canvas(pdf_path, pagesize=A4)
        page_w, page_h = A4

        img = ImageReader(img_path)
        iw, ih = img.getSize()

        # 여백 설정
        margin = 15 * mm
        max_w = page_w - 2 * margin
        max_h = page_h - 2 * margin

        # 비율 유지 스케일
        scale = min(max_w / iw, max_h / ih)
        draw_w = iw * scale
        draw_h = ih * scale
        x = (page_w - draw_w) / 2
        y = (page_h - draw_h) / 2

        c.drawImage(img, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True, anchor='c')
        c.showPage()
        c.save()
        print(f"[PDF] ✓ from image: {os.path.basename(pdf_path)}")
        return True
    except Exception as e:
        print(f"[PDF] 이미지→PDF 실패: {str(e)[:100]}")
        return False

    # 기본 옵션: 전체 페이지 스크린샷, 고해상도
    options = {
        'enable-local-file-access': None,  # 플래그형 옵션은 None 지정
        'width': 0,                        # 내용 너비에 맞춤
        'quality': 92,
        'format': 'png',
        'disable-smart-width': '',
        'encoding': 'UTF-8',
    }

    # wkhtmltoimage 경로 환경변수 지원
    config = None
    try:
        wkhtmltoimage_path = os.environ.get('WKHTMLTOIMAGE')
        if wkhtmltoimage_path and os.path.isfile(wkhtmltoimage_path):
            config = imgkit.config(wkhtmltoimage=wkhtmltoimage_path)
    except Exception:
        config = None

    try:
        if config:
            imgkit.from_file(html_path, img_path, options=options, config=config)
        else:
            imgkit.from_file(html_path, img_path, options=options)
        print(f"[IMG] ✓ imgkit: {os.path.basename(img_path)}")
        return True
    except Exception as e:
        print(f"[IMG] imgkit 실패: {str(e)[:100]}")
        return False

    # Windows에서 로컬 파일 접근 허용 옵션 필요
    options = {
        'enable-local-file-access': True,
        'encoding': 'UTF-8',
        'quiet': ''
    }

    # wkhtmltopdf 경로 자동 탐색(선택적)
    config = None
    try:
        wkhtmltopdf_path = os.environ.get('WKHTMLTOPDF')
        if wkhtmltopdf_path and os.path.isfile(wkhtmltopdf_path):
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    except Exception:
        config = None

    try:
        if config:
            pdfkit.from_file(html_path, pdf_path, options=options, configuration=config)
        else:
            pdfkit.from_file(html_path, pdf_path, options=options)
        print(f"[PDF] ✓ pdfkit: {os.path.basename(pdf_path)}")
        return True
    except Exception as e:
        print(f"[PDF] pdfkit 실패: {str(e)[:100]}")
        return False


def _html_to_pdf_reportlab(html_path: str, pdf_path: str) -> bool:
    """ReportLab으로 HTML을 PDF로 변환 (간단한 버전)"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from bs4 import BeautifulSoup
        
        # 한글 폰트 등록
        font_registered = False
        try:
            windir = os.environ.get("WINDIR", "C:\\Windows")
            font_paths = [
                os.path.join(windir, "Fonts", "malgun.ttf"),
                os.path.join(windir, "Fonts", "malgunbd.ttf"),
                "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            ]
            for font_path in font_paths:
                if os.path.isfile(font_path):
                    pdfmetrics.registerFont(TTFont("KoreanFont", font_path))
                    font_registered = True
                    break
        except Exception:
            pass
        
        base_font = "KoreanFont" if font_registered else "Helvetica"
        
        # HTML 읽기
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # PDF 문서 생성
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=20*mm,
            rightMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
        )
        
        # 스타일 정의
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=base_font,
            fontSize=24,
            textColor=colors.HexColor('#222222'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        h2_style = ParagraphStyle(
            'CustomH2',
            parent=styles['Heading2'],
            fontName=base_font,
            fontSize=18,
            textColor=colors.HexColor('#444444'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        h3_style = ParagraphStyle(
            'CustomH3',
            parent=styles['Heading3'],
            fontName=base_font,
            fontSize=14,
            textColor=colors.HexColor('#555555'),
            spaceAfter=10,
            spaceBefore=15
        )
        
        h4_style = ParagraphStyle(
            'CustomH4',
            parent=styles['Heading4'],
            fontName=base_font,
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=8,
            spaceBefore=10
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontName=base_font,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#333333')
        )
        
        story = []
        
        # 제목 페이지
        story.append(Spacer(1, 40*mm))
        story.append(Paragraph("EV Market Trend Analysis Report", title_style))
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph("전기차 시장 동향 분석 보고서", h2_style))
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("AI-Driven Multi-Agent Analysis System", body_style))
        story.append(PageBreak())
        
        # 본문 처리
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'table']):
            if element.name == 'h1':
                story.append(Paragraph(element.get_text(), title_style))
            elif element.name == 'h2':
                if len(story) > 5:  # 제목 페이지 이후
                    story.append(PageBreak())
                story.append(Paragraph(element.get_text(), h2_style))
            elif element.name == 'h3':
                story.append(Paragraph(element.get_text(), h3_style))
            elif element.name == 'h4':
                story.append(Paragraph(element.get_text(), h4_style))
            elif element.name == 'p':
                text = element.get_text().strip()
                if text and not text.startswith('[이미지'):
                    story.append(Paragraph(text, body_style))
                    story.append(Spacer(1, 3*mm))
            elif element.name == 'table':
                # 테이블 데이터 추출
                rows = []
                for tr in element.find_all('tr'):
                    cells = []
                    for td in tr.find_all(['th', 'td']):
                        cells.append(td.get_text().strip())
                    if cells:
                        rows.append(cells)
                
                if rows:
                    # 테이블 생성
                    t = Table(rows, repeatRows=1)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), base_font),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('FONTNAME', (0, 1), (-1, -1), base_font),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')])
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 5*mm))
        
        # PDF 생성
        doc.build(story)
        print(f"[PDF] ✓ ReportLab: {os.path.basename(pdf_path)}")
        return True
        
    except ImportError:
        print("[PDF] ReportLab 미설치: pip install reportlab beautifulsoup4")
        return False
    except Exception as e:
        print(f"[PDF] ReportLab 실패: {str(e)[:100]}")
        return False


# ===== LangGraph 노드 =====
class ReportState(TypedDict):
    supervisor_results: Optional[Dict[str, Any]]
    summary: Optional[Dict[str, Any]]
    images: Optional[Dict[str, Any]]
    target_company: Optional[str]
    user_prompt: Optional[str]
    llm_text: Optional[str]
    html_path: Optional[str]
    pdf_path: Optional[str]
    error: Optional[str]


def validate_inputs(state: ReportState) -> ReportState:
    new = state.copy()
    supervisor_results = state.get("supervisor_results", {})
    
    if not supervisor_results:
        new["error"] = "No supervisor results"
        return new
    
    new["summary"] = {
        "inputs": {
            "companies": supervisor_results.get("companies", []),
            "regions": supervisor_results.get("regions", [])
        },
        "tech": supervisor_results.get("tech_results", {}),
        "valuechain": supervisor_results.get("valuechain_results", {}),
        "stock": supervisor_results.get("stock_results", {}),
        "esg": supervisor_results.get("esg_results", {}),
        "run_id": "report_001"
    }
    return new


def collect_images_node(state: ReportState) -> ReportState:
    new = state.copy()
    summary = state.get("summary", {})
    new["images"] = _collect_images(summary)
    
    print(f"\n[Images] 수집:")
    oem_charts = new['images'].get('oem_charts_by_company', {})
    print(f"  - OEM 차트: {len(oem_charts)}개")
    for company, path in oem_charts.items():
        print(f"    • {company}")
    return new


def compose_prompt_node(state: ReportState) -> ReportState:
    new = state.copy()
    summary = state.get("summary", {})
    images = state.get("images", {})
    target_company = state.get("target_company", "")
    
    if not summary or not target_company:
        new["error"] = "Missing data"
        return new
    
    new["user_prompt"] = _compose_user_prompt(summary, images, target_company)
    print(f"[Prompt] {target_company} ({len(new['user_prompt'])} chars)")
    return new


def call_llm_node(state: ReportState) -> ReportState:
    new = state.copy()
    user_prompt = state.get("user_prompt", "")
    
    if not user_prompt or not _HAS_LANGCHAIN:
        new["error"] = "LLM unavailable"
        return new
    
    try:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0.3, max_tokens=4000)
        
        print(f"[LLM] 호출 중...")
        response = llm.invoke(f"{PROMPT_SYSTEM}\n\n{user_prompt}")
        text = getattr(response, "content", "") or str(response)
        
        if not text:
            new["error"] = "Empty LLM response"
            return new
        
        print(f"[LLM] 완료 ({len(text)} chars)")
        new["llm_text"] = text
        
    except Exception as e:
        print(f"[LLM] 실패: {e}")
        new["error"] = str(e)
    
    return new


def render_html_node(state: ReportState) -> ReportState:
    new = state.copy()
    text = state.get("llm_text", "")
    images = state.get("images", {})
    summary = state.get("summary", {})
    target_company = state.get("target_company", "manual")
    
    if not text:
        new["error"] = "No text to render"
        return new
    
    run_id = summary.get("run_id", "manual")
    safe_company = target_company.replace(" ", "_").replace("/", "_")
    html_path = os.path.join(_outputs_dir(), f"report_{run_id}_{safe_company}.html")
    
    try:
        new["html_path"] = _render_html(text, images, html_path)
    except Exception as e:
        new["error"] = str(e)
    
    return new


def convert_html_to_pdf_node(state: ReportState) -> ReportState:
    new = state.copy()
    html_path = state.get("html_path")
    summary = state.get("summary", {})
    target_company = state.get("target_company", "manual")
    
    if not html_path or not os.path.isfile(html_path):
        new["error"] = "No HTML file"
        return new
    
    run_id = summary.get("run_id", "manual")
    safe_company = target_company.replace(" ", "_").replace("/", "_")
    pdf_path = os.path.join(_outputs_dir(), f"report_{run_id}_{safe_company}.pdf")

    # HTML → PDF: Playwright(Chromium) 사용
    if _html_to_pdf_playwright(html_path, pdf_path):
        new["pdf_path"] = pdf_path
        return new

    # 최후의 수단(선택): 이미지→PDF 파이프라인
    tmp_img_path = os.path.join(_outputs_dir(), f"report_{run_id}_{safe_company}.png")
    if _html_to_image_imgkit(html_path, tmp_img_path) and _image_to_pdf_reportlab(tmp_img_path, pdf_path):
        new["pdf_path"] = pdf_path
        return new

    new["error"] = "PDF conversion failed: install playwright and 'playwright install chromium'"
    return new


def compile_report_graph():
    """LangGraph 그래프"""
    from langgraph.graph import StateGraph
    
    graph = StateGraph(ReportState)
    graph.add_node("validate", validate_inputs)
    graph.add_node("collect_images", collect_images_node)
    graph.add_node("compose_prompt", compose_prompt_node)
    graph.add_node("call_llm", call_llm_node)
    graph.add_node("render_html", render_html_node)
    graph.add_node("convert_pdf", convert_html_to_pdf_node)

    # HTML -> Image(리포트별) 노드
    def convert_html_to_image_node(state: ReportState) -> ReportState:
        new = state.copy()
        html_path = state.get("html_path")
        summary = state.get("summary", {})
        target_company = state.get("target_company", "manual")

        if not html_path or not os.path.isfile(html_path):
            return new

        run_id = summary.get("run_id", "manual")
        safe_company = target_company.replace(" ", "_").replace("/", "_")
        img_path = os.path.join(_outputs_dir(), f"report_{run_id}_{safe_company}.png")

        if _html_to_image_imgkit(html_path, img_path):
            new["img_path"] = img_path
        return new

    # 추가: 출력 폴더 내 HTML 일괄 PDF 변환 노드
    def convert_outputs_dir_node(state: ReportState) -> ReportState:
        try:
            out_dir = _outputs_dir()
            # 일괄: HTML → PDF (Playwright)
            for root, _, files in os.walk(out_dir):
                for name in sorted(files):
                    if not name.lower().endswith(('.html', '.htm')):
                        continue
                    html_path = os.path.join(root, name)
                    pdf_path = os.path.join(out_dir, os.path.splitext(name)[0] + '.pdf')
                    if not _html_to_pdf_playwright(html_path, pdf_path):
                        print("[PDF] 배치 변환 실패: playwright/chromium 확인 필요")
        except Exception as e:
            print(f"[PDF] batch convert 실패: {e}")
        return state

    graph.add_node("convert_outputs_dir", convert_outputs_dir_node)
    graph.add_node("convert_html_to_image", convert_html_to_image_node)

    # 추가: 출력 폴더 내 HTML -> 이미지 일괄 변환
    def convert_outputs_dir_images_node(state: ReportState) -> ReportState:
        try:
            # 의존성 미설치 상황에서도 파이프라인 지속
            from evagent.tools.convert_html_dir_to_image import convert_html_dir_to_image  # type: ignore
        except Exception:
            print("[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)")
            return state

        try:
            out_dir = _outputs_dir()
            convert_html_dir_to_image(
                input_dir=out_dir,
                output_dir=None,
                overwrite=True,
                format="png",
            )
        except Exception as e:
            print(f"[IMG] batch convert 실패: {e}")
        return state

    graph.add_node("convert_outputs_dir_images", convert_outputs_dir_images_node)
    
    graph.set_entry_point("validate")
    graph.add_edge("validate", "collect_images")
    graph.add_edge("collect_images", "compose_prompt")
    graph.add_edge("compose_prompt", "call_llm")
    graph.add_edge("call_llm", "render_html")
    graph.add_edge("render_html", "convert_pdf")
    graph.add_edge("convert_pdf", "convert_html_to_image")
    graph.add_edge("convert_html_to_image", "convert_outputs_dir")
    graph.add_edge("convert_outputs_dir", "convert_outputs_dir_images")
    
    return graph.compile()


def run_report_writer(supervisor_results: Dict[str, Any]) -> Dict[str, Any]:
    """모든 OEM별 보고서 생성"""
    
    # OEM 목록
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                               "config", "allowed_companies.json")
    all_oems = []
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_oems = [c["name"] for c in data.get("companies", []) if c.get("category") == "OEM"]
        except Exception:
            pass
    
    if not all_oems:
        return {"error": "No OEM list"}
    
    compiled = compile_report_graph()
    results = []
    
    print(f"\n{'='*60}")
    print(f"총 {len(all_oems)}개 OEM 보고서 생성")
    print(f"{'='*60}\n")
    
    for idx, company in enumerate(all_oems, 1):
        print(f"\n[{idx}/{len(all_oems)}] {company}")
        
        init_state: ReportState = {
            "supervisor_results": supervisor_results,
            "summary": None,
            "images": None,
            "target_company": company,
            "user_prompt": None,
            "llm_text": None,
            "html_path": None,
            "pdf_path": None,
            "error": None,
        }
        
        try:
            final_state = compiled.invoke(init_state)
            
            result = {
                "company": company,
                "html_path": final_state.get("html_path"),
                "pdf_path": final_state.get("pdf_path"),
                "error": final_state.get("error"),
            }
            results.append(result)
            
            if result.get("error"):
                print(f"  ✗ 실패: {result['error']}")
        
        except Exception as e:
            print(f"  ✗ 예외: {e}")
            results.append({
                "company": company,
                "html_path": None,
                "pdf_path": None,
                "error": str(e),
            })
    
    # 최종 요약
    print("\n" + "="*60)
    print("보고서 생성 완료")
    print("="*60)
    
    success = sum(1 for r in results if not r.get("error"))
    failed = len(results) - success
    
    print(f"성공: {success}개 / 실패: {failed}개")
    
    if success > 0:
        print("\n생성된 보고서:")
        for r in results:
            if not r.get("error") and r.get("pdf_path"):
                print(f"  • {r['company']}: {os.path.basename(r['pdf_path'])}")
    
    print("="*60 + "\n")
    
    return {
        "total": len(results),
        "success": success,
        "failed": failed,
        "results": results
    }


if __name__ == "__main__":
    dummy = {
        "companies": ["Tesla", "BYD"],
        "regions": ["USA", "China"],
        "tech_results": {},
        "valuechain_results": {},
        "stock_results": {},
        "esg_results": {},
    }
    
    result = run_report_writer(dummy)
    print("\n테스트 완료:", result)
