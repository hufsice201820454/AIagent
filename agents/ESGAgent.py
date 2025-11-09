# -*- coding: utf-8 -*-
"""
ESGAgent

Tools: GovESGSearch, CorpESGSearch, ExternalRatings
LangGraph flow: policy -> corporate -> ratings
Outputs full JSON (no HTML)
"""
from __future__ import annotations

import os
import json
import re
from typing import Dict, List, Optional, Any, TypedDict
from urllib import request

try:
    from langchain.tools import tool
except Exception:
    # Fallback decorator if langchain is unavailable
    def tool(*args, **kwargs):
        def deco(fn):
            return fn
        return deco

# Best-effort: load env from evagent/.env if present (for TAVILY_API_KEY, etc.)
def _load_env_from_dotenv() -> None:
    if os.getenv("TAVILY_API_KEY"):
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

# ---------------------------------
# Whitelist (OEM names)
# ---------------------------------
OEM_WHITELIST = {
    "Tesla",
    "Rivian",
    "General Motors",
    "Ford",
    "BYD",
    "Li Auto",
    "XPeng",
    "BMW",
    "Volkswagen",
    "Hyundai",
}

# ---------------------------------
# Tavily helpers
# ---------------------------------
def _tavily_search(query: str, *, depth: str = "basic") -> Dict[str, Any]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {}
    url = "https://api.tavily.com/search"
    body = json.dumps(
        {
            "api_key": api_key,
            "query": query,
            "max_results": 5,
            "include_answer": True,
            "search_depth": depth,
        }
    ).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}

def _parse_year(text: str) -> Optional[int]:
    s = text or ""
    yrs = [int(y) for y in re.findall(r"(20[2-6][0-9])", s)]
    if not yrs:
        return None
    valid = [y for y in yrs if 2024 <= y <= 2065]
    return min(valid) if valid else min(yrs)

def _parse_scopes(text: str) -> List[str]:
    s = (text or "").lower()
    scopes: List[str] = []
    if re.search(r"\bscope\s*1\b|\bs1\b", s):
        scopes.append("S1")
    if re.search(r"\bscope\s*2\b|\bs2\b", s):
        scopes.append("S2")
    if re.search(r"\bscope\s*3\b|\bs3\b", s):
        scopes.append("S3")
    return scopes

# ---------------------------------
# Tools
# ---------------------------------
@tool("GovESGSearch", description="Lookup government ESG/net-zero policies by region via Tavily")
def GovESGSearch(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Lookup government ESG policies by region.

    payload: {"regions": list[str]}
    returns: { region: {"policy": str, "carbon_neutral": int|None, "notes": str} }
    """
    regions: List[str] = payload.get("regions", [])
    api_key = os.getenv("TAVILY_API_KEY")

    def _region_name(code: str) -> str:
        m = {
            "KR": "South Korea",
            "CN": "China",
            "JP": "Japan",
            "EU": "European Union",
            "US": "United States",
            "UK": "United Kingdom",
        }
        return m.get(code.upper(), code)

    out: Dict[str, Any] = {}
    for r in regions:
        rn = _region_name(r)
        if api_key:
            q = f"{rn} government net zero policy target year carbon neutral official"
            data = _tavily_search(q, depth="basic")
            answer = data.get("answer") if isinstance(data, dict) else None
            out[r] = {
                "policy": (answer or "").strip() or "N/A",
                "carbon_neutral": _parse_year(answer or ""),
            }
        else:
            out[r] = {"policy": "N/A", "carbon_neutral": None}
    return out

@tool("CorpESGSearch", description="Summarize OEM corporate ESG targets (year, scope) via Tavily")
def CorpESGSearch(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize OEM corporate ESG targets for allowed companies via Tavily.

    payload: {"oems": list[str]}
    returns: { company: {"target_year": int|None, "scope": list[str], "policy": str} }
    """
    oems: List[str] = payload.get("oems", [])
    api_key = os.getenv("TAVILY_API_KEY")

    res: Dict[str, Any] = {}
    for comp in oems:
        if comp not in OEM_WHITELIST:
            continue
        if api_key:
            q = f"{comp} ESG net zero target year Scope 1 Scope 2 Scope 3 sustainability report"
            data = _tavily_search(q, depth="advanced")
            answer = data.get("answer") if isinstance(data, dict) else None
            res[comp] = {
                "target_year": _parse_year(answer or ""),
                "scope": _parse_scopes(answer or ""),
                "policy": (answer or "").strip() or "N/A",
            }
        else:
            res[comp] = {"target_year": None, "scope": [], "policy": "N/A"}
    return res

@tool("ExternalRatings", description="Fetch external ESG ratings hints (MSCI/CDP) via Tavily search")
def ExternalRatings(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch external ESG ratings hints (MSCI/CDP) via Tavily search.

    payload: {"oems": list[str]}
    returns: { company: {"msci": str|None, "cdp": str|None, "notes": str} }
    """
    api_key = os.getenv("TAVILY_API_KEY")
    companies: List[str] = payload.get("oems", [])
    if not api_key:
        return {c: {"msci": None, "cdp": None} for c in companies}

    def _pick(pattern: str, text: str) -> Optional[str]:
        m = re.search(pattern, text or "", re.IGNORECASE)
        return m.group(0) if m else None

    out: Dict[str, Any] = {}
    for c in companies:
        msci_ans = _tavily_search(f"MSCI ESG rating {c} official", depth="basic")
        cdp_ans = _tavily_search(f"CDP score {c} environmental score official", depth="basic")
        msci = _pick(r"AAA|AA|A|BBB|BB|B|CCC", msci_ans.get("answer") if isinstance(msci_ans, dict) else "")
        cdp = _pick(r"A\+|A-|A|B\+|B|B-|C\+|C|C-|D\+|D|D-", cdp_ans.get("answer") if isinstance(cdp_ans, dict) else "")
        out[c] = {"msci": msci, "cdp": cdp}
    return out

# ---------------------------------
# State
# ---------------------------------
class ESGState(TypedDict):
    regions: List[str]
    oems: List[str]
    gov_esg_findings: Optional[Dict[str, Any]]
    corp_esg_findings: Optional[Dict[str, Any]]
    external_ratings: Optional[Dict[str, Any]]
    out_dir: str

# ---------------------------------
# Nodes
# ---------------------------------
def collect_policy(state: ESGState) -> ESGState:
    gov = GovESGSearch.invoke({"payload": {"regions": state.get("regions", [])}})
    new = state.copy()
    new["gov_esg_findings"] = gov
    return new

def collect_corporate(state: ESGState) -> ESGState:
    oems = [o for o in state.get("oems", []) if o in OEM_WHITELIST]
    corp = CorpESGSearch.invoke({"payload": {"oems": oems}})
    new = state.copy()
    new["corp_esg_findings"] = corp
    return new

def collect_ratings(state: ESGState) -> ESGState:
    oems = [o for o in state.get("oems", []) if o in OEM_WHITELIST]
    ratings = ExternalRatings.invoke({"payload": {"oems": oems}})
    new = state.copy()
    new["external_ratings"] = ratings
    return new

# ---------------------------------
# Graph
# ---------------------------------
def compile_esg_graph():
    from langgraph.graph import StateGraph

    g = StateGraph(ESGState)
    g.add_node("policy", collect_policy)
    g.add_node("corporate", collect_corporate)
    g.add_node("ratings", collect_ratings)
    g.set_entry_point("policy")
    g.add_edge("policy", "corporate")
    g.add_edge("corporate", "ratings")
    return g.compile()

# ---------------------------------
# Runner
# ---------------------------------
def run_esg_agent(regions: List[str], oems: List[str], out_dir: Optional[str] = None):
    compiled = compile_esg_graph()
    base_out = out_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
    os.makedirs(base_out, exist_ok=True)

    init: ESGState = {
        "regions": regions,
        "oems": oems,
        "gov_esg_findings": None,
        "corp_esg_findings": None,
        "external_ratings": None,
        "out_dir": base_out,
    }
    final = compiled.invoke(init)

    # Build structured JSON output
    output_data = {
        "analysis_type": "ESG Summary (OEM only)",
        "regions": final["regions"],
        "government_policies": final["gov_esg_findings"],
        "corporate_esg_goals": final["corp_esg_findings"],
        "external_ratings": final.get("external_ratings", {}),
        "notes": {
            "ghg_protocol_scopes": {
                "scope_1": "Direct emissions from owned/controlled sources (e.g., company vehicles, on-site fuel combustion).",
                "scope_2": "Indirect emissions from purchased electricity, steam, heat, or cooling.",
                "scope_3": "All other indirect emissions across the value chain (upstream & downstream - suppliers, transportation, product use, etc.)."
            },
            "msci_esg_rating": {
                "scale": "AAA to CCC",
                "AAA_AA": "Leader - Strong management of financially relevant ESG risks relative to industry peers.",
                "A_BBB_BB": "Average - Mixed or average track record of managing ESG risks and opportunities.",
                "B_CCC": "Laggard - High exposure and failure to manage significant ESG risks.",
                "description": "Evaluates company resilience to industry-specific sustainability risks. Based on exposure to 35 key ESG issues and management effectiveness. Industry-relative scoring (0-10 scale mapped to letter grades)."
            },
            "cdp_score": {
                "scale": "A to F",
                "A": "Leadership - Environmental leadership with best practices - climate transition plans, supply chain risk management, TCFD/SBTi alignment.",
                "B": "Management - Demonstrates coordinated actions and strategies to manage environmental impacts.",
                "C": "Awareness - Acknowledges environmental issues but taking limited action.",
                "D": "Disclosure - Transparent about environmental impact but minimal evidence of action.",
                "F": "Failure - Failed to provide sufficient information or did not respond to CDP request.",
                "description": "Assesses transparency and action on climate change, water security, and forests. Companies progress through four stages: Disclosure ??Awareness ??Management ??Leadership. Scored separately for Climate, Water, and Forests themes."
            }
        },
        "references": {
            "ghg_protocol": "https://ghgprotocol.org/corporate-standard"
        }
    }

    # Save as JSON only
    out_path = os.path.join(base_out, "esg_analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    return {
        "gov": final["gov_esg_findings"],
        "corp": final["corp_esg_findings"],
        "ratings": final.get("external_ratings", {}),
        "json_path": out_path,
    }

if __name__ == "__main__":
    res = run_esg_agent(
        regions=["KR", "CN", "JP", "EU", "US", "UK"],
        oems=["Hyundai", "Tesla", "GM", "Ford", "BYD", "Toyota", "Volkswagen"],
    )
    print("ESG Analysis JSON:", res["json_path"])
