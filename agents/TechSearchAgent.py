# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import json
import re
import time
from typing import Any, Dict, List, Optional, TypedDict
from urllib import request, parse

try:
    from langchain.tools import tool
except Exception:
    def tool(*args, **kwargs):
        def deco(fn):
            return fn
        return deco

def _load_env_from_dotenv() -> None:
    if os.getenv("TAVILY_API_KEY") and os.getenv("OPENAI_API_KEY"):
        return
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.normpath(os.path.join(base_dir, "..", ".env"))
        if os.path.isfile(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and v and not os.getenv(k):
                        os.environ[k] = v
    except Exception:
        pass

_load_env_from_dotenv()

COMPANY_CANON = {
    "Tesla": "tesla.com",
    "Rivian": "rivian.com",
    "General Motors": "gm.com",
    "Ford": "ford.com",
    "BYD": "byd.com",
    "Li Auto": "lixiang.com",
    "XPeng": "xiaopeng.com",
    "BMW": "bmw.com",
    "Volkswagen": "volkswagen.com",
}

def _tavily_search(query: str, *, depth: str = "basic", include_domains: Optional[List[str]] = None, max_results: int = 8) -> Dict[str, Any]:
    """Call Tavily /search; return JSON dict (or {})."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {}
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "include_answer": True,
        "search_depth": depth,
    }
    if include_domains:
        payload["include_domains"] = include_domains
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}


def _extract_urls(results: Dict[str, Any]) -> List[Dict[str, str]]:
    """From Tavily response, collect [{'title':..., 'url':..., 'content':...}, ...]."""
    items: List[Dict[str, str]] = []
    if not isinstance(results, dict):
        return items
    for k in ("results", "data"):
        arr = results.get(k)
        if isinstance(arr, list):
            for e in arr:
                url = e.get("url") or e.get("link")
                title = e.get("title") or ""
                content = e.get("content") or e.get("snippet") or ""
                if url:
                    items.append({"title": title, "url": url, "content": content})
    return items


def _domain_from_url(url: str) -> str:
    try:
        netloc = parse.urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""

def _call_openai(messages: List[Dict[str, str]], model: str = "gpt-4o-mini", temperature: float = 0.3) -> str:
    """Call OpenAI Chat API; return assistant message content."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    try:
        with request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"Error: {e}"

@tool("TechDomainResolver", description="Resolve official website domain for a company (OEM focus)")
def TechDomainResolver(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Input: {"company": str} -> Output: {"company": str, "domain": str|None}.
    Resolve official domain using whitelist; fallback to Tavily search.
    """
    comp: str = payload.get("company", "").strip()
    if not comp:
        return {"company": comp, "domain": None}

    hint = COMPANY_CANON.get(comp)
    if hint:
        return {"company": comp, "domain": hint}

    data = _tavily_search(f"{comp} official website", depth="basic", max_results=5)
    items = _extract_urls(data)
    domains = []
    for it in items:
        d = _domain_from_url(it["url"])
        if d:
            domains.append(d)

    key = re.sub(r"[^a-z0-9]+", "", comp.lower())
    domains = sorted(set(domains), key=lambda x: (len(x), x))
    for d in domains:
        if key[:4] in re.sub(r"[^a-z0-9]+", "", d):
            return {"company": comp, "domain": d}
    return {"company": comp, "domain": domains[0] if domains else None}


@tool("TechQueryBuilder", description="Build OEM-specific technology query terms")
def TechQueryBuilder(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Input: {company, company_type} -> Output: {company, query_terms[]}.
    Return generic EV tech-related query terms for OEMs.
    """
    terms = [
        "800V platform", "SiC inverter", "thermal management", "heat pump",
        "battery pack cooling", "fast charging 350kW", "autonomy OTA",
        "manufacturing readiness", "production timeline", "supply chain",
    ]
    return {"company": payload.get("company"), "query_terms": terms}


@tool("TechSearch", description="Search web via Tavily with optional domain priority; return hits and best answer")
def TechSearch(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Input: {company, domain?, query_terms[]} -> Output: {hits[], answer}.
    Executes Tavily search for each query; prefers hits from given domain.
    """
    company = payload.get("company") or ""
    domain = payload.get("domain")
    terms: List[str] = payload.get("query_terms", [])
    queries = []
    for t in terms[:8]:
        q = f'{company} {t}'
        queries.append(q)

    include_domains = [domain] if domain else None
    all_hits: List[Dict[str, str]] = []
    best_answer: Optional[str] = None

    for q in queries:
        data = _tavily_search(q, depth="advanced", include_domains=include_domains, max_results=5)
        hits = _extract_urls(data)
        all_hits.extend(hits)
        if not best_answer and isinstance(data, dict):
            best_answer = data.get("answer") or best_answer
        time.sleep(0.2)

    return {"hits": all_hits, "answer": best_answer or ""}


@tool("TechDeduperRanker", description="Dedupe and rank search hits by domain priority and heuristics")
def TechDeduperRanker(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Input: {hits[], domain?} -> Output: {hits[]} deduped and ranked.
    Ranking prioritizes official domain, press/news paths, and concise titles.
    """
    hits: List[Dict[str, str]] = payload.get("hits", [])
    domain: Optional[str] = payload.get("domain")

    seen = set()
    dedup: List[Dict[str, str]] = []
    for h in hits:
        u = h.get("url")
        if not u or u in seen:
            continue
        seen.add(u)
        dedup.append(h)

    def score(h: Dict[str, str]) -> int:
        d = _domain_from_url(h.get("url", ""))
        s = 100 if domain and d.endswith(domain) else 0
        s += 50 if "press" in h.get("url", "") or "news" in h.get("url", "") else 0
        s += max(0, 40 - len(h.get("title", "")) // 4)
        return s

    ranked = sorted(dedup, key=score, reverse=True)
    return {"hits": ranked[:12]}


@tool("TechSummarizer", description="Lightweight extractive summarizer for hits; produce bullets and citations")
def TechSummarizer(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Input: {company, answer?, hits[]} -> Output: {bullets[], citations[]}.
    Extract cue-matching sentences; include top citations.
    """
    company = payload.get("company", "")
    answer = payload.get("answer") or ""
    hits: List[Dict[str, str]] = payload.get("hits", [])

    bullets: List[str] = []
    if answer:
        parts = re.split(r"(?<=[.!?])\s+", answer.strip())
        bullets.extend([p for p in parts if p][:3])

    cues = [
        r"\b(800V|SiC|inverter|heat pump|thermal|BMS|solid[- ]state|4680|LFP|NMC|anode|cathode|recycling|fast charging)\b",
        r"\b(heat exchanger|cooling plate|octovalve|HVAC|TMS)\b",
        r"\b(OTA|autonomy|NOA|L3|ADAS)\b",
        r"\b(production|manufacturing|MRL|supply chain|readiness)\b",
    ]
    rx = re.compile("|".join(cues), re.IGNORECASE)
    for h in hits[:8]:
        content = h.get("content") or ""
        lines = re.split(r"[\r\n\.]+", content)
        for ln in lines:
            if rx.search(ln):
                bullets.append(ln.strip())
                if len(bullets) >= 8:
                    break
        if len(bullets) >= 8:
            break

    cits = [{"title": h.get("title", "")[:120], "url": h.get("url", ""), "content": h.get("content", "")} 
            for h in hits[:6]]

    if not bullets:
        bullets = [f"{company}: No salient technical statements found."]

    return {"bullets": bullets[:10], "citations": cits}


@tool("LLMEvaluator", description="OpenAI-based 6-axis evaluation (TRL/MRL/CRAAP/Materiality/ISSB/OTA) and citation summaries")
def LLMEvaluator(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Input: {company, bullets[], citations[]} -> Output: {evaluation{}, citation_summaries[]}.
    Uses OpenAI chat.completions to score 6 axes and summarize citations.
    """
    company = payload.get("company", "")
    bullets = payload.get("bullets", [])
    citations = payload.get("citations", [])

    # Build evaluation prompt
    eval_prompt = f"""You are an automotive industry analyst. Evaluate the following technical summary for {company} using this 6-axis framework. Use the EXACT scoring rules provided.

FRAMEWORK:
1. 湲곗닠 ?깆닕??(TRL - Technology Readiness Level)
   梨꾩젏 洹쒖튃: TRL 1-9 scale (1=basic principles, 9=actual system proven in operational environment)
   洹쇨굅/怨듭떇異쒖쿂: NASA TRL ?뺤쓽, 1?? ?④퀎. ?꾪궎諛깃낵+3NASA+3NASA+3

2. ?쒖“ 以鍮꾨룄 (MRL - Manufacturing Readiness Level)
   梨꾩젏 洹쒖튃: MRL 1-10 scale (1=basic manufacturing implications identified, 10=full rate production demonstrated)
   洹쇨굅/怨듭떇異쒖쿂: DoD MRL ?곗뒪?щ턿/?뺤쓽. ?꾪궎諛깃낵+3dodmrl.com+3AcqNotes+3

3. 異쒖쿂 ?좊ː쨌寃利앹꽦 (CRAAP)
   梨꾩젏 洹쒖튃: ??ぉ蹂?Currency/Authority/Accuracy/Purpose/Relevance) 0~1?????⑹궛 0~5???섏궛
   洹쇨굅/怨듭떇異쒖쿂: CRAAP ?뚯뒪??猷⑤툕由?媛?대뱶. libguides.mchenry.edu+4Bellevue College+4guides.lib.uchicago.edu+4

4. ?곗뾽 '以묒슂?? ?뺥빀??(Materiality)
   梨꾩젏 洹쒖튃: 0=鍮꾪빑?? 3=遺遺??듭떖, 5=?곗뾽 ?듭떖 ?댁뒋(?? ?먮룞李? 諛곗텧쨌?먮꼫吏쨌?쒗뭹?덉쭏쨌?곗씠?곕낫????
   洹쇨굅/怨듭떇異쒖쿂: SASB Materiality Map/ Finder. SASB+3SASB+3SASB+3

5. 吏??紐⑺몴??怨듭떆 ?덉쭏 (ISSB IFRS S1쨌S2)
   梨꾩젏 洹쒖튃: 0=?щ줈嫄??섏?, 3=?뺤꽦+?쇰? ?섏튂, 5=紐낇솗 KPI/紐⑺몴/湲곗?쨌諛⑸쾿濡?紐낆떆
   洹쇨굅/怨듭떇異쒖쿂: IFRS S1/S2 媛쒖슂/?붽뎄?ы빆. KPMG+3IFRS Foundation+3IFRS Foundation+3

6. OTA 洹쒖젙/?쒖? ?뺥빀??(ISO 24089쨌UNECE R156)
   梨꾩젏 洹쒖튃: 0=?⑥닚 "OTA 媛??, 3=?꾨줈?몄뒪/寃利??멸툒, 5=ISO 24089쨌R156/SUMS 以???붿떆/紐낆떆
   洹쇨굅/怨듭떇異쒖쿂: ISO 24089, UNECE R156 諛??댁꽕. appluslaboratories.com+5ISO+5ISO+5

TECHNICAL SUMMARY:
{chr(10).join(f"- {b}" for b in bullets)}

Respond in this exact JSON format:
{{
  "TRL": {{"score": X (1-9), "rationale": "...", "references": ["source1", "source2"]}},
  "MRL": {{"score": X (1-10), "rationale": "...", "references": ["source1", "source2"]}},
  "CRAAP": {{"score": X (0-5, sum of 5 items each 0-1), "rationale": "...", "references": ["source1", "source2"]}},
  "Materiality": {{"score": X (0, 3, or 5 only), "rationale": "...", "references": ["source1", "source2"]}},
  "ISSB": {{"score": X (0, 3, or 5 only), "rationale": "...", "references": ["source1", "source2"]}},
  "OTA_Compliance": {{"score": X (0, 3, or 5 only), "rationale": "...", "references": ["source1", "source2"]}}
}}
"""

    eval_response = _call_openai([{"role": "user", "content": eval_prompt}])
    
    # Parse evaluation
    evaluation = {}
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', eval_response, re.DOTALL)
        if json_match:
            evaluation = json.loads(json_match.group())
    except Exception:
        evaluation = {
            "TRL": {"score": 0, "rationale": "Evaluation failed", "references": []},
            "MRL": {"score": 0, "rationale": "Evaluation failed", "references": []},
            "CRAAP": {"score": 0, "rationale": "Evaluation failed", "references": []},
            "Materiality": {"score": 0, "rationale": "Evaluation failed", "references": []},
            "ISSB": {"score": 0, "rationale": "Evaluation failed", "references": []},
            "OTA_Compliance": {"score": 0, "rationale": "Evaluation failed", "references": []},
        }

    # Summarize each citation
    citation_summaries = []
    for cit in citations:
        title = cit.get("title", "")
        url = cit.get("url", "")
        content = cit.get("content", "")[:1000]  # Limit content length
        
        if not content:
            citation_summaries.append({"title": title, "url": url, "summary": "No content available"})
            continue
        
        sum_prompt = f"""Summarize this article excerpt in 2-3 sentences focusing on technical details:

Title: {title}
Content: {content}

Summary:"""
        
        summary = _call_openai([{"role": "user", "content": sum_prompt}])
        citation_summaries.append({"title": title, "url": url, "summary": summary.strip()})
        time.sleep(0.3)  # Rate limiting

    return {
        "evaluation": evaluation,
        "citation_summaries": citation_summaries
    }

class TechState(TypedDict):
    company: str
    company_type: str
    domain: Optional[str]
    query_terms: Optional[List[str]]
    raw_hits: Optional[List[Dict[str, str]]]
    ranked_hits: Optional[List[Dict[str, str]]]
    answer: Optional[str]
    summary_bullets: Optional[List[str]]
    citations: Optional[List[Dict[str, str]]]
    evaluation: Optional[Dict[str, Any]]
    citation_summaries: Optional[List[Dict[str, str]]]
    out_dir: str

def resolve_domain(state: TechState) -> TechState:
    r = TechDomainResolver.invoke({"payload": {"company": state["company"]}})
    new = state.copy()
    new["domain"] = r.get("domain")
    return new


def build_queries(state: TechState) -> TechState:
    r = TechQueryBuilder.invoke({"payload": {
        "company": state["company"],
        "company_type": state["company_type"],
    }})
    new = state.copy()
    new["query_terms"] = r.get("query_terms", [])
    return new


def run_search(state: TechState) -> TechState:
    r = TechSearch.invoke({"payload": {
        "company": state["company"],
        "domain": state.get("domain"),
        "query_terms": state.get("query_terms", []),
    }})
    new = state.copy()
    new["raw_hits"] = r.get("hits", [])
    new["answer"] = r.get("answer")
    return new


def dedupe_rank(state: TechState) -> TechState:
    r = TechDeduperRanker.invoke({"payload": {
        "hits": state.get("raw_hits", []),
        "domain": state.get("domain"),
    }})
    new = state.copy()
    new["ranked_hits"] = r.get("hits", [])
    return new


def summarize(state: TechState) -> TechState:
    r = TechSummarizer.invoke({"payload": {
        "company": state["company"],
        "answer": state.get("answer"),
        "hits": state.get("ranked_hits", []),
    }})
    new = state.copy()
    new["summary_bullets"] = r.get("bullets", [])
    new["citations"] = r.get("citations", [])
    return new


def llm_evaluate(state: TechState) -> TechState:
    """New node: LLM evaluation + citation summarization"""
    r = LLMEvaluator.invoke({"payload": {
        "company": state["company"],
        "bullets": state.get("summary_bullets", []),
        "citations": state.get("citations", []),
    }})
    new = state.copy()
    new["evaluation"] = r.get("evaluation", {})
    new["citation_summaries"] = r.get("citation_summaries", [])
    return new

def compile_tech_graph():
    from langgraph.graph import StateGraph
    g = StateGraph(TechState)
    g.add_node("resolve_domain", resolve_domain)
    g.add_node("build_queries", build_queries)
    g.add_node("search", run_search)
    g.add_node("dedupe_rank", dedupe_rank)
    g.add_node("summarize", summarize)
    g.add_node("llm_evaluate", llm_evaluate)
    
    g.set_entry_point("resolve_domain")
    g.add_edge("resolve_domain", "build_queries")
    g.add_edge("build_queries", "search")
    g.add_edge("search", "dedupe_rank")
    g.add_edge("dedupe_rank", "summarize")
    g.add_edge("summarize", "llm_evaluate")
    
    return g.compile()

def run_tech_agent(company: str, company_type: str = "OEM", out_dir: Optional[str] = None) -> Dict[str, Any]:
    compiled = compile_tech_graph()
    base_out = out_dir or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs"))
    os.makedirs(base_out, exist_ok=True)

    init: TechState = {
        "company": company,
        "company_type": company_type,
        "domain": None,
        "query_terms": None,
        "raw_hits": None,
        "ranked_hits": None,
        "answer": None,
        "summary_bullets": None,
        "citations": None,
        "evaluation": None,
        "citation_summaries": None,
        "out_dir": base_out,
    }
    final = compiled.invoke(init)

    # Build JSON output
    output = {
        "company": company,
        "domain": final.get("domain"),
        "query_terms": final.get("query_terms"),
        "summary_bullets": final.get("summary_bullets"),
        "citations": final.get("citation_summaries", []),
        "evaluation": final.get("evaluation", {}),
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "company_type": company_type,
        }
    }

    # Write JSON
    fname = f"tech_summary_{re.sub(r'[^a-z0-9]+','_', company.lower())}.json"
    out_path = os.path.join(base_out, fname)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return {"company": company, "json_path": out_path, "evaluation": output.get("evaluation", {}), "evaluation_summary": {k: v.get("score") for k, v in output.get("evaluation", {}).items()}}


if __name__ == "__main__":
    # Demo: OEM companies only
    demos = [
        "Tesla",
        "BMW",
        "Volkswagen",
    ]
    for comp in demos:
        res = run_tech_agent(comp, "OEM")
        print(f"{comp} ??{res['json_path']}")
        print(f"Scores: {res['evaluation_summary']}\n")

