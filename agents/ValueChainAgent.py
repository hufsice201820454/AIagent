# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import json
import math
from typing import Dict, Optional, TypedDict, Any, List
import time
import pandas as pd
import plotly.express as px  # lightweight world map

LAT_CANDIDATES = ["lat", "latitude", "y", "y_coord"]
LON_CANDIDATES = ["lon", "lng", "longitude", "x", "x_coord"]
CITY_CANDIDATES = ["city", "city_name", "location", "plant_city"]
COUNTRY_CANDIDATES = ["country", "nation", "country_name"]
PLANT_CANDIDATES = ["plant", "plant_name", "facility"]

def _infer_coord_columns(df: pd.DataFrame) -> tuple[str, str]:
    cols = {c.lower(): c for c in df.columns}
    lat_col = next((cols[c] for c in LAT_CANDIDATES if c in cols), None)
    lon_col = next((cols[c] for c in LON_CANDIDATES if c in cols), None)
    if not lat_col or not lon_col:
        raise ValueError(
            f"Could not infer latitude/longitude columns from: {list(df.columns)}\n"
            f"Accepted lat={LAT_CANDIDATES}, lon={LON_CANDIDATES}"
        )
    return lat_col, lon_col


def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    cols = {c.lower(): c for c in df.columns}
    return next((cols[c] for c in candidates if c in cols), None)


def _ensure_latlon(
    df: pd.DataFrame,
    *,
    cache_path: Optional[str] = None,
    throttle_sec: float = 1.0,
) -> pd.DataFrame:
    try:
        _infer_coord_columns(df)
        return df
    except Exception:
        pass

    city_col = _find_col(df, CITY_CANDIDATES)
    country_col = _find_col(df, COUNTRY_CANDIDATES)
    plant_col = _find_col(df, PLANT_CANDIDATES)
    if not city_col or not country_col:
        raise ValueError(
            "Missing coordinate columns and cannot geocode: need City and Country columns."
        )

    try:
        from geopy.geocoders import Nominatim
    except Exception:
        raise ValueError(
            "No lat/lon columns and geopy not installed. Install with `pip install geopy` or add lat/lon columns."
        )

    # Load cache
    cache: Dict[str, tuple[float, float]] = {}
    if cache_path and os.path.isfile(cache_path):
        try:
            cache_df = pd.read_csv(cache_path)
            for _, r in cache_df.iterrows():
                cache[str(r["query"])]= (float(r["lat"]), float(r["lon"]))
        except Exception:
            pass

    geolocator = Nominatim(user_agent="evagent_valuechain", timeout=15)
    to_cache: list[tuple[str, float, float]] = []

    lat_name = "lat"
    lon_name = "lon"
    out_df = df.copy()
    if lat_name not in out_df.columns:
        out_df[lat_name] = None
    if lon_name not in out_df.columns:
        out_df[lon_name] = None

    for idx, row in out_df.iterrows():
        # Skip if already populated
        if pd.notna(row.get(lat_name)) and pd.notna(row.get(lon_name)):
            continue

        parts = []
        if plant_col and pd.notna(row.get(plant_col)):
            parts.append(str(row.get(plant_col)))
        if city_col and pd.notna(row.get(city_col)):
            parts.append(str(row.get(city_col)))
        if country_col and pd.notna(row.get(country_col)):
            parts.append(str(row.get(country_col)))
        if not parts:
            continue
        query = ", ".join(parts)

        if query in cache:
            la, lo = cache[query]
            out_df.at[idx, lat_name] = la
            out_df.at[idx, lon_name] = lo
            continue

        try:
            loc = geolocator.geocode(query)
            if loc is None and city_col and country_col:
                cc_key = f"{row.get(city_col)}, {row.get(country_col)}"
                if cc_key in cache:
                    la, lo = cache[cc_key]
                    out_df.at[idx, lat_name] = la
                    out_df.at[idx, lon_name] = lo
                    continue
                loc = geolocator.geocode(cc_key)
            if loc is not None:
                la = float(loc.latitude)
                lo = float(loc.longitude)
                out_df.at[idx, lat_name] = la
                out_df.at[idx, lon_name] = lo
                to_cache.append((query, la, lo))
            time.sleep(throttle_sec)
        except Exception:
            continue

    # Persist cache
    if cache_path and to_cache:
        try:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            mode = "a" if os.path.isfile(cache_path) else "w"
            with open(cache_path, mode, encoding="utf-8") as f:
                if mode == "w":
                    f.write("query,lat,lon\n")
                for q, la, lo in to_cache:
                    f.write(f"{q},{la},{lo}\n")
        except Exception:
            pass

    # Verify
    _infer_coord_columns(out_df)
    return out_df


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on Earth in km."""
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

try:
    from langchain.tools import tool
except Exception:
    # simple passthrough decorator if langchain not available
    def tool(*args, **kwargs):
        def deco(fn):
            return fn
        return deco


@tool("visualization_tool", description="Create plotly scatter_geo map PNG for OEM and supplier plants")
def visualization_tool(payload: Dict[str, Any]) -> str:
    out_dir = payload.get("out_dir", "outputs")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(out_dir):
        out_dir = os.path.normpath(os.path.join(base_dir, "..", out_dir))
    os.makedirs(out_dir, exist_ok=True)

    oem_df = pd.read_json(payload["oem_df"]) if isinstance(payload.get("oem_df"), str) else payload["oem_df"]
    supplier_df = pd.read_json(payload["supplier_df"]) if isinstance(payload.get("supplier_df"), str) else payload["supplier_df"]

    o_lat, o_lon = _infer_coord_columns(oem_df)
    s_lat, s_lon = _infer_coord_columns(supplier_df)
    oem_df = oem_df.rename(columns={o_lat: "lat", o_lon: "lon"}).copy()
    supplier_df = supplier_df.rename(columns={s_lat: "lat", s_lon: "lon"}).copy()

    oem_df["series"] = "OEM"
    seg = supplier_df.get("_seg")
    supplier_df["series"] = seg.where(seg.isin(["battery", "hvac"]) , "Supplier").map({
        "battery": "Battery",
        "hvac": "HVAC",
    }).fillna("Supplier")

    all_df = pd.concat([oem_df, supplier_df], ignore_index=True)

    hover_cols = [c for c in [
        "company", "oem", "plant_name", "plant", "city", "country", "status", "type"
    ] if c in all_df.columns]

    fig = px.scatter_geo(
        all_df,
        lat="lat",
        lon="lon",
        color="series",
        color_discrete_map={
            "OEM": "#1f77b4",      # blue
            "Battery": "#FFD700",  # yellow
            "HVAC": "#d62728",     # red
            "Supplier": "#ff7f0e", # orange fallback
        },
        labels={"series": "Category"},
        hover_name=hover_cols[0] if hover_cols else None,
        hover_data=hover_cols[1:] if len(hover_cols) > 1 else None,
        projection="natural earth",
        title="OEM & Supplier Plants",
    )
    fig.update_layout(showlegend=True, legend_title_text="Category",
                      legend=dict(orientation="h", y=-0.1))

    png_path = os.path.join(out_dir, "map_oem_suppliers.png")
    try:
        fig.write_image(png_path, format="png", width=1920, height=1080, scale=2, engine="kaleido")
    except Exception as e:
        try:
            img_bytes = fig.to_image(format="png", width=1920, height=1080, scale=2)
            with open(png_path, "wb") as f:
                f.write(img_bytes)
        except Exception as e2:
            raise RuntimeError(
                f"Failed to export PNG. Install kaleido: pip install kaleido\n"
                f"write_image error: {e}\n"
                f"to_image error: {e2}"
            )

    return png_path


def generate_jit_analysis(counts: Dict[str, Dict[str, int]], out_dir: str) -> Dict[str, Any]:
    companies = []
    for name, data in sorted(counts.items()):
        companies.append({
            "company": name,
            "suppliers_within_66km": data["within_66km"],
            "suppliers_within_140km": data["within_140km"]
        })
    
    analysis = {
        "analysis_type": "JIT Supply Chain Proximity Analysis",
        "description": "Supplier count within proximity thresholds (66km and 140km from OEM plants)",
        "companies": companies
    }
    
    # Save to JSON
    json_path = os.path.join(out_dir, "jit_analysis.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    return analysis


JIT_EVALUATION_PROMPT = """You are a supply chain data analyst. You will receive supplier proximity data for electric vehicle manufacturers.

## Data Format
{jit_analysis}

## Task
Simply format this data in a clear, readable manner for presentation. The counts themselves are the scores.

For each company, present:
- Company name
- Number of suppliers within 66km (66km score)
- Number of suppliers within 140km (140km score)

Output as clean JSON:
```json
{{
  "companies": [
    {{
      "company": "Company Name",
      "66km_counts": <count within 66km>,
      "140km_counts": <count within 140km>
    }}
  ]
}}
```

Do not add interpretations, ratings, or evaluations. Just present the counts as scores."""


def evaluate_jit_with_llm(jit_analysis: Dict[str, Any], llm=None) -> Dict[str, Any]:
    if llm is None:
        # Return counts directly as scores
        return _format_jit_scores(jit_analysis)
    
    try:
        from langchain.prompts import PromptTemplate
        from langchain.schema.output_parser import StrOutputParser
        
        prompt = PromptTemplate(
            input_variables=["jit_analysis"],
            template=JIT_EVALUATION_PROMPT
        )
        
        chain = prompt | llm | StrOutputParser()
        
        result = chain.invoke({
            "jit_analysis": json.dumps(jit_analysis, indent=2, ensure_ascii=False)
        })
        
        # Try to parse JSON response
        try:
            return json.loads(result)
        except:
            # If parsing fails, return direct format
            return _format_jit_scores(jit_analysis)
            
    except Exception as e:
        print(f"LLM formatting failed: {e}")
        return _format_jit_scores(jit_analysis)


def _format_jit_scores(jit_analysis: Dict[str, Any]) -> Dict[str, Any]:
    companies = []
    for company in jit_analysis["companies"]:
        companies.append({
            "company": company["company"],
            "jit_score": company["suppliers_within_66km"],
            "regional_score": company["suppliers_within_140km"]
        })
    
    return {"companies": companies}

def _default_data_dir() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, "..", "data"))


class VCState(TypedDict):
    """ValueChain Agent State"""
    data_dir: str
    out_dir: str
    oem_df: Optional[pd.DataFrame]
    sup_battery_df: Optional[pd.DataFrame]
    sup_hvac_df: Optional[pd.DataFrame]
    supplier_df: Optional[pd.DataFrame]
    counts_json: Optional[Dict[str, Dict[str, int]]]
    jit_analysis: Optional[Dict[str, Any]]
    jit_evaluation: Optional[Dict[str, Any]]
    map_path: Optional[str]
    thresholds_km: Dict[str, float]  # {"near": 66, "region": 140}
    llm: Optional[Any]  # Optional LLM for evaluation

def load_csvs(state: VCState) -> VCState:
    # Resolve data_dir robustly (fallback to project-relative data/)
    data_dir = state.get("data_dir") or _default_data_dir()
    data_dir = os.path.abspath(data_dir)
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(
            f"ValueChainAgent: data_dir not found: {data_dir}\n"
            "Hint: expected CSVs under <project>/data."
        )

    # Known filenames from the project screenshot
    oem_path = os.path.join(data_dir, "ev_factories_full_with_status.csv")
    bat_path = os.path.join(data_dir, "ev_battery_suppliers_plants_status.csv")
    hvac_path = os.path.join(data_dir, "HVAC_Supplier_Plants_FINAL.csv")

    for p in [oem_path, bat_path, hvac_path]:
        if not os.path.isfile(p):
            raise FileNotFoundError(
                f"Missing CSV: {p}\n"
                "Required files: ev_factories_full_with_status.csv, "
                "ev_battery_suppliers_plants_status.csv, HVAC_Supplier_Plants_FINAL.csv"
            )

    oem_df = pd.read_csv(oem_path)
    sup_battery_df = pd.read_csv(bat_path)
    sup_hvac_df = pd.read_csv(hvac_path)

    # Ensure coordinates exist; if not, geocode by City/Country
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_csv = os.path.normpath(os.path.join(base_dir, "..", "db", "geocode_cache.csv"))
    oem_df = _ensure_latlon(oem_df, cache_path=cache_csv)
    sup_battery_df = _ensure_latlon(sup_battery_df, cache_path=cache_csv)
    sup_hvac_df = _ensure_latlon(sup_hvac_df, cache_path=cache_csv)

    supplier_df = pd.concat(
        [sup_battery_df.assign(_seg="battery"), sup_hvac_df.assign(_seg="hvac")],
        ignore_index=True,
    )

    new = state.copy()
    new.update({
        "data_dir": data_dir,
        "oem_df": oem_df,
        "sup_battery_df": sup_battery_df,
        "sup_hvac_df": sup_hvac_df,
        "supplier_df": supplier_df,
    })
    return new


def build_maps(state: VCState) -> VCState:
    # Use the tool to create PNG map (OEM + suppliers)
    if px is None:
        new = state.copy()
        new["map_path"] = None
        return new

    # Normalize to absolute so downstream tools can always find it
    out_dir = os.path.abspath(state["out_dir"])
    os.makedirs(out_dir, exist_ok=True)

    # LangChain Tool expects a single arg named `payload`
    path = visualization_tool.invoke({
        "payload": {
            "oem_df": state["oem_df"],
            "supplier_df": state["supplier_df"],
            "out_dir": out_dir,
        }
    })
    new = state.copy()
    new["map_path"] = path
    return new


def count_suppliers(state: VCState) -> VCState:
    oem_df = state["oem_df"].copy()
    supplier_df = state["supplier_df"].copy()

    o_lat, o_lon = _infer_coord_columns(oem_df)
    s_lat, s_lon = _infer_coord_columns(supplier_df)

    near_km = float(state["thresholds_km"].get("near", 66))
    region_km = float(state["thresholds_km"].get("region", 140))

    # Choose company label (aggregate by company, not plant)
    cols = {c.lower(): c for c in oem_df.columns}
    company_label = None
    for cand in ["company", "oem"]:
        if cand in cols:
            company_label = cols[cand]
            break
    if not company_label:
        for cand in ["plant_name", "plant"]:
            if cand in cols:
                company_label = cols[cand]
                break
        else:
            company_label = o_lat

    results: Dict[str, Dict[str, int]] = {}

    sup_coords = supplier_df[[s_lat, s_lon]].to_numpy()

    for idx, row in oem_df.iterrows():
        comp_name = str(row.get(company_label, f"oem_{idx}"))
        lat1 = float(row[o_lat]); lon1 = float(row[o_lon])

        c66 = 0; c140 = 0
        for lat2, lon2 in sup_coords:
            try:
                d = haversine_km(lat1, lon1, float(lat2), float(lon2))
            except Exception:
                continue
            if d <= near_km:
                c66 += 1
            if d <= region_km:
                c140 += 1

        prev = results.get(comp_name, {"within_66km": 0, "within_140km": 0})
        prev["within_66km"] += c66
        prev["within_140km"] += c140
        results[comp_name] = prev

    new = state.copy()
    new["counts_json"] = results
    return new


def analyze_jit(state: VCState) -> VCState:
    """Generate structured JIT analysis from supplier counts"""
    counts = state["counts_json"]
    out_dir = os.path.abspath(state["out_dir"])
    os.makedirs(out_dir, exist_ok=True)
    
    jit_analysis = generate_jit_analysis(counts, out_dir)
    
    new = state.copy()
    new["jit_analysis"] = jit_analysis
    return new


def evaluate_with_llm(state: VCState) -> VCState:
    """Evaluate JIT capabilities using LLM chain"""
    jit_analysis = state["jit_analysis"]
    llm = state.get("llm")
    
    evaluation = evaluate_jit_with_llm(jit_analysis, llm)
    
    # Save evaluation results
    out_dir = os.path.abspath(state["out_dir"])
    eval_path = os.path.join(out_dir, "jit_evaluation.json")
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2, ensure_ascii=False)
    
    new = state.copy()
    new["jit_evaluation"] = evaluation
    return new

def compile_valuechain_graph() -> "CompiledGraph":
    from langgraph.graph import StateGraph

    graph = StateGraph(VCState)

    graph.add_node("load_csvs", load_csvs)
    graph.add_node("build_maps", build_maps)
    graph.add_node("count_suppliers", count_suppliers)
    graph.add_node("analyze_jit", analyze_jit)
    graph.add_node("evaluate_with_llm", evaluate_with_llm)

    graph.set_entry_point("load_csvs")
    graph.add_edge("load_csvs", "build_maps")
    graph.add_edge("build_maps", "count_suppliers")
    graph.add_edge("count_suppliers", "analyze_jit")
    graph.add_edge("analyze_jit", "evaluate_with_llm")

    return graph.compile()

def run_valuechain_agent(
    data_dir: Optional[str] = None,
    out_dir: Optional[str] = None,
    thresholds_km: Optional[Dict[str, float]] = None,
    llm = None
) -> Dict[str, Any]:
    resolved_data = data_dir or _default_data_dir()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    resolved_out = out_dir or os.path.normpath(os.path.join(base_dir, "..", "outputs"))
    resolved_out = os.path.abspath(resolved_out)

    compiled = compile_valuechain_graph()

    init_state: VCState = {
        "data_dir": resolved_data,
        "out_dir": resolved_out,
        "oem_df": None,
        "sup_battery_df": None,
        "sup_hvac_df": None,
        "supplier_df": None,
        "counts_json": None,
        "jit_analysis": None,
        "jit_evaluation": None,
        "map_path": None,
        "thresholds_km": thresholds_km or {"near": 66.0, "region": 140.0},
        "llm": llm,
    }

    final_state = compiled.invoke(init_state)
    return {
        "map_path": final_state.get("map_path"),
        "counts": final_state.get("counts_json", {}),
        "jit_analysis": final_state.get("jit_analysis", {}),
        "jit_evaluation": final_state.get("jit_evaluation", {}),
    }

if __name__ == "__main__":
    summary = run_valuechain_agent()
    print("Map:", summary["map_path"])
    print("\n=== JIT Analysis Summary ===")
    if "jit_analysis" in summary:
        print(f"Companies analyzed: {len(summary['jit_analysis']['companies'])}")
    
    print("\n=== JIT Evaluation Scores ===")
    if "jit_evaluation" in summary and "companies" in summary["jit_evaluation"]:
        for score in summary["jit_evaluation"]["companies"][:5]:
            print(f"{score['company']}: JIT={score['jit_score']}, Regional={score['regional_score']}")
