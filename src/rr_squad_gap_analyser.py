"""
SupeRR Selector Season 2 — Rajasthan Royals IPL 2027 Auction Intelligence
Component 4: RR Squad Gap Analysis & Roster Economics

Evaluates Rajasthan Royals' roster requirements for IPL 2027:
- Current retained squad core and roster balance
- 5 critical squad gaps identified from 2022-2026 performance data
- Squad Gap Fit (SGF) scoring engine for all qualifying players
- Player Versatility Factor (VF)
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent))
from config import ROOT_DIR, RESEARCH_DIR, OUTPUTS_DIR

AUCTION_DIR = OUTPUTS_DIR / "auction"
AUCTION_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DIR = ROOT_DIR / "SupeRR_Selector_RR_2027_Final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)
COACHING_DIR = OUTPUTS_DIR / "coaching"
STATS_DIR = OUTPUTS_DIR / "statistics"

def run_squad_gap_analysis():
    print("=" * 70)
    print("RUNNING RR SQUAD GAP ANALYSIS & ROSTER ECONOMICS")
    print("=" * 70)

    # 1. Define Current Squad Core (Retained Foundation & Incumbents)
    current_squad_data = [
        {"player_name": "Sanju Samson", "role": "Wicketkeeper-Batter / Captain", "nationality": "Indian", "status": "Retained Core", "phase_specialty": "Middle Overs (1-3)", "primary_strength": "High-intent spin attacker & franchise anchor"},
        {"player_name": "Yashasvi Jaiswal", "role": "Opening Batter", "nationality": "Indian", "status": "Retained Core", "phase_specialty": "Powerplay (1-6)", "primary_strength": "Dominant pace demolition & powerplay boundary scoring"},
        {"player_name": "Riyan Parag", "role": "Middle-Order Batter / Off-Spin", "nationality": "Indian", "status": "Retained Core", "phase_specialty": "Middle-to-Death (4-5)", "primary_strength": "Boundary acceleration & bowling utility"},
        {"player_name": "Dhruv Jurel", "role": "Wicketkeeper-Finisher", "nationality": "Indian", "status": "Retained Core", "phase_specialty": "Death Overs (5-7)", "primary_strength": "Situational composure & ice-cold death finishing"},
        {"player_name": "Shimron Hetmyer", "role": "Middle-Order Finisher", "nationality": "Overseas", "status": "Retained / Core Target", "phase_specialty": "Death Overs (5-6)", "primary_strength": "Explosive boundary conversion vs pace and spin at death"},
        {"player_name": "Sandeep Sharma", "role": "Seam Bowler", "nationality": "Indian", "status": "Retained Core", "phase_specialty": "Death & Powerplay", "primary_strength": "Knuckle balls, wide yorkers & defensive discipline under pressure"}
    ]
    df_current_squad = pd.DataFrame(current_squad_data)

    # 2. Define Squad Composition Targets (IPL 25-player roster archetype)
    squad_comp_data = [
        {"department": "Top-Order Batting", "current_count": 2, "target_count": 4, "gap_level": "HIGH", "priority": "Priority 1: Explosive Opening Partner for Jaiswal"},
        {"department": "Middle-Order & Finishers", "current_count": 3, "target_count": 6, "gap_level": "MEDIUM", "priority": "Priority 2: High-composure spin counter & finishing depth"},
        {"department": "All-Rounders (Pace/Spin)", "current_count": 1, "target_count": 4, "gap_level": "HIGH", "priority": "Priority 5: Multi-dimensional all-round balance"},
        {"department": "Pace Battery (Powerplay/Death)", "current_count": 1, "target_count": 6, "gap_level": "CRITICAL", "priority": "Priority 3: Elite high-pace enforcer & death specialist"},
        {"department": "Spin Department", "current_count": 0, "target_count": 5, "gap_level": "CRITICAL", "priority": "Priority 4: Leg-spin / mystery-spin wicket-taker post-Chahal"}
    ]
    df_squad_comp = pd.DataFrame(squad_comp_data)

    # 3. Define 5 Formal Squad Gaps & Role Requirements
    gaps_data = [
        {
            "gap_id": "GAP-01",
            "gap_name": "Explosive Pace-Hitting Opening Partner",
            "tactical_need": "Partner Yashasvi Jaiswal with an aggressive top-order batter who dominates pace inside overs 1-6 (PP SR > 145) and avoids powerplay dot balls.",
            "coaching_mandate": "Aligns with Kumar Sangakkara's demand for immediate boundary pressure and Rahul Dravid's need for high scoring floors.",
            "target_metrics": "PP SR >= 145, Boundary% >= 20%, Dot% <= 35%"
        },
        {
            "gap_id": "GAP-02",
            "gap_name": "Middle-Order Spin Counter & Chase Finisher",
            "tactical_need": "Shield the middle order against wrist-spin chokes in overs 7-15, and deliver cold execution in steep run chases (RRR >= 10.0).",
            "coaching_mandate": "Directly embodies Rahul Dravid's Composure Index (DCI) and Vikram Rathour's technical discipline against hard lengths.",
            "target_metrics": "Pressure SR >= 145, CV Runs <= 0.70, Average >= 32.0"
        },
        {
            "gap_id": "GAP-03",
            "gap_name": "High-Pace Enforcer & Death-Overs Seamer",
            "tactical_need": "Partner Sandeep Sharma at the death and replace the departing pace hostility with high velocity (>140 kph), nailing wide yorkers.",
            "coaching_mandate": "Core requirement of Shane Bond's discipline doctrine: death overs economy strictly under 9.20 rpo with >40% dot balls.",
            "target_metrics": "Death Econ <= 9.20, Dot% >= 42%, Pressure Econ <= 8.50"
        },
        {
            "gap_id": "GAP-04",
            "gap_name": "Wicket-Taking Mystery / Attacking Wrist Spinner",
            "tactical_need": "Replace the high-volume wicket threat of Yuzvendra Chahal through overs 7-15, attacking both right and left-hand batters.",
            "coaching_mandate": "Sangakkara's matchup weapon: attacking middle-overs spin that forces false shots and maintains wicket pressure.",
            "target_metrics": "Middle Econ <= 7.80, Wkts/Match >= 1.25, High Threat Wkts >= 5"
        },
        {
            "gap_id": "GAP-05",
            "gap_name": "Dual-Skill Lower-Order All-Rounder",
            "tactical_need": "Provide batting firepower at positions 7-8 (>150 SR) while delivering 2-3 reliable defensive overs.",
            "coaching_mandate": "Ensures tactical flexibility (TFI) across phases and insulates against batting collapses.",
            "target_metrics": "Versatility Factor >= 70.0%, Dual Contribution Index >= 65.0%"
        }
    ]
    df_gaps = pd.DataFrame(gaps_data)

    # 4. Compute Squad Gap Fit (SGF) & Versatility Factor (VF) for All Players
    df_bat = pd.read_csv(STATS_DIR / "batting_reliability_model.csv")
    df_bowl = pd.read_csv(STATS_DIR / "bowling_reliability_model.csv")
    df_cpas = pd.read_csv(COACHING_DIR / "rr_coach_persona_scores.csv")

    sgf_records = []

    # Batters SGF:
    for _, row in df_bat.iterrows():
        pid = row['player_id']
        pname = row['player_name']
        pp_sr = row.get('pp_sr', 0) if pd.notna(row.get('pp_sr')) else 0
        death_sr = row.get('death_sr', 0) if pd.notna(row.get('death_sr')) else 0
        b_pct = row.get('boundary_pct', 0)
        p_sr = row.get('pressure_sr', 0)
        dot_pct = row.get('dot_pct', 0)

        # Gap 1 Fit (Opener): High PP SR, high boundary%, low dot%
        fit_gap1 = float(np.clip((min(pp_sr, 180)/180 * 0.45 + min(b_pct, 28)/28 * 0.35 + max(0, 50 - dot_pct)/50 * 0.20) * 100, 0, 100))

        # Gap 2 Fit (Finisher/Middle): High Death SR, high Pressure SR, low CV
        cv = row.get('cv_runs', 1.0)
        fit_gap2 = float(np.clip((min(death_sr, 200)/200 * 0.40 + min(p_sr, 180)/180 * 0.35 + max(0, 1.2 - cv)/1.2 * 0.25) * 100, 0, 100))

        # Best Fit
        best_gap = "GAP-01 (Explosive Opener)" if fit_gap1 >= fit_gap2 else "GAP-02 (Middle/Finisher)"
        sgf_score = round(max(fit_gap1, fit_gap2), 2)

        # Versatility Factor (VF):
        # Operates across Powerplay AND Death, plus overall volume
        pp_vol = min(row.get('pp_balls', 0), 30) / 30.0
        death_vol = min(row.get('death_balls', 0), 30) / 30.0
        vf_score = float(np.clip(round((0.40 * pp_vol + 0.40 * death_vol + 0.20 * min(row.get('total_runs', 0), 500)/500) * 100, 2), 0, 100))

        sgf_records.append({
            'player_id': pid,
            'player_name': pname,
            'role': 'Batter',
            'primary_gap_targeted': best_gap,
            'gap_1_fit': round(fit_gap1, 2),
            'gap_2_fit': round(fit_gap2, 2),
            'gap_3_fit': 0.0,
            'gap_4_fit': 0.0,
            'gap_5_fit': round((fit_gap1 + fit_gap2)/2, 2),
            'sgf_score': sgf_score,
            'versatility_factor': vf_score
        })

    # Bowlers SGF:
    for _, row in df_bowl.iterrows():
        pid = row['player_id']
        pname = row['player_name']
        pp_econ = row.get('pp_econ', 8.5) if pd.notna(row.get('pp_econ')) and row.get('pp_econ') > 0 else 8.5
        death_econ = row.get('death_econ', 10.5) if pd.notna(row.get('death_econ')) and row.get('death_econ') > 0 else 10.5
        dot_pct = row.get('dot_pct', 35)
        p_econ = row.get('pressure_econ', 9.0) if pd.notna(row.get('pressure_econ')) and row.get('pressure_econ') > 0 else 9.0
        is_spin = (row.get('pace_or_spin') == 'spin')

        # Gap 3 Fit (Death Seam & Pace): Low death econ, high dot%, low pressure econ
        fit_gap3 = (max(0, 13.0 - death_econ)/5.0 * 0.45 + min(dot_pct, 55)/55 * 0.35 + max(0, 12.0 - p_econ)/4.0 * 0.20) * 100
        if is_spin:
            fit_gap3 *= 0.6  # Seam preferred for pure death pace role
        fit_gap3 = float(np.clip(fit_gap3, 0, 100))

        # Gap 4 Fit (Attacking Spin): Low econ, high wickets, spin specialty
        wkts_norm = min(row.get('total_wickets', 0), 30)/30.0
        mid_econ = row.get('economy', 8.0)
        fit_gap4 = (max(0, 10.0 - mid_econ)/3.0 * 0.40 + wkts_norm * 0.40 + min(dot_pct, 50)/50 * 0.20) * 100
        if not is_spin:
            fit_gap4 *= 0.5  # Spin preferred for gap 4
        fit_gap4 = float(np.clip(fit_gap4, 0, 100))

        best_gap = "GAP-03 (High-Pace / Death Seam)" if fit_gap3 >= fit_gap4 else "GAP-04 (Attacking Spin Choke)"
        sgf_score = round(max(fit_gap3, fit_gap4), 2)

        # Versatility Factor (VF):
        pp_vol = min(row.get('pp_balls', 0), 36) / 36.0
        death_vol = min(row.get('death_balls', 0), 36) / 36.0
        vf_score = float(np.clip(round((0.40 * pp_vol + 0.40 * death_vol + 0.20 * min(row.get('total_wickets', 0), 20)/20) * 100, 2), 0, 100))

        sgf_records.append({
            'player_id': pid,
            'player_name': pname,
            'role': 'Bowler',
            'primary_gap_targeted': best_gap,
            'gap_1_fit': 0.0,
            'gap_2_fit': 0.0,
            'gap_3_fit': round(fit_gap3, 2),
            'gap_4_fit': round(fit_gap4, 2),
            'gap_5_fit': round((fit_gap3 + fit_gap4)/2, 2),
            'sgf_score': sgf_score,
            'versatility_factor': vf_score
        })

    df_sgf = pd.DataFrame(sgf_records)

    # Save all squad gap datasets
    df_current_squad.to_csv(AUCTION_DIR / "rr_current_squad.csv", index=False)
    df_current_squad.to_csv(FINAL_DIR / "rr_current_squad.csv", index=False)

    df_squad_comp.to_csv(AUCTION_DIR / "rr_squad_composition.csv", index=False)
    df_squad_comp.to_csv(FINAL_DIR / "rr_squad_composition.csv", index=False)

    df_gaps.to_csv(AUCTION_DIR / "rr_squad_gaps.csv", index=False)
    df_gaps.to_csv(FINAL_DIR / "rr_squad_gaps.csv", index=False)

    df_gaps.to_csv(AUCTION_DIR / "rr_role_requirements.csv", index=False)
    df_gaps.to_csv(FINAL_DIR / "rr_role_requirements.csv", index=False)

    df_sgf.to_csv(AUCTION_DIR / "rr_squad_gap_scores.csv", index=False)
    df_sgf.to_csv(FINAL_DIR / "rr_squad_gap_scores.csv", index=False)

    print(f"Generated: rr_current_squad.csv ({len(df_current_squad)} players)")
    print(f"Generated: rr_squad_composition.csv ({len(df_squad_comp)} departments)")
    print(f"Generated: rr_squad_gaps.csv ({len(df_gaps)} strategic gaps)")
    print(f"Generated: rr_squad_gap_scores.csv ({len(df_sgf)} players scored)")
    print("Squad Gap Analysis completed successfully.\n")

if __name__ == '__main__':
    run_squad_gap_analysis()
