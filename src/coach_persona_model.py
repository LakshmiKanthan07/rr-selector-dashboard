"""
SupeRR Selector Season 2 — Rajasthan Royals IPL 2027 Auction Intelligence
Component 3: Coach Persona Alignment Model (CPAS)

Translates documented coaching philosophies into standardized empirical metrics:
- Rahul Dravid Composure Index (DCI)
- Kumar Sangakkara Matchup & Intent Index (SMI)
- Shane Bond Discipline Index (BDI)
- Vikram Rathour Technical Discipline Index (RDI)
- Tactical Flexibility Index (TFI)
- Final Coach Persona Alignment Score (CPAS)
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent))
from config import ROOT_DIR, RESEARCH_DIR, OUTPUTS_DIR

COACHING_DIR = OUTPUTS_DIR / "coaching"
COACHING_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DIR = ROOT_DIR / "SupeRR_Selector_RR_2027_Final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)
STATS_DIR = OUTPUTS_DIR / "statistics"

def min_max_norm(series, invert=False):
    """Normalize a series to [0, 1]. If invert=True, lower values get higher scores."""
    s = pd.to_numeric(series, errors='coerce').fillna(0)
    s_min = s.min()
    s_max = s.max()
    if s_max == s_min:
        return pd.Series(0.5, index=s.index)
    norm = (s - s_min) / (s_max - s_min)
    return 1.0 - norm if invert else norm

def run_coach_persona_model():
    print("=" * 70)
    print("RUNNING COACH PERSONA ALIGNMENT MODEL (CPAS)")
    print("=" * 70)

    # 1. Load Batting Reliability Data
    bat_path = STATS_DIR / "batting_reliability_model.csv"
    bowl_path = STATS_DIR / "bowling_reliability_model.csv"
    if not bat_path.exists() or not bowl_path.exists():
        raise FileNotFoundError("Missing reliability model files in outputs/statistics/")

    df_bat = pd.read_csv(bat_path)
    df_bowl = pd.read_csv(bowl_path)

    print(f"Loaded {len(df_bat)} qualifying batters and {len(df_bowl)} qualifying bowlers.")

    # ============================================================
    # 2. BATTING CPAS MODELLING
    # ============================================================
    # DCI (Dravid Composure Index):
    # - Low run volatility (cv_runs)
    # - High pressure performance (pressure_perf_score)
    # - Low dot ball % (dot_pct)
    dci_bat = (
        0.35 * min_max_norm(df_bat['cv_runs'], invert=True) +
        0.35 * min_max_norm(df_bat['pressure_perf_score']) +
        0.30 * min_max_norm(df_bat['dot_pct'], invert=True)
    )

    # SMI (Sangakkara Matchup & Intent Index):
    # - Boundary percentage
    # - High overall strike rate
    # - Death acceleration
    smi_bat = (
        0.35 * min_max_norm(df_bat['boundary_pct']) +
        0.35 * min_max_norm(df_bat['strike_rate']) +
        0.30 * min_max_norm(df_bat['death_sr'])
    )

    # RDI (Rathour Technical Discipline Index):
    # - Consistency score
    # - Scoring floor (avoiding sub-10s)
    # - Batting average
    rdi_bat = (
        0.35 * min_max_norm(df_bat['consistency_score']) +
        0.35 * min_max_norm(df_bat['sub10_inv']) +
        0.30 * min_max_norm(df_bat['average'])
    )

    # TFI (Tactical Flexibility Index):
    # Ability to operate across both Powerplay and Death
    pp_flex = np.minimum(df_bat['pp_balls'].fillna(0), 30) / 30.0
    death_flex = np.minimum(df_bat['death_balls'].fillna(0), 30) / 30.0
    tfi_bat = 0.5 * pp_flex + 0.5 * death_flex

    # Composite CPAS Batting:
    cpas_bat = (0.35 * dci_bat + 0.35 * smi_bat + 0.20 * rdi_bat + 0.10 * tfi_bat) * 100.0

    df_bat['dci_score'] = (dci_bat * 100).round(2)
    df_bat['smi_score'] = (smi_bat * 100).round(2)
    df_bat['rdi_score'] = (rdi_bat * 100).round(2)
    df_bat['tfi_score'] = (tfi_bat * 100).round(2)
    df_bat['cpas_score'] = cpas_bat.round(2)
    df_bat['cpas_rank'] = df_bat['cpas_score'].rank(ascending=False, method='min').astype(int)

    # ============================================================
    # 3. BOWLING CPAS MODELLING
    # ============================================================
    # BDI (Shane Bond Discipline Index):
    # - High dot ball % (dot_pct)
    # - Contextual wicket quality (wicket_quality_score)
    # - Death overs economy control (death_econ)
    death_econ_clean = df_bowl['death_econ'].replace(0, np.nan).fillna(df_bowl['economy'])
    bdi_bowl = (
        0.35 * min_max_norm(df_bowl['dot_pct']) +
        0.35 * min_max_norm(df_bowl['wicket_quality_score']) +
        0.30 * min_max_norm(death_econ_clean, invert=True)
    )

    # DCI (Dravid Composure Index for Bowling):
    # - Low economy volatility (cv_economy)
    # - Pressure economy control (pressure_econ)
    # - High pressure wickets (p_wkt_norm)
    p_econ_clean = df_bowl['pressure_econ'].replace(0, np.nan).fillna(df_bowl['economy'])
    dci_bowl = (
        0.40 * min_max_norm(df_bowl['cv_economy'], invert=True) +
        0.35 * min_max_norm(p_econ_clean, invert=True) +
        0.25 * min_max_norm(df_bowl['p_wkt_norm'])
    )

    # SMI (Sangakkara Intent & Strike Index for Bowling):
    # - Wickets per match / strike capacity
    # - Powerplay hostility
    # - Pressure dot balls
    pp_balls_clean = np.maximum(1, df_bowl['pp_balls'])
    pp_wkt_rate = df_bowl['pp_wickets'] / pp_balls_clean
    smi_bowl = (
        0.40 * min_max_norm(df_bowl['wkts_norm']) +
        0.30 * min_max_norm(pp_wkt_rate) +
        0.30 * min_max_norm(df_bowl['dot_ball_score'])
    )

    # TFI (Tactical Flexibility Index for Bowling):
    # Multi-phase execution (Powerplay + Death overs)
    pp_flex_b = np.minimum(df_bowl['pp_balls'].fillna(0), 30) / 30.0
    death_flex_b = np.minimum(df_bowl['death_balls'].fillna(0), 30) / 30.0
    tfi_bowl = 0.5 * pp_flex_b + 0.5 * death_flex_b

    # Composite CPAS Bowling:
    cpas_bowl = (0.40 * bdi_bowl + 0.35 * dci_bowl + 0.15 * smi_bowl + 0.10 * tfi_bowl) * 100.0

    df_bowl['bdi_score'] = (bdi_bowl * 100).round(2)
    df_bowl['dci_score'] = (dci_bowl * 100).round(2)
    df_bowl['smi_score'] = (smi_bowl * 100).round(2)
    df_bowl['tfi_score'] = (tfi_bowl * 100).round(2)
    df_bowl['cpas_score'] = cpas_bowl.round(2)
    df_bowl['cpas_rank'] = df_bowl['cpas_score'].rank(ascending=False, method='min').astype(int)

    # ============================================================
    # 4. SAVE CPAS SCORES & DIMENSIONS
    # ============================================================
    bat_cpas_cols = [
        'player_id', 'player_name', 'dataset', 'innings', 'total_runs',
        'batting_reliability_pct', 'batting_rank',
        'dci_score', 'smi_score', 'rdi_score', 'tfi_score', 'cpas_score', 'cpas_rank'
    ]
    bowl_cpas_cols = [
        'player_id', 'player_name', 'dataset', 'matches', 'total_wickets', 'economy',
        'bowling_reliability_pct', 'bowling_rank',
        'bdi_score', 'dci_score', 'smi_score', 'tfi_score', 'cpas_score', 'cpas_rank'
    ]

    out_bat = df_bat[bat_cpas_cols].sort_values(by='cpas_score', ascending=False)
    out_bowl = df_bowl[bowl_cpas_cols].sort_values(by='cpas_score', ascending=False)

    # Combined CPAS table
    out_bat['primary_role'] = 'Batter'
    out_bowl['primary_role'] = 'Bowler'
    combined_cpas = pd.concat([
        out_bat.rename(columns={'batting_reliability_pct': 'reliability_pct', 'batting_rank': 'official_pri_rank'}),
        out_bowl.rename(columns={'bowling_reliability_pct': 'reliability_pct', 'bowling_rank': 'official_pri_rank'})
    ], ignore_index=True)

    # Save to outputs/coaching and SupeRR_Selector_RR_2027_Final
    combined_cpas.to_csv(COACHING_DIR / "rr_coach_persona_scores.csv", index=False)
    combined_cpas.to_csv(FINAL_DIR / "rr_coach_persona_scores.csv", index=False)

    # Dimensional Breakdown Table
    dim_df = combined_cpas[[
        'player_id', 'player_name', 'primary_role', 'dci_score', 'smi_score',
        'bdi_score', 'rdi_score', 'tfi_score', 'cpas_score', 'cpas_rank'
    ]].copy()
    dim_df.to_csv(COACHING_DIR / "rr_coach_dimension_scores.csv", index=False)
    dim_df.to_csv(FINAL_DIR / "rr_coach_dimension_scores.csv", index=False)

    # ============================================================
    # 5. WEIGHT SENSITIVITY STRESS TEST
    # ============================================================
    # Test 4 distinct coaching philosophies:
    # 1. Balanced (35/35/20/10)
    # 2. Dravid-Dominant (60% DCI, 20% SMI, 15% RDI, 5% TFI)
    # 3. Sangakkara-Dominant (20% DCI, 60% SMI, 15% RDI, 5% TFI)
    # 4. Ultra-Aggressive Intent (15% DCI, 70% SMI, 10% RDI, 5% TFI)
    sens_rows = []
    top_batters_sample = out_bat.head(15)['player_name'].tolist()
    
    for p_name in top_batters_sample:
        row = out_bat[out_bat['player_name'] == p_name].iloc[0]
        d = row['dci_score'] / 100.0
        s = row['smi_score'] / 100.0
        r = row['rdi_score'] / 100.0
        t = row['tfi_score'] / 100.0

        cpas_balanced = row['cpas_score']
        cpas_dravid = round((0.60 * d + 0.20 * s + 0.15 * r + 0.05 * t) * 100, 2)
        cpas_sanga = round((0.20 * d + 0.60 * s + 0.15 * r + 0.05 * t) * 100, 2)
        cpas_ultra = round((0.15 * d + 0.70 * s + 0.10 * r + 0.05 * t) * 100, 2)

        sens_rows.append({
            'player_name': p_name,
            'role': 'Batter',
            'cpas_balanced': cpas_balanced,
            'cpas_dravid_led': cpas_dravid,
            'cpas_sangakkara_led': cpas_sanga,
            'cpas_ultra_intent': cpas_ultra,
            'max_delta': round(max(cpas_dravid, cpas_sanga, cpas_ultra) - min(cpas_dravid, cpas_sanga, cpas_ultra), 2)
        })

    df_sens = pd.DataFrame(sens_rows)
    df_sens.to_csv(COACHING_DIR / "rr_coach_weight_sensitivity.csv", index=False)
    df_sens.to_csv(FINAL_DIR / "rr_coach_weight_sensitivity.csv", index=False)

    print(f"Generated: rr_coach_persona_scores.csv ({len(combined_cpas)} players)")
    print(f"Generated: rr_coach_dimension_scores.csv ({len(dim_df)} players)")
    print(f"Generated: rr_coach_weight_sensitivity.csv ({len(df_sens)} stress test profiles)")
    print("Coach Persona Alignment Model completed successfully.\n")

if __name__ == '__main__':
    run_coach_persona_model()

