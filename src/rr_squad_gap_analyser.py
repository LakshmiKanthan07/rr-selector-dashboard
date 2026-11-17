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

    # 1. RR squad for IPL 2027 from the 17 Nov 2026 retention lists (src/ipl2027_lists.py).
    # Source: IPL 2027 lists as published by press on deadline day (owner-supplied, cross-checked with Cricket News/Yahoo
    # 17 Nov 2026). An official iplt20.com page could not be reached, so "retention_outlook" says "per 17 Nov lists".
    # Roles are general cricket knowledge, not from the data pack.
    from ipl2027_lists import TEAMS, TRADES, AS_OF
    rr = TEAMS["RR"]
    role = {
        "Riyan Parag": ("Middle-Order Batter / Off-Spin (Captain)", "Indian", "Middle"),
        "Yashasvi Jaiswal": ("Opening Batter", "Indian", "Top"),
        "Vaibhav Sooryavanshi": ("Opening Batter", "Indian", "Top"),
        "Lhuan-dre Pretorius": ("Wicketkeeper-Batter", "Overseas", "Top"),
        "Dhruv Jurel": ("Wicketkeeper-Batter", "Indian", "Middle"),
        "Donovan Ferreira": ("Batter / Wicketkeeper", "Overseas", "Middle"),
        "Shubham Dubey": ("Finisher", "Indian", "Middle"),
        "Aman Rao Parela": ("Batter", "Indian", "Middle"),
        "Ravindra Jadeja": ("All-Rounder (Spin)", "Indian", "AR"),
        "Dasun Shanaka": ("All-Rounder (Pace)", "Overseas", "AR"),
        "Jofra Archer": ("Fast Bowler", "Overseas", "Pace"),
        "Nandre Burger": ("Fast Bowler", "Overseas", "Pace"),
        "Sandeep Sharma": ("Seam Bowler", "Indian", "Pace"),
        "Sushant Mishra": ("Seam Bowler", "Indian", "Pace"),
        "Yash Raj Punja": ("Seam Bowler", "Indian", "Pace"),
        "Mohammed Shami": ("Fast Bowler", "Indian", "Pace"),
        "Ravi Bishnoi": ("Leg-Spinner", "Indian", "Spin"),
        "Brijesh Sharma": ("Spinner", "Indian", "Spin"),
        "M Siddharth": ("Left-Arm Spinner", "Indian", "Spin"),
    }
    trade_from = {t[0]: t[1] for t in TRADES if t[2] == "RR"}
    sq = []
    for n in rr["retained"] + rr["traded_in"]:
        r, nat, d = role[n]
        if n in trade_from:
            out = f"Traded in from {trade_from[n]} (completed trade; {AS_OF} lists)"
        elif n == "Ravindra Jadeja":
            out = f"Retained per {AS_OF} lists (Cricket News/Yahoo describes him as traded in from CSK; either way on RR)"
        else:
            out = f"Retained per {AS_OF} lists"
        sq.append((n, r, nat, d, out))
    assert len(sq) == len(role), "role map and RR list out of step"
    current_squad_data = [{"player_name": n, "role": r, "nationality": nat, "department": d,
                           "status": "On RR squad (IPL 2027, " + AS_OF + ")", "retention_outlook": o,
                           "phase_specialty": "", "primary_strength": ""} for n, r, nat, d, o in sq]
    df_current_squad = pd.DataFrame(current_squad_data)
    n_over = int((df_current_squad.nationality == "Overseas").sum())
    assert n_over == 8 - rr["overseas_free"], "overseas count disagrees with the lists' free-slot figure"

    # released list + trade-outs (RR facts)
    released_rows = [{"player_name": n, "team": "RR", "action": "Released", "source": f"IPL 2027 lists {AS_OF}"} for n in rr["released"]]
    released_rows += [{"player_name": t[0], "team": "RR", "action": f"Traded out to {t[2]}", "source": f"completed trade, {AS_OF} lists"} for t in TRADES if t[1] == "RR"]
    df_released = pd.DataFrame(released_rows)
    df_rr_ctx = pd.DataFrame([dict(as_of=AS_OF, purse_remaining_cr=rr["purse"], open_squad_slots=rr["open_slots"],
                                   squad_size=len(df_current_squad), overseas_in_squad=n_over,
                                   overseas_cap=8, overseas_slots_free=rr["overseas_free"],
                                   source=f"IPL 2027 lists {AS_OF} (press-compiled) + Cricket News/Yahoo purse/slot table")])

    # 2. Squad composition vs the 25-player roster archetype. Gap level is a rule on the numbers:
    #    shortfall >= 2 -> HIGH, shortfall 1 -> MEDIUM, no shortfall -> LOW (quality upgrade only).
    cnt = df_current_squad.department.value_counts().to_dict()
    def lvl(dept, target):
        short = target - cnt.get(dept, 0)
        return "HIGH" if short >= 2 else "MEDIUM" if short == 1 else "LOW"
    squad_comp_data = [
        {"department": "Top-Order Batting", "current_count": cnt.get("Top", 0), "target_count": 4, "gap_level": lvl("Top", 4), "priority": "Jaiswal, Sooryavanshi and Pretorius only: one more explosive opening / keeper-batter option would complete the top order (Samson is now at CSK)"},
        {"department": "Middle-Order & Finishers", "current_count": cnt.get("Middle", 0), "target_count": 6, "gap_level": lvl("Middle", 6), "priority": "Hetmyer (Rs 11 cr) was released, so one finisher slot is open; quality upgrade over Dubey / Aman Rao"},
        {"department": "All-Rounders (Pace/Spin)", "current_count": cnt.get("AR", 0), "target_count": 4, "gap_level": lvl("AR", 4), "priority": "Only Jadeja and Shanaka remain (Yudhvir Singh released): needs a dual-skill lower-order all-rounder"},
        {"department": "Pace Battery (Powerplay/Death)", "current_count": cnt.get("Pace", 0), "target_count": 6, "gap_level": lvl("Pace", 6), "priority": "Numbers at target with Archer, Burger, Shami, Sandeep; Maphaka, Milne, Deshpande, Sen released, so an elite death specialist is still the need"},
        {"department": "Spin Department", "current_count": cnt.get("Spin", 0), "target_count": 5, "gap_level": lvl("Spin", 5), "priority": "Bishnoi, Brijesh Sharma and M Siddharth (traded in) with Jadeja: a second attacking wrist-spinner is still missing"}
    ]
    df_squad_comp = pd.DataFrame(squad_comp_data)
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    df_squad_comp = df_squad_comp.sort_values("gap_level", key=lambda c: c.map(order), kind="stable").reset_index(drop=True)
    df_squad_comp["priority"] = ["Priority " + str(i + 1) + ": " + p for i, p in enumerate(df_squad_comp["priority"])]

    # 3. Define 5 Formal Squad Gaps & Role Requirements
    gaps_data = [
        {
            "gap_id": "GAP-01",
            "gap_name": "Explosive Pace-Hitting Opening Partner",
            "tactical_need": "Partner Yashasvi Jaiswal and Vaibhav Sooryavanshi with a pace-dominant top-order batter, ideally a keeper (Sanju Samson now plays for CSK), who dominates pace inside overs 1-6 (PP SR > 145) and avoids powerplay dot balls.",
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
            "tactical_need": "Support Sandeep Sharma, Mohammed Shami and Jofra Archer at the death after the releases of Maphaka, Milne, Deshpande and Sen, adding high velocity (>140 kph) and wide yorkers.",
            "coaching_mandate": "Core requirement of Shane Bond's discipline doctrine: death overs economy strictly under 9.20 rpo with >40% dot balls.",
            "target_metrics": "Death Econ <= 9.20, Dot% >= 42%, Pressure Econ <= 8.50"
        },
        {
            "gap_id": "GAP-04",
            "gap_name": "Wicket-Taking Mystery / Attacking Wrist Spinner",
            "tactical_need": "Add a second attacking spinner beside Ravi Bishnoi, M Siddharth (traded in) and Ravindra Jadeja for overs 7-15 (Chahal left RR before 2025), attacking both right and left-hand batters.",
            "coaching_mandate": "Sangakkara's matchup weapon: attacking middle-overs spin that forces false shots and maintains wicket pressure.",
            "target_metrics": "Middle Econ <= 7.80, Wkts/Match >= 1.25, High Threat Wkts >= 5"
        },
        {
            "gap_id": "GAP-05",
            "gap_name": "Dual-Skill Lower-Order All-Rounder",
            "tactical_need": "Provide batting firepower at positions 7-8 (>150 SR) while delivering 2-3 reliable defensive overs; RR retain only Jadeja and Shanaka as all-rounders.",
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

    for _nm, _df in (("rr_released_players.csv", df_released), ("rr_context_17nov.csv", df_rr_ctx)):
        _df.to_csv(AUCTION_DIR / _nm, index=False)
        _df.to_csv(FINAL_DIR / _nm, index=False)

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
