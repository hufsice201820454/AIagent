# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import json
import asyncio
from typing import Any, Dict, List, Optional, TypedDict

# Import sub-agents
try:
    from .TechSearchAgent import run_tech_agent
    from .ValueChainAgent import run_valuechain_agent
    from .StockAnalyzerAgent import run_stock_analysis
    from .ESGAgent import run_esg_agent
except ImportError:
    # Fallback for standalone execution
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from TechSearchAgent import run_tech_agent
    from ValueChainAgent import run_valuechain_agent
    from StockAnalyzerAgent import run_stock_analysis
    from ESGAgent import run_esg_agent

def _load_env_from_dotenv() -> None:
    if os.getenv("OPENAI_API_KEY"):
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

def _call_openai(messages: List[Dict[str, str]], model: str = "gpt-4o-mini", temperature: float = 0.3) -> str:
    """Call OpenAI Chat API; return assistant message content."""
    from urllib import request
    
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


VALIDATION_PROMPT = """You are a quality control analyst. Check if the agent output contains all required evaluation metrics.

Agent: {agent_name}
Required Metrics: {required_metrics}

Agent Output:
{agent_output}

Respond with ONLY a JSON object:
{{
  "valid": true/false,
  "missing_fields": ["field1", "field2"],
  "error_message": "brief description if invalid"
}}
"""

class SupervisorState(TypedDict):
    companies: List[str]  # OEM companies to analyze
    regions: List[str]    # Regions for ESG analysis
    out_dir: str
    
    # Agent results
    tech_results: Optional[Dict[str, Any]]
    valuechain_results: Optional[Dict[str, Any]]
    stock_results: Optional[Dict[str, Any]]
    esg_results: Optional[Dict[str, Any]]
    
    # Validation status
    validation_status: Dict[str, bool]  # {agent_name: is_valid}
    retry_count: Dict[str, int]         # {agent_name: retry_count}
    
    # Final status
    final_status: int  # 1 = success, 0 = failure
    error_log: Dict[str, str]  # {agent_name: error_message}


async def run_tech_async(company: str, out_dir: str) -> Dict[str, Any]:
    """Run TechSearchAgent asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_tech_agent, company, "OEM", out_dir)


async def run_valuechain_async(out_dir: str) -> Dict[str, Any]:
    """Run ValueChainAgent asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_valuechain_agent, None, out_dir, None, None)


async def run_stock_async(out_dir: str) -> Dict[str, Any]:
    """Run StockAnalyzerAgent asynchronously"""
    loop = asyncio.get_event_loop()
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    except Exception:
        llm = None
    return await loop.run_in_executor(None, run_stock_analysis, llm, out_dir)


async def run_esg_async(regions: List[str], oems: List[str], out_dir: str) -> Dict[str, Any]:
    """Run ESGAgent asynchronously"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_esg_agent, regions, oems, out_dir)

def validate_tech_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Validate TechSearchAgent output (single or multi-company)."""
    required_eval_keys = ["TRL", "MRL", "CRAAP", "Materiality", "ISSB", "OTA_Compliance"]

    missing: List[str] = []

    def _check_eval(prefix: str, eval_obj: Any) -> None:
        if not isinstance(eval_obj, dict):
            missing.append(f"{prefix}evaluation")
            return
        for key in required_eval_keys:
            if key not in eval_obj:
                missing.append(f"{prefix}evaluation.{key}")
            elif not isinstance(eval_obj[key], dict) or "score" not in eval_obj[key]:
                missing.append(f"{prefix}evaluation.{key}.score")

    if isinstance(results, dict) and "evaluation" in results:
        _check_eval("", results.get("evaluation"))
    elif isinstance(results, dict):
        for company, item in results.items():
            if isinstance(item, dict) and "evaluation" in item:
                _check_eval(f"{company}.", item.get("evaluation"))
            else:
                missing.append(f"{company}.evaluation")
    else:
        missing.append("evaluation")

    valid = len(missing) == 0
    return {
        "valid": valid,
        "missing_fields": missing,
        "error_message": f"Missing required fields: {', '.join(missing)}" if missing else ""
    }


def validate_valuechain_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ValueChainAgent output"""
    required = ["jit_evaluation"]
    
    missing = []
    if "jit_evaluation" not in results:
        missing.append("jit_evaluation")
    else:
        jit = results["jit_evaluation"]
        if "companies" not in jit or not isinstance(jit["companies"], list):
            missing.append("jit_evaluation.companies")
        else:
            # Check if companies have required scores
            for idx, company in enumerate(jit["companies"]):
                if "jit_score" not in company:
                    missing.append(f"jit_evaluation.companies[{idx}].jit_score")
                if "regional_score" not in company:
                    missing.append(f"jit_evaluation.companies[{idx}].regional_score")
    
    valid = len(missing) == 0
    return {
        "valid": valid,
        "missing_fields": missing,
        "error_message": f"Missing required fields: {', '.join(missing)}" if missing else ""
    }


def validate_stock_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Validate StockAnalyzerAgent output"""
    required = ["trend_indicators"]
    required_trend_keys = ["oem_trend", "supplier_trend", "correlation_score"]
    
    missing = []
    if "trend_indicators" not in results:
        missing.append("trend_indicators")
    else:
        trend = results["trend_indicators"]
        for key in required_trend_keys:
            if key not in trend:
                missing.append(f"trend_indicators.{key}")
    
    valid = len(missing) == 0
    return {
        "valid": valid,
        "missing_fields": missing,
        "error_message": f"Missing required fields: {', '.join(missing)}" if missing else ""
    }


def validate_esg_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Validate ESGAgent output"""
    required = ["gov", "corp", "ratings"]
    
    missing = []
    for key in required:
        if key not in results:
            missing.append(key)
        elif not results[key]:  # Check if dict is not empty
            missing.append(f"{key} (empty)")
    
    valid = len(missing) == 0
    return {
        "valid": valid,
        "missing_fields": missing,
        "error_message": f"Missing required fields: {', '.join(missing)}" if missing else ""
    }

async def run_agents_parallel(state: SupervisorState) -> SupervisorState:
    """Run all 4 agents in parallel"""
    companies = state["companies"]
    regions = state.get("regions", ["KR", "CN", "JP", "EU", "US"])
    out_dir = state["out_dir"]
    
    # Prepare Tech tasks for all OEMs
    tech_companies = companies if companies else ["Tesla"]

    async def run_all_tech() -> Dict[str, Any]:
        subtasks = [run_tech_async(c, out_dir) for c in tech_companies]
        subresults = await asyncio.gather(*subtasks, return_exceptions=True)
        mapping: Dict[str, Any] = {}
        for comp, res in zip(tech_companies, subresults):
            if not isinstance(res, Exception) and isinstance(res, dict):
                mapping[comp] = res
            else:
                mapping[comp] = {"error": str(res)} if isinstance(res, Exception) else {"error": "invalid_result"}
        return mapping

    # Run all agents in parallel (tech batch + others)
    tasks = [
        asyncio.create_task(run_all_tech()),
        run_valuechain_async(out_dir),
        run_stock_async(out_dir),
        run_esg_async(regions, companies, out_dir),
    ]

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        results = [None, None, None, None]

    new = state.copy()
    new["tech_results"] = results[0] if not isinstance(results[0], Exception) else None
    new["valuechain_results"] = results[1] if not isinstance(results[1], Exception) else None
    new["stock_results"] = results[2] if not isinstance(results[2], Exception) else None
    new["esg_results"] = results[3] if not isinstance(results[3], Exception) else None
    
    # Initialize retry counters if not present
    if "retry_count" not in new:
        new["retry_count"] = {
            "tech": 0,
            "valuechain": 0,
            "stock": 0,
            "esg": 0,
        }
    
    return new


def validate_results(state: SupervisorState) -> SupervisorState:
    """Validate all agent results"""
    validations = {
        "tech": validate_tech_results(state.get("tech_results") or {}),
        "valuechain": validate_valuechain_results(state.get("valuechain_results") or {}),
        "stock": validate_stock_results(state.get("stock_results") or {}),
        "esg": validate_esg_results(state.get("esg_results") or {}),
    }
    
    new = state.copy()
    new["validation_status"] = {k: v["valid"] for k, v in validations.items()}
    
    # Update error log for failed validations
    error_log = state.get("error_log", {})
    for agent, validation in validations.items():
        if not validation["valid"]:
            error_log[agent] = validation["error_message"]
    new["error_log"] = error_log
    
    return new


def check_completion(state: SupervisorState) -> str:
    """Check if all validations passed or max retries reached"""
    validation_status = state.get("validation_status", {})
    retry_count = state.get("retry_count", {})
    
    # Check if all agents validated successfully
    if all(validation_status.values()):
        return "finish"
    
    # Check if any agent needs retry and hasn't exceeded max retries
    for agent, is_valid in validation_status.items():
        if not is_valid and retry_count.get(agent, 0) < 2:
            return "retry"
    
    # Max retries reached for all failed agents
    return "finish"


async def retry_failed_agents(state: SupervisorState) -> SupervisorState:
    """Retry only the failed agents"""
    validation_status = state.get("validation_status", {})
    retry_count = state.get("retry_count", {})
    companies = state["companies"]
    regions = state.get("regions", ["KR", "CN", "JP", "EU", "US"])
    out_dir = state["out_dir"]
    
    tasks = []
    agent_names = []
    
    # Build task list for failed agents
    if not validation_status.get("tech") and retry_count.get("tech", 0) < 2:
        async def rerun_all_tech():
            tech_companies = companies if companies else ["Tesla"]
            subtasks = [run_tech_async(c, out_dir) for c in tech_companies]
            subresults = await asyncio.gather(*subtasks, return_exceptions=True)
            mapping: Dict[str, Any] = {}
            for comp, res in zip(tech_companies, subresults):
                if not isinstance(res, Exception) and isinstance(res, dict):
                    mapping[comp] = res
                else:
                    mapping[comp] = {"error": str(res)} if isinstance(res, Exception) else {"error": "invalid_result"}
            return mapping
        tasks.append(rerun_all_tech())
        agent_names.append("tech")
    
    if not validation_status.get("valuechain") and retry_count.get("valuechain", 0) < 2:
        tasks.append(run_valuechain_async(out_dir))
        agent_names.append("valuechain")
    
    if not validation_status.get("stock") and retry_count.get("stock", 0) < 2:
        tasks.append(run_stock_async(out_dir))
        agent_names.append("stock")
    
    if not validation_status.get("esg") and retry_count.get("esg", 0) < 2:
        tasks.append(run_esg_async(regions, companies, out_dir))
        agent_names.append("esg")
    
    # Run retry tasks in parallel
    if tasks:
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception:
            results = [None] * len(tasks)
        
        # Update results
        new = state.copy()
        for agent_name, result in zip(agent_names, results):
            if not isinstance(result, Exception) and result:
                new[f"{agent_name}_results"] = result
            # Increment retry count
            new["retry_count"][agent_name] = retry_count.get(agent_name, 0) + 1
        
        return new
    
    return state


def finalize_status(state: SupervisorState) -> SupervisorState:
    """Set final status based on validation results"""
    validation_status = state.get("validation_status", {})
    all_valid = all(validation_status.values())
    
    new = state.copy()
    new["final_status"] = 1 if all_valid else 0
    
    # Save summary to file
    out_dir = state["out_dir"]
    summary = {
        "final_status": new["final_status"],
        "validation_status": validation_status,
        "retry_count": state.get("retry_count", {}),
        "error_log": state.get("error_log", {}),
        "agent_results": {
            "tech": bool(state.get("tech_results")),
            "valuechain": bool(state.get("valuechain_results")),
            "stock": bool(state.get("stock_results")),
            "esg": bool(state.get("esg_results")),
        }
    }
    
    summary_path = os.path.join(out_dir, "supervisor_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return new

def compile_supervisor_graph():
    from langgraph.graph import StateGraph
    
    graph = StateGraph(SupervisorState)
    
    # Add nodes
    graph.add_node("run_agents", lambda s: asyncio.run(run_agents_parallel(s)))
    graph.add_node("validate", validate_results)
    graph.add_node("retry", lambda s: asyncio.run(retry_failed_agents(s)))
    graph.add_node("finalize", finalize_status)
    
    # Set entry point
    graph.set_entry_point("run_agents")
    
    # Add edges
    graph.add_edge("run_agents", "validate")
    graph.add_conditional_edges(
        "validate",
        check_completion,
        {
            "retry": "retry",
            "finish": "finalize",
        }
    )
    graph.add_edge("retry", "validate")
    
    return graph.compile()



def run_supervisor(
    companies: List[str],
    regions: Optional[List[str]] = None,
    out_dir: Optional[str] = None
) -> Dict[str, Any]:

    base_dir = os.path.dirname(os.path.abspath(__file__))
    resolved_out = out_dir or os.path.normpath(os.path.join(base_dir, "..", "outputs"))
    os.makedirs(resolved_out, exist_ok=True)
    
    compiled = compile_supervisor_graph()
    
    resolved_regions = regions or ["KR", "CN", "JP", "EU", "US"]
    
    init_state: SupervisorState = {
        "companies": companies,
        "regions": resolved_regions,
        "out_dir": resolved_out,
        "tech_results": None,
        "valuechain_results": None,
        "stock_results": None,
        "esg_results": None,
        "validation_status": {},
        "retry_count": {},
        "final_status": 0,
        "error_log": {},
    }
    
    final_state = compiled.invoke(init_state)
    
    return {
        "final_status": final_state["final_status"],
        "validation_status": final_state.get("validation_status", {}),
        "error_log": final_state.get("error_log", {}),
        "retry_count": final_state.get("retry_count", {}),
        "companies": companies,  # ← 추가
        "regions": resolved_regions,  # ← 추가
        "tech_results": final_state.get("tech_results"),
        "valuechain_results": final_state.get("valuechain_results"),
        "stock_results": final_state.get("stock_results"),
        "esg_results": final_state.get("esg_results"),
    }


if __name__ == "__main__":
    # Demo run
    result = run_supervisor(
        companies=["Tesla", "BMW", "BYD"],
        regions=["KR", "CN", "JP", "EU", "US"]
    )
    
    print("\n=== Supervisor Execution Summary ===")
    print(f"Final Status: {'SUCCESS ✓' if result['final_status'] == 1 else 'FAILED ✗'}")
    print(f"\nValidation Status:")
    for agent, status in result['validation_status'].items():
        print(f"  {agent}: {'✓' if status else '✗'}")
    
    if result['error_log']:
        print(f"\nErrors:")
        for agent, error in result['error_log'].items():
            print(f"  {agent}: {error}")
    
    print(f"\nRetry Count:")
    for agent, count in result['retry_count'].items():
        print(f"  {agent}: {count}")
