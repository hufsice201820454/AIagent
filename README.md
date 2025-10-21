# AIagent

{TITLE}
본 프로젝트는 전기차(EV) 시장 분석을 하는 에이전트를 설계하고 구현한 실습 프로젝트입니다.

## Core Agents (3)
	Value Chain Agent: 공장 입지/가동 현황 데이터 분석 및 지리적 클러스터링
	Stock Agent: 완성차·배터리·공조 관련 상장사 주가 흐름/지표 분석 및 차트 생성
	ESG Agent: 각국 ESG/탄소 규제와 기업 ESG 정책·리스크 요약
	Supervisor Agent: 3개 결과를 통합하여 최종 보고서 작성
	
## Overview
Objective: EV 관련 시장(OEM, 배터리, 공조) 분석
대상: 기업 분석, 주가 분석, 완성차 주변 공장 수/가동 현황 분석
목적: EV 시장의 생산(현상), 시장 반응(주가/재무), 규제/ESG(정책) 축을 통합 분석·시각화하여 투자 인사이트와 트렌드 리포트를 자동 생성한다.
최종 산출물: EV Trend Report (클러스터 지도 + 주가 차트 + ESG 요약 포함)

## Method: AI Agent + Advanced RAG

## Tools
# 공통/검색
	tavily_tool: 최신 정보/문헌 검색(Research 보조)
	
# 주가/시각화
	stock_analysis: 주식 핵심 지표 요약 분석 문자열 반환 (Stock Agent)
	create_stock_chart: 티커 기반 PNG 차트 생성 + 통계 요약 반환 (Stock Agent)
	visualization_tool: 밸류체인 클러스터 지도/산출물 시각화 (Value Chain Agent)
	
# ESG/정책
	GovESGSearch: 각국 ESG·탄소 규제 검색 (ESG Agent)
	CorpESGSearch: 기업 도메인 기반 ESG 정책/보고서 검색 (ESG Agent)

# 각 Tool의 주 사용 에이전트
	Value Chain Agent: visualization_tool, (보조로 tavily_tool)
	Stock Agent: stock_analysis, create_stock_chart
	ESG Agent: GovESGSearch, CorpESGSearch, (보조로 tavily_tool)
	
##State
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


Tech Stack
Category	Details
Framework	LangGraph, LangChain, Python
LLM	GPT-4o-mini via OpenAI API
Retrieval	Chroma
Embedding	OpenAI, multilingual-e5-large
DB	PostgreSQL

##Agents
	#Supervisor Agent
		역할: 하위 에이전트 실행 순서 조정 및 최종 보고서 통합
		서브에이전트: Vaule Agent, Stock Agent, ESG Agent
	#Value Chain Agent
		입력: 공장/설비 데이터, 참조 문헌(선택)
		도구: visualization_tool, tavily_tool(보조)
		출력: cluster_map_image, list_result
		서브에이전트: DBAgent(CSV 적재 및 데이터 로드), MapVisualizer (클러스터링)
	#Stock Agent
		입력: 대상 회사/티커 목록
		도구: stock_analysis, create_stock_chart
		출력: stock_chart_image, 지표 요약(JSON/텍스트)
		서브에이전트: Researcher, Stock Analyzer, ChartVisualizer (주식 차트 반환)
	#ESG Agent
		입력: 국가/기업 식별자(도메인/이름)
		도구: GovESGSearch, CorpESGSearch, tavily_tool(보조)
		출력: gov_esg_findings, corp_esg_findings, 위험·정책 요약
		서브에이전트: PolicyCrawler, CorporateESGSummarizer, RiskScorer(가능 하다면)
		
Architecture
User → Supervisor → (Value Chain / Stock / ESG) → 결과 병합 → EV Trend Report
각 메인 에이전트 내부에서 1~3개의 서브에이전트를 선택적으로 호출해 단계별 처리
Directory Structure
├── data/ # PDF 문서
├── agents/ # Agent 모듈
├── prompts/ # 프롬프트 템플릿
├── outputs/ # 평가 결과 저장
├── app.py # 실행 스크립트
└── README.md
