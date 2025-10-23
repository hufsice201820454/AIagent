# -*- coding: utf-8 -*-
"""
EV Agent Pipeline - Main Entry Point (Auto OEM Discovery)

Automatically loads OEM companies from config/allowed_companies.json

Usage:
    python app.py                          # All OEMs from whitelist
    python app.py --regions "KR,CN,JP"     # Custom regions
    python app.py --oems "Tesla,BMW"       # Specific OEMs only
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add agents directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
sys.path.insert(0, AGENTS_DIR)

from agents.SupervisorAgent import run_supervisor
from agents.ReportWriterAgent import run_report_writer


def load_oem_companies() -> list[str]:
    """Load OEM companies from config/allowed_companies.json"""
    whitelist_path = os.path.join(CONFIG_DIR, "allowed_companies.json")
    
    if not os.path.isfile(whitelist_path):
        print(f"[WARNING] Whitelist not found: {whitelist_path}")
        return ["Tesla", "BMW", "BYD"]  # Fallback
    
    try:
        with open(whitelist_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        companies = data.get("companies", [])
        oems = [c["name"] for c in companies if c.get("category") == "OEM"]
        
        print(f"[Config] Loaded {len(oems)} OEMs from whitelist:")
        for oem in oems:
            print(f"  - {oem}")
        
        return oems
    
    except Exception as e:
        print(f"[ERROR] Failed to load whitelist: {e}")
        return ["Tesla", "BMW", "BYD"]  # Fallback


def main():
    parser = argparse.ArgumentParser(
        description="EV Market Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                              # All OEMs from whitelist
  python app.py --oems "Tesla,BMW,Ford"      # Specific OEMs only
  python app.py --regions "KR,CN,JP"         # Custom regions
  python app.py --skip-report                # Skip PDF generation
        """
    )
    parser.add_argument(
        "--oems",
        type=str,
        default=None,
        help="Comma-separated OEM companies (default: all from whitelist)"
    )
    parser.add_argument(
        "--regions",
        type=str,
        default="KR,CN,JP,EU,US",
        help="Comma-separated regions for ESG analysis (default: KR,CN,JP,EU,US)"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=os.path.join(BASE_DIR, "outputs"),
        help="Output directory (default: ./outputs)"
    )
    parser.add_argument(
        "--skip-report",
        action="store_true",
        help="Skip PDF report generation"
    )
    
    args = parser.parse_args()
    
    # Load OEMs
    if args.oems:
        # User-specified OEMs
        companies = [c.strip() for c in args.oems.split(",") if c.strip()]
        print(f"[Config] Using user-specified OEMs: {companies}")
    else:
        # Auto-load from whitelist
        companies = load_oem_companies()
    
    regions = [r.strip() for r in args.regions.split(",") if r.strip()]
    
    if not companies:
        print("[ERROR] No companies to analyze!")
        return 1
    
    # Print header
    print("=" * 80)
    print("EV Market Analysis Pipeline")
    print("=" * 80)
    print(f"Target OEMs ({len(companies)}):")
    for i, company in enumerate(companies, 1):
        print(f"  {i}. {company}")
    print(f"\nESG Regions: {', '.join(regions)}")
    print(f"Output: {args.out_dir}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Step 1: Run Supervisor
    print("\n" + "=" * 80)
    print("[STEP 1/2] Running SupervisorAgent (4 agents in parallel)")
    print("=" * 80)
    try:
        supervisor_results = run_supervisor(
            companies=companies,
            regions=regions,
            out_dir=args.out_dir
        )
        
        print("\n[SUPERVISOR] Execution Summary:")
        print(f"  Final Status: {'✓ SUCCESS' if supervisor_results['final_status'] == 1 else '✗ FAILED'}")
        
        print(f"\n  Validation Results:")
        for agent, status in supervisor_results.get('validation_status', {}).items():
            symbol = '✓' if status else '✗'
            print(f"    {symbol} {agent}")
        
        # Tech 상세 결과 (형태에 따라 정규화)
        tech_results = supervisor_results.get('tech_results')
        if tech_results:
            entries = []
            # Case 1: 단일 결과 객체(dict) 형태
            if isinstance(tech_results, dict) and 'company' in tech_results:
                entries = [tech_results]
            # Case 2: 리스트 형태
            elif isinstance(tech_results, list):
                entries = [e for e in tech_results if isinstance(e, dict)]
            # Case 3: 회사명→결과 매핑 형태
            elif isinstance(tech_results, dict):
                for k, v in tech_results.items():
                    if isinstance(v, dict):
                        item = v.copy()
                        item.setdefault('company', k)
                        entries.append(item)

            print(f"\n  Tech Analysis ({len(entries)} companies):")
            for entry in entries:
                company_name = entry.get('company', 'N/A') if isinstance(entry, dict) else str(entry)
                if isinstance(entry, dict) and 'error' in entry:
                    print(f"    ✗ {company_name}: {entry['error']}")
                else:
                    eval_summary = entry.get('evaluation_summary') if isinstance(entry, dict) else None
                    if not isinstance(eval_summary, dict):
                        eval_summary = {}
                    scores = ', '.join([f"{k}={v}" for k, v in eval_summary.items()])
                    print(f"    ✓ {company_name}: {scores if scores else 'OK'}")
        
        if supervisor_results.get('error_log'):
            print(f"\n  Errors:")
            for agent, error in supervisor_results['error_log'].items():
                print(f"    - {agent}: {error}")
        
        # Stop if failed
        if supervisor_results['final_status'] != 1:
            print("\n[ERROR] Agent execution failed. Stopping pipeline.")
            print("Check outputs/supervisor_summary.json for details.")
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] SupervisorAgent failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Step 2: Generate Report
    if args.skip_report:
        print("\n" + "=" * 80)
        print("[STEP 2/2] Report generation SKIPPED (--skip-report)")
        print("=" * 80)
        _print_output_summary(args.out_dir)
        return 0
    
    print("\n" + "=" * 80)
    print("[STEP 2/2] Running ReportWriterAgent (PDF generation)")
    print("=" * 80)
    try:
        report_result = run_report_writer(supervisor_results)
        
        if report_result.get('error'):
            print(f"\n[WARNING] Report generation had issues:")
            print(f"  {report_result['error']}")
        
        if report_result.get('pdf_path'):
            print(f"\n[SUCCESS] ✓ PDF Report Generated:")
            print(f"  {report_result['pdf_path']}")
        else:
            print(f"\n[ERROR] ✗ PDF Report generation failed")
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] ReportWriterAgent failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Final summary
    print("\n" + "=" * 80)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    _print_output_summary(args.out_dir)
    
    return 0


def _print_output_summary(out_dir: str):
    """Print generated files summary"""
    print(f"\nOutput directory: {out_dir}")
    print("\nGenerated files:")
    
    files_to_check = [
        ("supervisor_summary.json", "Supervisor execution summary"),
        ("jit_analysis.json", "JIT supply chain analysis"),
        ("jit_evaluation.json", "JIT evaluation scores"),
        ("stock_analysis.json", "Stock market analysis"),
        ("esg_analysis.json", "ESG policy analysis"),
        ("map_oem_suppliers.png", "Global OEM/supplier map"),
    ]
    
    for filename, description in files_to_check:
        path = os.path.join(out_dir, filename)
        exists = "✓" if os.path.isfile(path) else "✗"
        print(f"  {exists} {filename:<30} - {description}")
    
    # Tech summaries (per company)
    import glob
    tech_files = glob.glob(os.path.join(out_dir, "tech_summary_*.json"))
    if tech_files:
        print(f"\n  Tech analysis files ({len(tech_files)}):")
        for path in sorted(tech_files)[:5]:  # Show first 5
            print(f"    ✓ {os.path.basename(path)}")
        if len(tech_files) > 5:
            print(f"    ... and {len(tech_files) - 5} more")
    
    # Stock charts
    stock_charts = glob.glob(os.path.join(out_dir, "stock_*.png"))
    if stock_charts:
        print(f"\n  Stock charts ({len(stock_charts)}):")
        for path in sorted(stock_charts)[:3]:
            print(f"    ✓ {os.path.basename(path)}")
        if len(stock_charts) > 3:
            print(f"    ... and {len(stock_charts) - 3} more")
    
    # PDF report
    pdf_files = glob.glob(os.path.join(out_dir, "report_*.pdf"))
    if pdf_files:
        print(f"\n  PDF Report:")
        print(f"    ✓ {os.path.basename(pdf_files[-1])}")


if __name__ == "__main__":
    sys.exit(main())
