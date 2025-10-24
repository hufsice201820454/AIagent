# AI Agent

본 프로젝트는 전기차(EV) 시장 분석 다중 에이전트 시스템을 설계·구현하는 실습 프로젝트입니다. 현재와 미래 관점을 통합해 전기차 시장 전반과 OEM별 동향 보고서를 자동 생성합니다.

	1) 현재 → 완성차 공장 주변 협력사 공장 수를 기준(66km/140km)으로 점수화
	2) 미래 → 국가별 ESG 정책과 기업 ESG 목표를 수집·요약
	3) 기술 → 완성차 10~20문장, 협력사 5~10문장으로 차별화 기술 요약
	4) 주식 → 시장 지표/차트와 1~3의 결과를 병합해 최종 리포트 생성

## 모든 결과는 output폴더에 저장되어 있습니다. (하위 Agent 생성 결과 + 최종 보고서 (html/pdf))

## Core Agents
	Value Chain Agent: 공장 입지/가동 현황 분석, 지리적 클러스터링
	TechSearch Agent: 완성차·배터리·공조의 차별화 기술 검색/요약
	ESG Agent: 각국 ESG/탄소 규제 및 기업 ESG 정책 요약
	Stock Agent: 상장사 주가 흐름/지표 분석 및 차트 생성
	Supervisor Agent: 하위 에이전트 결과 통합 및 보고서 생성

<img width="701" height="475" alt="image" src="https://github.com/user-attachments/assets/2e353a14-72b0-4ad6-92fb-4d31bc057be9" />
<img width="713" height="315" alt="image" src="https://github.com/user-attachments/assets/87b0efb2-6024-4543-a99c-d7ab5ff912b6" />
<img width="842" height="535" alt="image" src="https://github.com/user-attachments/assets/d95fa9cb-19cd-4610-a81f-1a86ad122d0d" />

## Overview
Objective: EV 관련 시장(OEM, 배터리, 공조) 분석
대상: 기업 분석, 주가 분석, 완성차 주변 공장 수/가동 현황 분석
목적: EV 시장의 생산(현상), 시장 반응(주가/재무), 규제/ESG(정책) 축을 통합 분석·시각화하여 투자 인사이트와 트렌드 리포트를 자동 생성한다.
최종 산출물: EV Trend Report (지도 + 주가 차트 + ESG 요약 포함, HTML/PDF)

## Method: AI Agent

## Tools
- 공통/검색: `tavily_tool`
- 주가/시각화: `stock_analysis`, `create_stock_chart`, `visualization_tool`
- ESG/정책: `GovESGSearch`, `CorpESGSearch`
- 기술 요약: 검색/파싱/중복제거/랭킹/요약·인용 유틸 일체(TechSearchAgent 내부)
- 보고서 출력: ReportWriterAgent 내 HTML→PDF 변환(Playwright/Chromium)


각 Tool의 주 사용 에이전트
	Value Chain Agent: visualization_tool, (보조로 tavily_tool)
	Stock Agent: stock_analysis, create_stock_chart
	ESG Agent: GovESGSearch, CorpESGSearch, (보조로 tavily_tool)
	
## State

1) Global State
	pg_conn: PostgreSQL 연결
	data_path: 산출물 파일 경로 (str)
	messages: 노드(에이전트)별 응답 누적
	final_report: 최종 리포트 파일명 또는 경로

	
2) Value Chain Agent State
	table(Data): PostgreSQL에서 가져온 공장/설비 데이터프레임 (DataFrame)
	list_result: 
	JIT 분석 결과 JIT 평가 결과 (List[Dict[str, float]] -> Json리턴)
    JIT 분석 결과 시각화 그래프 - map_oem_suppliers.png
	

4) Stock Agent State
	stock_chart_image: 생성된 주가 차트 이미지 경로 (str)
    stock_analysis_json 및 각 회사 주식 차트 return


5) ESG Agent State
	gov_esg_findings: 국가/지역 ESG 정책 검색 결과 요약
	corp_esg_findings: 기업 ESG 정책/보고서 요약


6) TechSearch Agent State
   query: str — 사용자가 던진 검색 질의(예: “EV 배터리 팩 공급거점 2024 생산량”)
   constraints: dict — 필터(언어, 국가/도메인, 날짜 범위, 파일형식 포함/제외)
   entities: list[str] — 회사/제품/지역 키워드 토큰화 결과
   results: list[dict] — 1차 검색 결과(타이틀, URL, 스니펫, 날짜, 출처 도메인)
   docs: list[dict] — 본문 추출/요약된 문서 블록(본문텍스트, 핵심문장, 추출표/수치)
   citations: list[dict] — 인용 메타(문장 ↔ URL, 발행일, 접근일)
   dedup_index: set — URL/문서 해시로 중복 제거용
   cache: dict — 동일/유사 질의 캐시(결과 재사용)
   output_json: dict — 최종 반환(JSON): { “summary”, “key_facts[]”, “links[]”, “citations[]” }


## Tech Stack
Category	Details
Framework	LangGraph, LangChain, Python
LLM	        GPT-4o-mini via OpenAI API
Embedding	OpenAI, multilingual-e5-large

## Agents
	#Supervisor Agent
		역할: 하위 에이전트 실행 순서 조정 및 최종 보고서 통합
		서브에이전트: Vaule Agent, Stock Agent, ESG Agent, TechSearch Agent
	#Value Chain Agent
		입력: 공장/설비 데이터, 참조 문헌(선택)
		도구: visualization_tool, tavily_tool(보조)
		출력: cluster_map_image, list_result
		서브에이전트: DBAgent(CSV 적재 및 데이터 로드), MapVisualizer(거리 좌표)
	#Stock Agent
		입력: 대상 회사/티커 목록
		도구: stock_analysis, create_stock_chart
		출력: stock_chart_image, 지표 요약(JSON/텍스트)
		서브에이전트: Researcher, Stock Analyzer, ChartVisualizer (주식 차트 반환)
	#ESG Agent
		입력: 국가/기업 식별자(도메인/이름)
		도구: GovESGSearch, CorpESGSearch, tavily_tool(보조)
		출력: gov_esg_findings, corp_esg_findings, 위험·정책 요약 (각 기업이 설정한 ESG 목표 연도를 설정 예정(완성차 회사 한정))
		서브에이전트: PolicyCrawler, CorporateESGSummarizer, RiskScorer(가능 하다면)
	#TechSearchAgent
		echQueryAgent: 기업명·도메인·제품 정보를 기반으로 EV 핵심 기술 키워드를 자동 생성. 완성차 회사만 검색하도록 변경(Tavily API 부족으로 인한 문제)

## 데이터 셋
	# 공장 위치(주소) 데이터
	# 완성차 위치
	# 공조 공장 위치
	# 배터리 공장 위치

## 평가지표

1. ValueChain Agent
정리
구분	        평균 거리 (km)	    출처
일본 자동차 산업	66 km (≈ 41 mile)	Smitka (1991), MIT Sloan Working Paper “Competitive Ties: Subcontracting in the Japanese Automotive Industry”
미국 자동차 산업	140 km (≈ 87 mile)	동 논문 / 미국 OEM 비교 데이터 인용
위 숫자를 count하여 count 자체를 점수로 선정
평가지표 설정 이유: JIT라는 용어는 완성차 공장 주위로 얼마나 많은 협력사들이 존재하는가를 의미
이를 기반으로 전기차 생산 및 연구에 얼마나 적극적인지를 직접적으로 알 수 있다고 판단하여 추가 에정

3. Stock_analyzer Agent
   	전기차 시장에 대한 전반적인 평가로만 사용을 할예정이며
	완성차시장과 협력사가 동시에 같이 오르는 양상을 보인다면 1
	아니라면 0점을 줄예정
    -> 시장에 대한 평가만 진행하며, OEM에 대한 평가는 진행하지 않음
   
5. ESG Agent
   1) S1, S2, S3의 Scope 설정
      S1: "scope_1": "Direct emissions from owned/controlled sources (e.g., company vehicles, on-site fuel combustion).",
      S2: "scope_2": "Indirect emissions from purchased electricity, steam, heat, or cooling.",
      S3: "scope_3": "All other indirect emissions across the value chain (upstream & downstream - suppliers, transportation, product use, etc.)."
   2) msci_esg_rating
      "scale": "AAA to CCC",
      "AAA_AA": "Leader - Strong management of financially relevant ESG risks relative to industry peers.",
      "A_BBB_BB": "Average - Mixed or average track record of managing ESG risks and opportunities.",
      "B_CCC": "Laggard - High exposure and failure to manage significant ESG risks.",
      "description": "Evaluates company resilience to industry-specific sustainability risks. Based on exposure to 35 key ESG issues and management effectiveness. Industry-relative scoring (0-10 scale mapped to letter grades)." 
   3) Cdp Score
   	  "cdp_score": {
      "scale": "A to F",
      "A": "Leadership - Environmental leadership with best practices - climate transition plans, supply chain risk management, TCFD/SBTi alignment.",
      "B": "Management - Demonstrates coordinated actions and strategies to manage environmental impacts.",
      "C": "Awareness - Acknowledges environmental issues but taking limited action.",
      "D": "Disclosure - Transparent about environmental impact but minimal evidence of action.",
      "F": "Failure - Failed to provide sufficient information or did not respond to CDP request.",
      "description": "Assesses transparency and action on climate change, water security, and forests. Companies progress through four stages: Disclosure ??Awareness ??Management ??Leadership. Scored separately for Climate, Water, and Forests themes."
    }

	"ghg_protocol": "https://ghgprotocol.org/corporate-standard" -> 위 선정기준에 따라 각 완성차 회사의 ESG 평가 진행
     평가 진행 이유: 국제 정책에 따라 ESG 압박이 심해지는 추세로, ESG 대응에 적극적이라면, 전기차 연구또한 적극적일것
   
7. TechSearch Agent
   	기사에 대한 요약 및 전기차 핵심기술 출력
    기술 평가 지표 (Evaluation Metrics)
	구분	의미	평가 기준 요약
	TRL (Technology Readiness Level)	기술성숙도	기술의 개발 단계 성숙도를 평가. (1: 기본원리 확인 ~ 9: 상용운영 완료)
	MRL (Manufacturing Readiness Level)	제조성숙도	양산 준비 수준을 평가. (1: 개념설계 ~ 10: 전량 생산 단계)
	CRAAP	정보 신뢰도 평가	정보의 Currency(시의성), Relevance(적합성), Authority(권위), Accuracy(정확성), Purpose(목적)을 기반으로 판단.
	Materiality	중요도(재무·비재무 영향)	기술이 산업·지속가능성·재무성과 등에 미치는 실질적 영향 정도 평가.
	ISSB Alignment	국제 지속가능 공시 연계성	IFRS S1/S2 등 국제 기준(ISSB, IFRS)과의 정합성 평가.
	OTA_Compliance	OTA(Over-the-Air) 규제 준수	ISO 24089, UNECE R156 등 차량 OTA 업데이트 관련 표준 및 규제 준수 여부 평가.

## 종합 결과 산정
   1) Value-Chain : 30
   2) ESG : 30
   3) TechSearch : 30
   4) StockAnalyer: 10

## 종합 결과 선정 이유

# Value-Chain 30
자동차 산업의 공급업체 집적과 근접성은 생산성·품질·물류 효율과 연관됨(집적경제, JIT 지원).
MIT Sloan Working Paper: 일본 자동차 하도급 네트워크와 JIT의 지역적 근접성 분석. Smitka, 1991. https://dspace.mit.edu/handle/1721.1/47204
연방준비은행(시카고) 연구: 자동차 공급업체 공장의 군집화와 agglomeration economies. Klier & McMillen, 2008. 


# ESG 30
대규모 메타연구: ESG-재무성과 간 양(+)의 상관이 관찰됨(표본·방법론별 차이는 존재).
Friede, Busch, Bassen (2015) “ESG and Financial Performance: Aggregated Evidence from more than 2000 Empirical Studies.” Journal of Sustainable Finance & Investment. https://www.tandfonline.com/doi/abs/10.1080/20430795.2015.1118917
Khan, Serafeim, Yoon (2016) “Corporate Sustainability: First Evidence on Materiality.” (SSRN/Harvard) 재무적으로 “중요한” ESG 이슈에 대한 성과와 초과성과의 관련성 보고. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2575912
ISSB(IFRS S1/S2): 투자자 의사결정에 유용한 지속가능성 공시 표준으로 제정. https://www.ifrs.org/issued-standards/ifrs-sustainability-standards/


# TechSearch 30
TRL/MRL 등 기술·제조 성숙도 지표는 사업화 리스크(비용·일정 지연) 저감과 연계되어 평가·투자 의사결정에 활용됨.
예시 출처:
GAO “Technology Readiness Assessment Guide” (GAO-20-48G): TRL 활용 가이드, 성숙도 부족은 프로그램 실패·초과비용 리스크 증가. https://www.gao.gov/products/gao-20-48g
DoD “Manufacturing Readiness Level (MRL) Deskbook”: MRL로 제조 성숙도 평가·리스크 관리. (DAU 배포판)
OTA 관련 규제·표준은 안전·보안·규정준수의 객관적 기준 제공(예: UNECE R156, ISO 24089). https://unece.org/ (R156), https://www.iso.org/ (ISO 24089)


# Stock 10
주가 지표는 시장 심리·유동성 등 단기 요인이 크고, 실물·장기 운영성과의 설명력은 제한적이라는 연구가 존재. 전략·운영평가의 보조지표로 낮은 가중치 정당화 가능.
Shiller (1981) “Do Stock Prices Move Too Much to be Justified by Subsequent Changes in Dividends?” American Economic Review. 주가 변동성 과잉 논증. (JSTOR/NBER 게재)
Fischer Black (1986) “Noise.” The Journal of Finance. 가격에 반영된 “노이즈” 개념화로 정보 대비 변동성 강조.
장기 펀더멘털 예측보다는 단기 모멘텀·역전 현상 보고(예: Jegadeesh & Titman 1993), 전략/기술·운영 지표와 목적이 상이.
   

## 산출 보고서 양식
	전기차 시장 트렌드 분석 레포트 – 보고서 양식 요약

	이 문서는 EV 시장 분석 보고서의 공식 템플릿입니다.
	하위 Agent들이 생성한 JSON·이미지 데이터를 기반으로 자동 PDF 보고서를 생성합니다.

	구성 목차
	1. 전기차 시장 트렌드 분석 레포트

		보고서 표지 (제목 + 작성일)

	2. 요약 (Executive Summary)

		5~7문장 핵심 요약

		주요 수치 및 출처(예: “2024년 EV 시장 35% 성장 (Stock)”)

	3. 시장 분석
	구분	내용
	3.1 전기차 산업 개요	글로벌 생산·판매·기술·공급망 동향 (4~6문단)
	3.2 정부 ESG 정책	국가별 목표/정책 표 + 2~3줄 설명
	3.3 글로벌 생산 거점 분석	[이미지:지도] OEM & 공급사 위치 + JIT 리스크 분석
	3.4 소결	상기 요약 (3~4줄)
	4. 개별 OEM 분석 (반복 섹션)

	모든 OEM(BMW, Tesla, BYD, Hyundai 등)에 대해 동일 형식으로 작성.

	항목	주요 내용
	4.X.1 공급망 경쟁력 (JIT)	JIT Score / Regional Score 표 + 해석
	4.X.2 Value Chain 위치	66km·140km 내 공급사 수
	4.X.3 기술 수준	TRL·MRL·OTA 등 기술 점수 표
	4.X.4 주가 동향	90일 변화율·시가총액·PER 표 + 주가·협력사 차트 삽입
	4.X.5 ESG 대응	탄소중립 목표·Scope1/2/3·MSCI·CDP 표
	4.X.6 종합 평가	강점·약점 요약 + 총점 및 산정 기준
	5. 종합 결론
	구분	내용
	5.1 현재 시장 상황	ValueChain + Stock 종합 분석
	5.2 미래 전망	ESG 목표 기반 시장 예측
	5.3 종합 순위	OEM별 종합 점수표 (JIT·Tech·ESG·Stock 기반)
	5.4 최종 결론	시장 핵심 메시지 (3~4줄)
	6. Appendix


## 디렉터리 구조(요약)


├── data/                  # PDF 문서


├────── csv 파일 3개


├── agents/                # Agent 모듈


├────── SupervisorAgent.py


├────── ValueChainAgent.py


├────── StockAnalyzerAgent.py


├────── ESGAgent.py


├────── TechSearchAgent.py


├── prompts/               # 프롬프트 템플릿


├────── Prompt.py


├── outputs/               # 결과 산출물(HTML/PDF/이미지/JSON)


├── db/


├────── Postgre.py


├── app.py                 # 실행 스크립트


├── README.md


└── .env

## 변경사항
# Part 1 (25.10.23)
 1. PDF Adorby 문제로 보고서 생성 중간에 완료되어버리는 문제 발생
 2. 이에 따라 보고서를 기업별로 생성하는 로직으로 변경
 3. 또한 보고서 생성시 html을 먼저 생성하고 html을 PDF로 변환하는 로직으로 변경
 4. StockAnalyerAgent에서 주식 분석 및 기업 서치를 동시에 진행하였으나, 하나의 Agent가 하나의 역할을 수행하게 하기 위해 StockAnalyzer와 TechSearch Agent로 분할
 5. Supervisor이후 ReportWriterAgent가 작동되도록 ReportWriterAgent 추가
 6. Supervisor의 정의에 따라, Supervisor가 하위 Agent에 명령을 하달하고 그를 기반으로 수행하는 로직으로 변경
 7. RAG 파이프라인 계획과 DB 연동 계획 제거

## 에러 상황
1. 보고서에 reference가 들어가지를 않음 -> 현재 Json타입에는 제대로 reference가 들어가 있음
2. 그 외 모든 에러는 해결되었습니다.
3. 다만 아키텍처 수정이 안된 상황입니다.

## 확장 방향
1. 영업팀을 위한 실시간 대시보드로 Agent의 결과를 연동할 계획입니다.
2. 대시보드 예정상황은 다음과 같습니다.
<img width="259" height="282" alt="image" src="https://github.com/user-attachments/assets/3c2deec0-2345-4632-8593-609cd65ac73d" />


		
## Architecture
<img width="2505" height="1640" alt="Mermaid Chart - Create complex, visual diagrams with text -2025-10-21-083600" src="https://github.com/user-attachments/assets/20c05d80-e84b-47f0-8876-abc42c558a4a" />


## 보고서 생성(HTML/PDF)
- HTML 생성: `ReportWriterAgent`가 OEM별 본문/표/이미지를 합쳐 HTML 생성
- PDF 생성: Playwright 기반으로 HTML을 A4 PDF로 직접 렌더링
  - 필수 설치
    - `pip install playwright`
    - `playwright install chromium`
- 배치 변환: 에이전트 실행 시 `outputs` 폴더의 남은 HTML도 일괄 PDF로 변환

## 실행 예시
- 앱 실행: `python evagent/app.py`



## 실행결과
PS C:\workspace\evagent> python app.py
[Config] Loaded 9 OEMs from whitelist:
  - Tesla
  - Rivian
  - General Motors
  - Ford
  - BYD
  - Li Auto
  - XPeng
  - BMW
  - Volkswagen

EV Market Analysis Pipeline

Target OEMs (9):
  1. Tesla
  2. Rivian
  3. General Motors
  4. Ford
  5. BYD
  6. Li Auto
  7. XPeng
  8. BMW
  9. Volkswagen

ESG Regions: KR, CN, JP, EU, US
Output: C:\workspace\evagent\outputs
Timestamp: 2025-10-24 15:30:00


[STEP 1/2] Running SupervisorAgent (4 agents in parallel)

Fetching data for 9 OEMs, 5 Battery, 6 HVAC suppliers...
  Fetching Tesla (TSLA)...
  Fetching Rivian (RIVN)...
  Fetching General Motors (GM)...
  Fetching Ford (F)...
  Fetching BYD (BYDDF)...
  Fetching Li Auto (LI)...
  Fetching XPeng (XPEV)...
  Fetching BMW (BMWYY)...
$BMWYY: possibly delisted; no price data found  (period=3mo) (Yahoo error = "No data found, symbol may be delisted")
  Fetching Volkswagen (VWAGY)...
  Fetching TSMC (TSM)...
  Fetching CATL (300750.SZ)...
  Fetching Panasonic (PCRFY)...
$PCRFY: possibly delisted; no price data found  (period=3mo) (Yahoo error = "No data found, symbol may be delisted")
  Fetching Samsung SDI (006400.KS)...
  Fetching LG Energy Solution (373220.KS)...
  Fetching DENSO (6902.T)...
  Fetching Valeo (FR.PA)...
  Fetching Gentherm (THRM)...
  Fetching Modine (MOD)...
  Fetching Dana (DAN)...
  Fetching Hanon Systems (018880.KS)...

Analyzing market trends...
Running LLM evaluation...

✓ Analysis complete. Results saved to C:\workspace\evagent\outputs\stock_analysis.json
✓ OEM charts: 8
✓ Supplier charts: 2
✓ Trend indicators: OEM=1, Supplier=1, Correlation=1.0

[SUPERVISOR] Execution Summary:
  Final Status: ✓ SUCCESS

  Validation Results:
    ✓ tech
    ✓ valuechain
    ✓ stock
    ✓ esg

  Tech Analysis (9 companies):
    ✓ Tesla: TRL=7, MRL=8, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5
    ✓ Rivian: TRL=7, MRL=8, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5
    ✓ General Motors: TRL=7, MRL=6, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5
    ✓ Ford: TRL=7, MRL=6, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5
    ✓ BYD: TRL=7, MRL=8, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5
    ✓ Li Auto: TRL=7, MRL=8, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5
    ✓ XPeng: TRL=7, MRL=6, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5
    ✓ BMW: TRL=7, MRL=8, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5
    ✓ Volkswagen: TRL=5, MRL=4, CRAAP=4, Materiality=5, ISSB=3, OTA_Compliance=5

[STEP 2/2] Running ReportWriterAgent (PDF generation)
총 9개 OEM 보고서 생성
[1/9] Tesla

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] Tesla (40680 chars)
[LLM] 호출 중...
[LLM] 완료 (4103 chars)
[INFO] 회사 섹션: Tesla
[HTML] ✓ report_report_001_Tesla.html
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

[2/9] Rivian

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] Rivian (40702 chars)
[LLM] 호출 중...
[LLM] 완료 (3841 chars)
[INFO] 회사 섹션: Rivian
[HTML] ✓ report_report_001_Rivian.html
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

[3/9] General Motors

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] General Motors (41103 chars)
[LLM] 호출 중...
[LLM] 완료 (3335 chars)
[INFO] 회사 섹션: General Motors
[HTML] ✓ report_report_001_General_Motors.html
[PDF] ✓ playwright: report_report_001_General_Motors.pdf
[PDF] ✓ playwright: report_report_001_General_Motors.pdf
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

[4/9] Ford

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] Ford (40771 chars)
[LLM] 호출 중...
[LLM] 완료 (4843 chars)
[INFO] 회사 섹션: Ford
[HTML] ✓ report_report_001_Ford.html
[PDF] ✓ playwright: report_report_001_Ford.pdf
[PDF] ✓ playwright: report_report_001_Ford.pdf
[PDF] ✓ playwright: report_report_001_General_Motors.pdf
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

[5/9] BYD

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] BYD (41012 chars)
[LLM] 호출 중...
[LLM] 완료 (3490 chars)
[INFO] 회사 섹션: BYD
[HTML] ✓ report_report_001_BYD.html
[PDF] ✓ playwright: report_report_001_BYD.pdf
[PDF] ✓ playwright: report_report_001_BYD.pdf
[PDF] ✓ playwright: report_report_001_Ford.pdf
[PDF] ✓ playwright: report_report_001_General_Motors.pdf
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

[6/9] Li Auto

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] Li Auto (41257 chars)
[LLM] 호출 중...
[LLM] 완료 (4306 chars)
[INFO] 회사 섹션: Li Auto
[HTML] ✓ report_report_001_Li_Auto.html
[PDF] ✓ playwright: report_report_001_Li_Auto.pdf
[PDF] ✓ playwright: report_report_001_BYD.pdf
[PDF] ✓ playwright: report_report_001_Ford.pdf
[PDF] ✓ playwright: report_report_001_General_Motors.pdf
[PDF] ✓ playwright: report_report_001_Li_Auto.pdf
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

[7/9] XPeng

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] XPeng (40665 chars)
[LLM] 호출 중...
[LLM] 완료 (4394 chars)
[INFO] 회사 섹션: XPeng
[HTML] ✓ report_report_001_XPeng.html
[PDF] ✓ playwright: report_report_001_XPeng.pdf
[PDF] ✓ playwright: report_report_001_BYD.pdf
[PDF] ✓ playwright: report_report_001_Ford.pdf
[PDF] ✓ playwright: report_report_001_General_Motors.pdf
[PDF] ✓ playwright: report_report_001_Li_Auto.pdf
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[PDF] ✓ playwright: report_report_001_XPeng.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

[8/9] BMW

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] BMW (40624 chars)
[LLM] 호출 중...
[LLM] 완료 (3678 chars)
[HTML] ✓ report_report_001_BMW.html
[PDF] ✓ playwright: report_report_001_BMW.pdf
[PDF] ✓ playwright: report_report_001_BMW.pdf
[PDF] ✓ playwright: report_report_001_BYD.pdf
[PDF] ✓ playwright: report_report_001_Ford.pdf
[PDF] ✓ playwright: report_report_001_General_Motors.pdf
[PDF] ✓ playwright: report_report_001_Li_Auto.pdf
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[PDF] ✓ playwright: report_report_001_XPeng.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

[9/9] Volkswagen

[Images] 수집:
  - OEM 차트: 8개
    • BYD
    • Ford
    • General Motors
    • Li Auto
    • Rivian
    • Tesla
    • Volkswagen
    • XPeng
[Prompt] Volkswagen (40876 chars)
[LLM] 호출 중...
[LLM] 완료 (3497 chars)
[INFO] 회사 섹션: Volkswagen
[HTML] ✓ report_report_001_Volkswagen.html
[PDF] ✓ playwright: report_report_001_Volkswagen.pdf
[PDF] ✓ playwright: report_report_001_BMW.pdf
[PDF] ✓ playwright: report_report_001_BYD.pdf
[PDF] ✓ playwright: report_report_001_Ford.pdf
[PDF] ✓ playwright: report_report_001_General_Motors.pdf
[PDF] ✓ playwright: report_report_001_Li_Auto.pdf
[PDF] ✓ playwright: report_report_001_Rivian.pdf
[PDF] ✓ playwright: report_report_001_Tesla.pdf
[PDF] ✓ playwright: report_report_001_Volkswagen.pdf
[PDF] ✓ playwright: report_report_001_XPeng.pdf
[IMG] batch converter unavailable (imgkit/wkhtmltoimage 미설치 가능)

보고서 생성 완료

성공: 9개 / 실패: 0개

생성된 보고서:
  • Tesla: report_report_001_Tesla.pdf
  • Rivian: report_report_001_Rivian.pdf
  • General Motors: report_report_001_General_Motors.pdf
  • Ford: report_report_001_Ford.pdf
  • BYD: report_report_001_BYD.pdf
  • Li Auto: report_report_001_Li_Auto.pdf
  • XPeng: report_report_001_XPeng.pdf
  • BMW: report_report_001_BMW.pdf
  • Volkswagen: report_report_001_Volkswagen.pdf



