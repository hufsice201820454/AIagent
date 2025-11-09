# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
except Exception:
    plt = None
    mdates = None

try:
    from langchain.tools import tool
except Exception:
    def tool(*args, **kwargs):
        def deco(fn):
            return fn
        return deco


# -------------------------
# Utilities
# -------------------------

def _outputs_dir() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.normpath(os.path.join(base_dir, "..", "outputs"))
    return os.path.abspath(out_dir)


def _config_dir() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_dir = os.path.normpath(os.path.join(base_dir, "..", "config"))
    return os.path.abspath(cfg_dir)


def _load_whitelist() -> List[Dict[str, Any]]:
    cfg = os.path.join(_config_dir(), "allowed_companies.json")
    with open(cfg, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("companies", [])


def _fmt_currency(v: Optional[float]) -> str:
    try:
        if v is None:
            return "-"
        if abs(v) >= 1e12:
            return f"${v/1e12:.2f}T"
        if abs(v) >= 1e9:
            return f"${v/1e9:.2f}B"
        if abs(v) >= 1e6:
            return f"${v/1e6:.2f}M"
        return f"${v:.2f}"
    except Exception:
        return "-"

def fetch_stock_data(ticker: str, period: str = "3mo") -> Optional[Dict[str, Any]]:
    """Fetch 90-day price data and basic info for a ticker.
    
    Returns:
        {
            "ticker": str,
            "name": str,
            "current": float,
            "prev_close": float,
            "market_cap": float,
            "pe": float,
            "history": DataFrame,
            "change_90d_pct": float
        }
    """
    if yf is None:
        return None
    
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period=period, interval="1d")
        
        if hist is None or hist.empty:
            return None
        
        close = hist["Close"].dropna()
        if close.empty:
            return None
        
        # Basic info
        info = getattr(tk, "fast_info", {})
        current = getattr(info, "last_price", None) or close.iloc[-1]
        prev_close = getattr(info, "previous_close", None)
        market_cap = getattr(info, "market_cap", None)
        
        # Try to get P/E from info dict
        pe = None
        try:
            full_info = tk.info
            pe = full_info.get("trailingPE") or full_info.get("forwardPE")
        except Exception:
            pass
        
        # Calculate 90-day change
        if len(close) >= 2:
            start_price = close.iloc[0]
            end_price = close.iloc[-1]
            change_pct = ((end_price - start_price) / start_price) * 100
        else:
            change_pct = 0.0
        
        return {
            "ticker": ticker,
            "current": float(current),
            "prev_close": float(prev_close) if prev_close else None,
            "market_cap": float(market_cap) if market_cap else None,
            "pe": float(pe) if pe else None,
            "history": hist,
            "change_90d_pct": float(change_pct)
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def create_individual_chart(data: Dict[str, Any], company_name: str, out_dir: str) -> str:
    """Create individual stock chart for OEM companies."""
    if plt is None:
        return "matplotlib_not_available"
    
    ticker = data["ticker"]
    hist = data["history"]
    close = hist["Close"].dropna()
    
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    png_path = os.path.join(out_dir, f"stock_OEM_{ticker}_{ts}.png")
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(close.index, close.values, label=company_name, color="#1f77b4", linewidth=2)
    ax.set_title(f"{company_name} ({ticker}) - Last 90 Days", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Price (USD)", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    # Format x-axis dates
    if mdates:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
    
    fig.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    return png_path


def create_merged_chart(data_list: List[Dict[str, Any]], category: str, out_dir: str) -> str:
    """Create merged chart for Battery or HVAC suppliers."""
    if plt is None:
        return "matplotlib_not_available"
    
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
    png_path = os.path.join(out_dir, f"stock_{category}_merged_{ts}.png")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    
    for idx, data in enumerate(data_list):
        hist = data["history"]
        close = hist["Close"].dropna()
        
        # Normalize to starting price = 100
        normalized = (close / close.iloc[0]) * 100
        
        color = colors[idx % len(colors)]
        ax.plot(normalized.index, normalized.values, 
               label=data["company_name"], color=color, linewidth=2, alpha=0.8)
    
    ax.set_title(f"{category} Suppliers - Normalized Price (Base=100)", 
                fontsize=14, fontweight="bold")
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Normalized Price", fontsize=11)
    ax.axhline(y=100, color="gray", linestyle="--", alpha=0.5, linewidth=1)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9, loc="best")
    
    # Format x-axis dates
    if mdates:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
    
    fig.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    
    return png_path

def analyze_market_trend(oem_data: List[Dict[str, Any]], 
                        supplier_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze overall market trends based on 90-day price changes.
    
    Returns:
        {
            "oem_trend": 1 or 0,
            "supplier_trend": 1 or 0,
            "correlation_score": 1.0, 0.5, or 0.0,
            "oem_avg_change_pct": float,
            "supplier_avg_change_pct": float
        }
    """
    # Calculate average changes
    oem_changes = [d["change_90d_pct"] for d in oem_data if d.get("change_90d_pct") is not None]
    supplier_changes = [d["change_90d_pct"] for d in supplier_data if d.get("change_90d_pct") is not None]
    
    oem_avg = sum(oem_changes) / len(oem_changes) if oem_changes else 0.0
    supplier_avg = sum(supplier_changes) / len(supplier_changes) if supplier_changes else 0.0
    
    # Determine trends (up=1, down=0)
    oem_trend = 1 if oem_avg > 0 else 0
    supplier_trend = 1 if supplier_avg > 0 else 0
    
    # Correlation score
    if oem_trend == 1 and supplier_trend == 1:
        correlation = 1.0  # Both up
    elif oem_trend == 0 and supplier_trend == 0:
        correlation = 0.0  # Both down
    else:
        correlation = 0.5  # One up, one down
    
    return {
        "oem_trend": oem_trend,
        "supplier_trend": supplier_trend,
        "correlation_score": correlation,
        "oem_avg_change_pct": round(oem_avg, 2),
        "supplier_avg_change_pct": round(supplier_avg, 2)
    }


STOCK_EVALUATION_PROMPT = """You are a financial analyst evaluating the electric vehicle (EV) market trends.

## Market Data

### OEM Companies (Electric Vehicle Manufacturers)
{oem_summary}

### Supplier Companies (Battery & HVAC)
{supplier_summary}

### Market Trend Indicators
- OEM Trend: {oem_trend_label} (Avg: {oem_avg_change:.2f}%)
- Supplier Trend: {supplier_trend_label} (Avg: {supplier_avg_change:.2f}%)
- Market Correlation Score: {correlation}/1.0

## Your Task

Analyze the overall EV market situation and provide:

1. **Market Health Assessment**: Is the EV market in a growth phase or correction phase?
2. **OEM-Supplier Dynamics**: What does the correlation (or lack thereof) tell us?
3. **Key Insights**: Notable patterns, outliers, or concerns
4. **Market Outlook**: Brief forward-looking statement

Output as JSON:
```json
{{
  "market_health": "Growth/Correction/Stable/Mixed",
  "market_summary": "2-3 sentence overview of current EV market state",
  "oem_supplier_dynamics": "Brief analysis of relationship between OEMs and suppliers",
  "key_insights": ["Insight 1", "Insight 2", "Insight 3"],
  "outlook": "Brief forward outlook"
}}
```

Be concise, objective, and data-driven."""


def evaluate_market_with_llm(
    oem_data: List[Dict[str, Any]],
    supplier_data: List[Dict[str, Any]],
    trend_analysis: Dict[str, Any],
    llm=None
) -> Dict[str, Any]:
    """Evaluate market trends using LLM."""
    
    # Prepare summaries
    oem_summary = "\n".join([
        f"- {d['company_name']} ({d['ticker']}): "
        f"Current ${d['current']:.2f}, "
        f"90d Change: {d['change_90d_pct']:+.2f}%, "
        f"Market Cap: {_fmt_currency(d['market_cap'])}"
        for d in oem_data
    ])
    
    supplier_summary = "\n".join([
        f"- {d['company_name']} ({d['ticker']}, {d['category']}): "
        f"Current ${d['current']:.2f}, "
        f"90d Change: {d['change_90d_pct']:+.2f}%"
        for d in supplier_data
    ])
    
    if llm is None:
        # Fallback: basic rule-based evaluation
        return _basic_market_evaluation(trend_analysis)
    
    try:
        from langchain.prompts import PromptTemplate
        from langchain.schema.output_parser import StrOutputParser
        
        prompt = PromptTemplate(
            input_variables=["oem_summary", "supplier_summary",
                             "oem_trend_label", "supplier_trend_label",
                             "oem_avg_change", "supplier_avg_change", "correlation"],
            template=STOCK_EVALUATION_PROMPT
        )
        
        chain = prompt | llm | StrOutputParser()
        
        oem_trend_label = "Upward ↑" if trend_analysis["oem_trend"] else "Downward ↓"
        supplier_trend_label = "Upward ↑" if trend_analysis["supplier_trend"] else "Downward ↓"
        result = chain.invoke({
            "oem_summary": oem_summary,
            "supplier_summary": supplier_summary,
            "oem_trend_label": oem_trend_label,
            "supplier_trend_label": supplier_trend_label,
            "oem_avg_change": trend_analysis["oem_avg_change_pct"],
            "supplier_avg_change": trend_analysis["supplier_avg_change_pct"],
            "correlation": trend_analysis["correlation_score"]
        })
        
        # Try to parse JSON
        try:
            return json.loads(result)
        except:
            return {"llm_evaluation": result}
    
    except Exception as e:
        print(f"LLM evaluation failed: {e}")
        return _basic_market_evaluation(trend_analysis)


def _basic_market_evaluation(trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback evaluation without LLM."""
    oem_trend = trend_analysis["oem_trend"]
    supplier_trend = trend_analysis["supplier_trend"]
    correlation = trend_analysis["correlation_score"]
    
    if oem_trend == 1 and supplier_trend == 1:
        health = "Growth"
        summary = "Both OEMs and suppliers showing positive momentum."
    elif oem_trend == 0 and supplier_trend == 0:
        health = "Correction"
        summary = "Market-wide correction affecting both OEMs and suppliers."
    else:
        health = "Mixed"
        summary = "Divergent trends between OEMs and suppliers suggest market uncertainty."
    
    return {
        "market_health": health,
        "market_summary": summary,
        "oem_supplier_dynamics": f"Correlation score: {correlation}",
        "key_insights": [
            f"OEM avg change: {trend_analysis['oem_avg_change_pct']}%",
            f"Supplier avg change: {trend_analysis['supplier_avg_change_pct']}%"
        ],
        "outlook": "Further monitoring required",
        "evaluation_method": "rule_based"
    }


def run_stock_analysis(llm=None, out_dir: Optional[str] = None) -> Dict[str, Any]:
    if yf is None or plt is None:
        raise RuntimeError("yfinance and matplotlib required. pip install yfinance matplotlib")
    
    out_dir = out_dir or _outputs_dir()
    os.makedirs(out_dir, exist_ok=True)
    
    companies = _load_whitelist()
    
    # Separate by category
    oems = [c for c in companies if c.get("category") == "OEM"]
    battery = [c for c in companies if "Battery" in c.get("category", "")]
    hvac = [c for c in companies if c.get("category") == "HVAC"]
    
    print(f"Fetching data for {len(oems)} OEMs, {len(battery)} Battery, {len(hvac)} HVAC suppliers...")
    
    # Fetch OEM data
    oem_data = []
    oem_charts = {}
    for c in oems:
        ticker = c["ticker"]
        name = c["name"]
        print(f"  Fetching {name} ({ticker})...")
        data = fetch_stock_data(ticker)
        if data:
            data["company_name"] = name
            data["category"] = "OEM"
            oem_data.append(data)
            
            # Create individual chart
            chart_path = create_individual_chart(data, name, out_dir)
            oem_charts[ticker] = chart_path
    
    # Fetch Battery supplier data
    battery_data = []
    for c in battery:
        ticker = c["ticker"]
        name = c["name"]
        print(f"  Fetching {name} ({ticker})...")
        data = fetch_stock_data(ticker)
        if data:
            data["company_name"] = name
            data["category"] = "Battery"
            battery_data.append(data)
    
    # Fetch HVAC supplier data
    hvac_data = []
    for c in hvac:
        ticker = c["ticker"]
        name = c["name"]
        print(f"  Fetching {name} ({ticker})...")
        data = fetch_stock_data(ticker)
        if data:
            data["company_name"] = name
            data["category"] = "HVAC"
            hvac_data.append(data)
    
    # Create merged supplier charts
    supplier_charts = {}
    if battery_data:
        supplier_charts["Battery"] = create_merged_chart(battery_data, "Battery", out_dir)
    if hvac_data:
        supplier_charts["HVAC"] = create_merged_chart(hvac_data, "HVAC", out_dir)
    
    # Combine all supplier data
    supplier_data = battery_data + hvac_data
    
    # Analyze trends
    print("\nAnalyzing market trends...")
    trend_indicators = analyze_market_trend(oem_data, supplier_data)
    
    # LLM evaluation
    print("Running LLM evaluation...")
    llm_evaluation = evaluate_market_with_llm(oem_data, supplier_data, trend_indicators, llm)
    
    # Prepare output (remove history DataFrames for JSON serialization)
    oem_output = [{k: v for k, v in d.items() if k != "history"} for d in oem_data]
    supplier_output = [{k: v for k, v in d.items() if k != "history"} for d in supplier_data]
    
    result = {
        "oem_charts": oem_charts,
        "supplier_charts": supplier_charts,
        "oem_data": oem_output,
        "supplier_data": supplier_output,
        "trend_indicators": trend_indicators,
        "llm_evaluation": llm_evaluation
    }
    
    # Save to JSON
    json_path = os.path.join(out_dir, "stock_analysis.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Analysis complete. Results saved to {json_path}")
    print(f"✓ OEM charts: {len(oem_charts)}")
    print(f"✓ Supplier charts: {len(supplier_charts)}")
    print(f"✓ Trend indicators: OEM={trend_indicators['oem_trend']}, "
          f"Supplier={trend_indicators['supplier_trend']}, "
          f"Correlation={trend_indicators['correlation_score']}")
    
    return result


if __name__ == "__main__":
    # Optional: Use LLM for evaluation
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    except Exception:
        llm = None
        print("Warning: LLM not available, using rule-based evaluation")
    
    result = run_stock_analysis(llm=llm)
    print("\n=== Market Summary ===")
    print(json.dumps(result["llm_evaluation"], indent=2, ensure_ascii=False))

