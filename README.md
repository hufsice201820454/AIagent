# AIagent

본 프로젝트는 전기차(EV) 시장 분석을 하는 에이전트를 설계하고 구현한 실습 프로젝트입니다.

# change 1
	크게 현재와 미래를 토대로 전반적인 전기차 시장 분석과 각 완성차 기업이 전기차 시장에서 어떻게 사업을 전개하고 있는지 주식리포트를 생성하려 합니다.

	1) 현재 -> 전기 자동차 공장의 위치를 기반 그 주변의 협력사 공장의 수를 count 하여 점수화 하려합니다. -> 도메인적 지식으로 66km, 140km 를 평가기준으로 설정합니다.
	2) 미래 -> ESG 정책을 국가 별로 검색하고 / 각 기업의 목표를 (url)을 입력하여 Agent가 기업별 ESG 목표/년도를 찾게 할 생각입니다.
	3) 기업의 차별화된 전기차 기술을 검색하려 합니다 / 완성차의 경우 10 ~ 20문장 / 협력사의 경우 5 ~ 10 문장/ 으로 요약할 생각입니다.
	4) 주식 리포트와 1,2,3의 결과를 병합하여 보고서를 출력하려 합니다. 

## Core Agents (3)
	Value Chain Agent: 공장 입지/가동 현황 데이터 분석 및 지리적 클러스터링
	TechSearch Agent: 완성차·배터리·공조 회사에서의 전기차 관련 차별화된 기술을 정리합니다 / 완성차 10 ~ 20 / 협력사 5 ~ 10
	ESG Agent: 각국 ESG/탄소 규제와 기업 ESG 정책·리스크 요약
	Stock Agent: 완성차·배터리·공조 관련 상장사 주가 흐름/지표 분석 및 차트 생성
	Supervisor Agent: 3개 결과를 통합하여 최종 보고서 작성

<img width="701" height="475" alt="image" src="https://github.com/user-attachments/assets/2e353a14-72b0-4ad6-92fb-4d31bc057be9" />
<img width="713" height="315" alt="image" src="https://github.com/user-attachments/assets/87b0efb2-6024-4543-a99c-d7ab5ff912b6" />
<img width="842" height="535" alt="image" src="https://github.com/user-attachments/assets/d95fa9cb-19cd-4610-a81f-1a86ad122d0d" />

## Overview
Objective: EV 관련 시장(OEM, 배터리, 공조) 분석
대상: 기업 분석, 주가 분석, 완성차 주변 공장 수/가동 현황 분석
목적: EV 시장의 생산(현상), 시장 반응(주가/재무), 규제/ESG(정책) 축을 통합 분석·시각화하여 투자 인사이트와 트렌드 리포트를 자동 생성한다.
최종 산출물: EV Trend Report (지도 + 주가 차트 + ESG 요약 포함)

## Method: AI Agent + Advanced RAG

## Tools
1. 공통/검색
	tavily_tool: 최신 정보/문헌 검색(Research 보조)

	
2. 주가/시각화
	stock_analysis: 주식 핵심 지표 요약 분석 문자열 반환 (Stock Agent)
	create_stock_chart: 티커 기반 PNG 차트 생성 + 통계 요약 반환 (Stock Agent)
	visualization_tool: 밸류체인 클러스터 지도/산출물 시각화 (Value Chain Agent)

	
3. ESG/정책
	GovESGSearch: 각국 ESG·탄소 규제 검색 (ESG Agent)
	CorpESGSearch: 기업 도메인 기반 ESG 정책/보고서 검색 (ESG Agent)


4. 기술 요약
	TechSearchAgent – Tools
	SearchTool — 웹 검색 API 호출(뉴스/웹/학술/도메인 필터, 날짜 범위)
	Fetcher — URL 가져오기(HTML/PDF/CSV), 리다이렉트/헤더 처리	
	Parser — 본문/표/메타데이터 추출(HTML, PDF 텍스트화), 언어 감지
	Deduper — 유사도/URL 해시 기반 중복 제거
	Ranker — 최신성·권위도·일치도 가중 랭킹(예: 날짜↑, .gov/.edu/.org 가중)
	Summarizer — 문서 요약·핵심 문장/수치 뽑기(문장별 근거 연결)
	CitationBuilder — 문장별 근거 URL/발행일 매핑, 인용 리스트 생성
	Normalizer — 수치/단위/날짜 표준화(예: kWh↔MWh, 2025-10-22 ISO)
	CacheStore — 질의↔결과 캐시 저장/조회
	RateLimiter — 호출 빈도 제어(벤더 API 쿼터 보호)


6. 각 Tool의 주 사용 에이전트
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
	list_result: 클러스터링/요약 결과 (List[Dict[str, float]] 등)
	cluster_map_image: 클러스터 시각화 이미지 경로 (str)


3) Stock Agent State
	stock_chart_image: 생성된 주가 차트 이미지 경로 (str)
	(선택) price_df, metrics_json 등 내부 분석 산출물


4) ESG Agent State
	gov_esg_findings: 국가/지역 ESG 정책 검색 결과 요약
	corp_esg_findings: 기업 ESG 정책/보고서 요약


5) TechSearch Agent State
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
Retrieval	Chroma
Embedding	OpenAI, multilingual-e5-large
DB	        PostgreSQL

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
	🧩 기술 평가 지표 (Evaluation Metrics)
	구분	의미	평가 기준 요약
	TRL (Technology Readiness Level)	기술성숙도	기술의 개발 단계 성숙도를 평가. (1: 기본원리 확인 ~ 9: 상용운영 완료)
	MRL (Manufacturing Readiness Level)	제조성숙도	양산 준비 수준을 평가. (1: 개념설계 ~ 10: 전량 생산 단계)
	CRAAP	정보 신뢰도 평가	정보의 Currency(시의성), Relevance(적합성), Authority(권위), Accuracy(정확성), Purpose(목적)을 기반으로 판단.
	Materiality	중요도(재무·비재무 영향)	기술이 산업·지속가능성·재무성과 등에 미치는 실질적 영향 정도 평가.
	ISSB Alignment	국제 지속가능 공시 연계성	IFRS S1/S2 등 국제 기준(ISSB, IFRS)과의 정합성 평가.
	OTA_Compliance	OTA(Over-the-Air) 규제 준수	ISO 24089, UNECE R156 등 차량 OTA 업데이트 관련 표준 및 규제 준수 여부 평가.
   

## 산출 보고서 양식
	📘 전기차 시장 트렌드 분석 레포트 – 보고서 양식 요약

	이 문서는 EV 시장 분석 보고서의 공식 템플릿입니다.
	하위 Agent들이 생성한 JSON·이미지 데이터를 기반으로 자동 PDF 보고서를 생성합니다.

	📑 구성 목차
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


## 디렉토리 구조


├── data/                  # PDF 문서


├────── csv 파일 3개


├── agents/                # Agent 모듈


├────── SupervisorAgent.py


├────── ValuechainAgent.py


├────── StockAnalyzerAgent.py


├────── EsgAgent.py


├────── TechSearchAgent.py


├── prompts/               # 프롬프트 템플릿


├────── Prompt.py


├── outputs/			   # 결과 값 산출


├── db/


├────── Postgre.py


├── app.py                 # 실행 스크립트


├── README.md


└── .env
		
Architecture
<img width="2505" height="1640" alt="Mermaid Chart - Create complex, visual diagrams with text -2025-10-21-083600" src="https://github.com/user-attachments/assets/20c05d80-e84b-47f0-8876-abc42c558a4a" />



