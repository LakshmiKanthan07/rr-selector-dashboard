"""
Rajasthan Royals — SupeRR Selector Season 2: Master Pipeline Runner
Executes all analytical phases end-to-end:
Phase 1: Data Audit
Phase 2-5: Match Reconstruction, Pressure, Batting & Bowling
Phase 6-7: Wicket Quality & Reliability Scoring
Phase 8: Player Profiling & Evidence Generation
Reports: Publication PDF Generation
Tests: Automated Verification Suite
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent
SRC_DIR = ROOT_DIR / "src"

def run_step(step_name, script_path):
    print(f"\n{'='*70}")
    print(f"RUNNING: {step_name}")
    print(f"Script: {script_path.name}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    cmd = [sys.executable, str(script_path)]
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if result.returncode != 0:
        print(f"\n[ERROR] Step '{step_name}' failed with return code {result.returncode}.")
        sys.exit(result.returncode)
    print(f"[SUCCESS] Step '{step_name}' completed successfully.")

def main():
    start_time = datetime.now()
    print("*" * 70)
    print("RAJASTHAN ROYALS — SUPERR SELECTOR SEASON 2 PIPELINE")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("*" * 70)
    
    # Step 1: Data Audit
    run_step("Phase 1: Data Audit & Quality Report", SRC_DIR / "phase1_data_audit.py")
    
    # Step 2: Batting Reconciliation
    run_step("Phase 4: Batting Reconstruction & Dismissals", SRC_DIR / "run_batting_update.py")
    
    # Step 3: Reliability Models & Wicket Quality
    run_step("Phase 6-7: Wicket Quality & Reliability Modelling", SRC_DIR / "phase6_7_reliability.py")
    
    # Step 4: Player Profiles & Supporting Charts
    run_step("Phase 8: Player Profiles & Charts", SRC_DIR / "phase8_player_profiles.py")
    
    # Step 5: PDF Reports
    run_step("Phase 12: Publication PDF Generation", SRC_DIR / "generate_reports.py")
    
    # Step 6: Automated Testing
    run_step("Phase 13: Automated Testing Suite", ROOT_DIR / "tests" / "test_pipeline.py")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print("\n" + "*" * 70)
    print(f"ALL PIPELINE PHASES COMPLETED IN: {duration}")
    print(f"Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("*" * 70)

if __name__ == "__main__":
    main()

