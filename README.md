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


4. 각 Tool의 주 사용 에이전트
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
(선택) esg_risk_score 등 정규화된 지표


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
		서브에이전트: Vaule Agent, Stock Agent, ESG Agent
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
글로벌 설계 상한	≤ 1 000 km	        Boston Consulting Group (2015), Balancing Auto Suppliers’ Manufacturing Networks

2. Stock_analyzer Agent -> 찾을 예정 
3. ESG Agent -> 찾을 예정

## 산출 보고서 양식
	1. 전반적 요약
	2. 전기차 시장 전체적 트렌드 요약
		1. Agent 별 결과 종합하여 확인 -> 전기차 시장의 현재를 확인
		2. ESG 정책을 토대로 전기차 시장의 미래가 어떻게 될지 확인
	3. 각 완성차 기업 분석 결과
		#완성차 회사
		1. Value Chain Agent -> 현재 기업 주위로 묶어져 있는 협력사 숫자 확인
		2. Stock Analyzer Agent -> 현재 그 기업의 주가를 분석 예정
		3. ESG Agent -> 각 기업이 설정한 ESG 목표 연도를 설정 예정(완성차 회사 한정)
			#완성차 회사 별 협력사 상황
			2. Stock Analyzer Agent -> 주가를 분석할 예정

## 디렉토리 구조


├── data/                  # PDF 문서


├────── csv 파일 3개


├── agents/                # Agent 모듈


├────── SupervisorAgent.py


├────── ValuechainAgent.py


├────── StockAnalyzerAgent.py


├────── EsgAgent.py


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



