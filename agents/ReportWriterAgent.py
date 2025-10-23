# -*- coding: utf-8 -*-
"""
ReportWriterAgent - Fixed: OEM charts placement + table formatting
"""
from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List, Optional, TypedDict

_HAS_LANGCHAIN = False
try:
    from langchain_openai import ChatOpenAI
    _HAS_LANGCHAIN = True
except Exception:
    pass

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _outputs_dir() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(base_dir, "..", "outputs"))
    return os.path.abspath(out)


def _file_uri(p: str) -> str:
    ap = os.path.abspath(p)
    return "file:///" + ap.replace("\\", "/")


# ===== 개선된 프롬프트 (표 형식 + 구조화) =====
PROMPT_SYSTEM = """당신은 전문 시장 분석 보고서 작성자입니다.

중요 규칙:
1. **표(Table) 사용 필수**: 수치 데이터는 반드시 표로 정리
2. **출처 표기**: 모든 데이터에 (Tech), (ESG), (Stock), (JIT), (ValueChain) 명시
3. **섹션 번호 정확히**: 3.1, 3.2, 4.1.1, 4.1.2 형식 준수
4. **이미지 마커**: [이미지:설명] 형식으로 표시
5. **한국어 사용**
"""

PROMPT_USER_TEMPLATE = """전기차 시장 분석 보고서 본문을 작성하세요.

# 입력 데이터
{data_summary}

# 출력 구조 (정확히 따를 것)

## 1. 전기차 시장 트렌드 분석 레포트

## 2. 요약 (Executive Summary)
- 5-7문장으로 핵심 내용 요약
- 주요 수치와 출처 명시
- 예: "2024년 글로벌 EV 시장은 35% 성장 (Stock)"

## 3. 시장 분석

### 3.1 전기차 산업 개요
- 4-6문단으로 글로벌 시장 현황 서술
- 생산, 판매, 기술 동향 포괄
- 제공된 데이터 기반 (추측 금지)

### 3.2 정부 ESG 정책
표 형식으로 정리:
국가 | 목표연도 | 주요 정책
한국 | 2050 | ...
중국 | 2060 | ...
(각 국가별 2-3줄 해설)

### 3.3 글로벌 생산 거점 분석
[이미지:지도] 글로벌 OEM & 공급사 위치

JIT 관점 분석 (2-3문단):
- 주요 OEM의 공급사 근접도 (ValueChain)
- 지역 분산 리스크 평가 (JIT)

### 3.4 소결
3.1~3.3 핵심 내용 3-4줄 정리

## 4. 개별 OEM 분석

**다음 형식을 모든 OEM에 반복 적용:**

### 4.X [회사명] 분석

#### 4.X.1 공급망 경쟁력 (JIT)
표 형식:
항목 | 점수 | 해석
JIT Score | XX점 (JIT) | ...
Regional Score | XX점 (JIT) | ...

#### 4.X.2 Value Chain 위치
- 66km 이내 공급사: XX개 (ValueChain)
- 140km 이내 공급사: XX개 (ValueChain)

#### 4.X.3 기술 수준
표 형식:
지표 | 점수 | 만점
TRL | X | 9
MRL | X | 10
OTA Compliance | X | 5
ISSB | X | 5
Materiality | X | 5
CRAAP | X | 5
(종합 평가 2-3줄)

#### 4.X.4 주가 동향
표 형식:
항목 | 수치 | 출처
90일 변화율 | XX% | (Stock)
시가총액 | $XXB | (Stock)
P/E Ratio | XX | (Stock)

**[중요] 해당 회사의 주가 차트 삽입:**
[이미지:주가] [회사명] 주가 차트 (90일)

**협력사 차트 삽입:**
[이미지:배터리] 배터리 공급사 가격 지수
[이미지:HVAC] HVAC 공급사 가격 지수

#### 4.X.5 ESG 대응
표 형식:
항목 | 내용 | 출처
탄소중립 목표 | 20XX년 | (ESG)
Scope 1/2 감축 | XX% | (ESG)
Scope 3 대응 | ... | (ESG)
MSCI 등급 | XX | (ESG)
CDP 점수 | X | (ESG)

#### 4.X.6 종합 평가
- 강점/약점 요약 (2-3줄)
- 종합 점수: XX점 (산정 기준 명시)

---

## 5. 종합 결론

### 5.1 현재 시장 상황
- ValueChain + Stock 분석 종합
- OEM-공급사 관계, 주요 섹터 모멘텀 (3-4문단)

### 5.2 미래 전망
- ESG 목표 기반 시장 방향성
- 정부 정책 영향 분석 (3-4문단)

### 5.3 종합 순위
표 형식:
순위 | OEM | 종합점수 | 주요 근거
1 | XXX | 88 | JIT 상위, ESG A등급, 90일 +XX% (Stock)
2 | XXX | 85 | ...
(산정 기준: Stock 변화율, JIT Score, Tech 평균, ESG 등급 정규화 후 평균)

### 5.4 최종 결론
- 시장 현황/전망/순위 통합 메시지 (3-4줄)

## 6. Appendix
- 참조 OEM 웹사이트 목록
- GHG Protocol: https://ghgprotocol.org/corporate-standard
- 사용 데이터 파일 목록

---

**중요 체크리스트:**
- [ ] 모든 수치 데이터는 표 형식
- [ ] 각 회사 4.X.4에 해당 회사 주가 차트 삽입
- [ ] 섹션 번호 정확히 (4.1, 4.2, 4.3...)
- [ ] 이미지 마커는 [이미지:유형] 형식
- [ ] 출처 표기 누락 없음"""


def _compose_user_prompt(summary: Dict[str, Any], images: Dict[str, Any]) -> str:
    """프롬프트 조합"""
    def dumps(x: Any) -> str:
        return json.dumps(x, ensure_ascii=False, indent=2)
    
    # 데이터 요약 생성
    data_summary = f"""
## 분석 대상
{dumps(summary.get("inputs", {}))}

## ValueChain 분석
{dumps(summary.get("valuechain", {}))}

## ESG 분석
{dumps(summary.get("esg", {}))}

## 주가 분석
{dumps(summary.get("stock", {}))}

## 기술 분석 (회사별)
{dumps(summary.get("tech", {}))}

## 사용 가능한 이미지
- 지도: {images.get("map", "없음")}
- 배터리 차트: {images.get("battery_chart", "없음")}
- HVAC 차트: {images.get("hvac_chart", "없음")}
- OEM 주가 차트: {len(images.get("oem_charts", []))}개 (각 회사 섹션에 배치)
"""
    
    return PROMPT_USER_TEMPLATE.format(data_summary=data_summary)


def _collect_images(summary: Dict[str, Any]) -> Dict[str, Any]:
    """이미지 수집 + 회사별 차트 매핑"""
    import glob
    out_dir = _outputs_dir()
    out: Dict[str, Any] = {}
    
    # 1. 지도
    map_png = os.path.join(out_dir, "map_oem_suppliers.png")
    out["map"] = _file_uri(map_png) if os.path.isfile(map_png) else ""
    
    # 2. 배터리/HVAC 차트
    battery_files = glob.glob(os.path.join(out_dir, "stock_Battery_merged_*.png"))
    hvac_files = glob.glob(os.path.join(out_dir, "stock_HVAC_merged_*.png"))
    out["battery_chart"] = _file_uri(battery_files[-1]) if battery_files else ""
    out["hvac_chart"] = _file_uri(hvac_files[-1]) if hvac_files else ""
    
    # 3. OEM 개별 차트 (회사명-티커 매핑)
    oem_charts_by_company = {}
    
    # allowed_companies.json에서 티커 매핑 로드
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
    
    # 파일명에서 티커 추출 (stock_OEM_TSLA_20241023_153045.png)
    oem_files = glob.glob(os.path.join(out_dir, "stock_OEM_*_*.png"))
    for filepath in oem_files:
        filename = os.path.basename(filepath)
        # stock_OEM_TSLA_... → TSLA 추출
        parts = filename.split("_")
        if len(parts) >= 3:
            ticker = parts[2]
            # 티커 → 회사명 역매핑
            company_name = next((name for name, t in ticker_map.items() if t == ticker), None)
            if company_name:
                oem_charts_by_company[company_name] = _file_uri(filepath)
    
    out["oem_charts"] = []  # 리스트 대신 dict 사용
    out["oem_charts_by_company"] = oem_charts_by_company
    
    return out


def _register_font() -> str:
    """한글 폰트 등록"""
    try:
        font_candidates = [
            (os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "malgun.ttf"), "Malgun Gothic"),
            (os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "gulim.ttc"), "Gulim"),
        ]
        
        for path, name in font_candidates:
            if os.path.isfile(path):
                pdfmetrics.registerFont(TTFont("KFont", path))
                return "KFont"
        
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
        return "HeiseiKakuGo-W5"
        
    except Exception:
        return "Helvetica"


def _render_pdf(text: str, images: Dict[str, Any], pdf_path: str) -> str:
    """PDF 렌더링 (개선: 회사별 차트 배치)"""
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    base_font = _register_font()
    
    # 한글 폰트 적용
    for style_name in ["BodyText", "Heading1", "Heading2", "Heading3", "Title"]:
        styles[style_name].fontName = base_font
    
    story: List[Any] = []
    
    # 제목
    story.append(Paragraph("전기차 시장 트렌드 분석 레포트", styles["Title"]))
    story.append(Spacer(1, 12))
    
    # 현재 섹션 추적 (회사별 차트 삽입용)
    current_company = None
    current_section = None
    
    oem_charts_by_company = images.get("oem_charts_by_company", {})
    
    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 2))
            continue
        
        # 섹션 감지
        if re.match(r"^###?\s+4\.\d+\s+(.+?)\s+분석", stripped):
            # 예: "### 4.1 Tesla 분석"
            match = re.search(r"^###?\s+4\.\d+\s+(.+?)\s+분석", stripped)
            if match:
                current_company = match.group(1).strip()
                current_section = None
        
        if re.match(r"^####\s+4\.\d+\.\d+", stripped):
            # 예: "#### 4.1.4 주가 동향"
            match = re.search(r"^####\s+4\.\d+\.(\d+)", stripped)
            if match:
                current_section = int(match.group(1))
        
        # 이미지 삽입 감지
        if "[이미지:" in stripped or "[그림:" in stripped:
            # 일반 이미지 (지도, 배터리, HVAC)
            if "지도" in stripped or "OEM & 공급사" in stripped:
                _add_image(story, styles, "[그림] 글로벌 OEM & 공급사 위치", images.get("map", ""))
            elif "배터리" in stripped:
                _add_image(story, styles, "[그림] 배터리 공급사 차트", images.get("battery_chart", ""))
            elif "HVAC" in stripped or "공조" in stripped:
                _add_image(story, styles, "[그림] HVAC 공급사 차트", images.get("hvac_chart", ""))
            elif "주가" in stripped and current_company:
                # 회사별 주가 차트 삽입
                chart_uri = oem_charts_by_company.get(current_company, "")
                if chart_uri:
                    _add_image(story, styles, f"[그림] {current_company} 주가 차트 (90일)", chart_uri, width_mm=140)
                else:
                    print(f"[PDF] 경고: {current_company} 주가 차트 없음")
            continue
        
        # 일반 텍스트
        try:
            para = Paragraph(stripped, styles["BodyText"])
            story.append(para)
            story.append(Spacer(1, 4))
        except Exception as e:
            print(f"[PDF] 텍스트 렌더링 실패: {e}")
            continue
    
    # PDF 빌드
    try:
        doc.build(story)
        print(f"[PDF] ✓ 빌드 성공: {pdf_path}")
    except Exception as e:
        print(f"[PDF] ✗ 빌드 실패: {e}")
        raise
    
    return pdf_path


def _add_image(story: List[Any], styles, title: str, uri: str, width_mm: float = 160.0):
    """이미지 추가 헬퍼"""
    try:
        if not uri or not isinstance(uri, str):
            print(f"[PDF] 이미지 URI 없음: {title}")
            return
        
        p = uri.replace("file:///", "").replace("/", os.sep)
        if not os.path.isfile(p):
            print(f"[PDF] 이미지 파일 없음: {p}")
            return
        
        story.append(Spacer(1, 8))
        story.append(Paragraph(title, styles["Heading3"]))
        story.append(Spacer(1, 4))
        
        # PIL로 크기 계산
        try:
            from PIL import Image as PILImage
            pil_img = PILImage.open(p)
            img_width, img_height = pil_img.size
            
            target_width = width_mm * mm
            aspect_ratio = img_height / img_width
            target_height = target_width * aspect_ratio
            
            # 최대 높이 제한
            max_height = 180 * mm
            if target_height > max_height:
                target_height = max_height
                target_width = target_height / aspect_ratio
            
            img = Image(p, width=target_width, height=target_height)
            story.append(img)
            print(f"[PDF] 이미지 추가 성공: {title}")
            
        except ImportError:
            img = Image(p, width=width_mm*mm)
            story.append(img)
            print(f"[PDF] 이미지 추가 (PIL 없음): {title}")
            
    except Exception as e:
        print(f"[PDF] 이미지 추가 실패 '{title}': {e}")


# ===== LangGraph 노드 =====
class ReportState(TypedDict):
    supervisor_results: Optional[Dict[str, Any]]
    summary: Optional[Dict[str, Any]]
    images: Optional[Dict[str, Any]]
    user_prompt: Optional[str]
    llm_text: Optional[str]
    pdf_path: Optional[str]
    error: Optional[str]


def validate_inputs(state: ReportState) -> ReportState:
    new = state.copy()
    supervisor_results = state.get("supervisor_results", {})
    
    if not supervisor_results:
        new["error"] = "No supervisor results provided"
        return new
    
    summary = {
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
    
    new["summary"] = summary
    return new


def collect_images_node(state: ReportState) -> ReportState:
    new = state.copy()
    summary = state.get("summary", {})
    new["images"] = _collect_images(summary)
    
    print(f"\n[Images] 수집 완료:")
    print(f"  - 지도: {'있음' if new['images'].get('map') else '없음'}")
    print(f"  - 배터리: {'있음' if new['images'].get('battery_chart') else '없음'}")
    print(f"  - HVAC: {'있음' if new['images'].get('hvac_chart') else '없음'}")
    print(f"  - OEM 차트: {len(new['images'].get('oem_charts_by_company', {}))}개")
    
    return new


def compose_prompt_node(state: ReportState) -> ReportState:
    new = state.copy()
    summary = state.get("summary", {})
    images = state.get("images", {})
    
    if not summary:
        new["error"] = "No summary available"
        return new
    
    user_prompt = _compose_user_prompt(summary, images)
    new["user_prompt"] = user_prompt
    
    print(f"\n[Prompt] 구성 완료 ({len(user_prompt)} chars)")
    return new


def call_llm_node(state: ReportState) -> ReportState:
    new = state.copy()
    user_prompt = state.get("user_prompt", "")
    
    if not user_prompt:
        new["error"] = "No user prompt generated"
        return new
    
    if not _HAS_LANGCHAIN:
        new["error"] = "LangChain not available"
        return new
    
    try:
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(model=model_name, temperature=0.3, max_tokens=4000)
        
        full_prompt = f"{PROMPT_SYSTEM}\n\n{user_prompt}"
        
        print(f"\n[LLM] 호출 중... (모델: {model_name})")
        response = llm.invoke(full_prompt)
        text = getattr(response, "content", "") or str(response)
        
        if not text or "can't create PDF" in text.lower():
            new["error"] = "LLM refused or returned empty"
            return new
        
        print(f"[LLM] 응답 수신 ({len(text)} chars)")
        new["llm_text"] = text
        
    except Exception as e:
        print(f"[LLM] 호출 실패: {e}")
        new["error"] = f"LLM call failed: {e}"
    
    return new


def render_pdf_node(state: ReportState) -> ReportState:
    new = state.copy()
    text = state.get("llm_text", "")
    images = state.get("images", {})
    summary = state.get("summary", {})
    
    if not text:
        new["error"] = "No LLM text to render"
        return new
    
    run_id = summary.get("run_id", "manual")
    pdf_path = os.path.join(_outputs_dir(), f"report_{run_id}.pdf")
    
    try:
        print(f"\n[PDF] 렌더링 시작...")
        out_pdf = _render_pdf(text, images, pdf_path)
        new["pdf_path"] = out_pdf
        print(f"[PDF] ✓ 렌더링 성공: {out_pdf}")
    except Exception as e:
        print(f"[PDF] ✗ 렌더링 실패: {e}")
        new["error"] = f"PDF render failed: {e}"
    
    return new


def compile_report_graph():
    from langgraph.graph import StateGraph
    
    graph = StateGraph(ReportState)
    graph.add_node("validate", validate_inputs)
    graph.add_node("collect_images", collect_images_node)
    graph.add_node("compose_prompt", compose_prompt_node)
    graph.add_node("call_llm", call_llm_node)
    graph.add_node("render_pdf", render_pdf_node)
    
    graph.set_entry_point("validate")
    graph.add_edge("validate", "collect_images")
    graph.add_edge("collect_images", "compose_prompt")
    graph.add_edge("compose_prompt", "call_llm")
    graph.add_edge("call_llm", "render_pdf")
    
    return graph.compile()


def run_report_writer(supervisor_results: Dict[str, Any]) -> Dict[str, Any]:
    compiled = compile_report_graph()
    
    init_state: ReportState = {
        "supervisor_results": supervisor_results,
        "summary": None,
        "images": None,
        "user_prompt": None,
        "llm_text": None,
        "pdf_path": None,
        "error": None,
    }
    
    final_state = compiled.invoke(init_state)
    
    return {
        "pdf_path": final_state.get("pdf_path"),
        "error": final_state.get("error"),
    }