"""
SupeRR Selector Season 2 — Batting & Bowling Analysis with Exact Dismissal Resolution
Loads bbb_pressure.csv, computes accurate batting innings with dismissals,
bowling innings, and player aggregates.
"""

import pandas as pd
import numpy as np
import warnings
import sys
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import *

print("=" * 70)
print("BATTING & BOWLING ANALYSIS (EXACT DISMISSAL RESOLUTION)")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Load bbb_pressure.csv
print("\n[LOAD] Loading bbb_pressure.csv...")
bbb_valid = pd.read_csv(INTERIM_DIR / 'bbb_pressure.csv', low_memory=False)
print(f"  Loaded {len(bbb_valid):,} deliveries.")

# Boolean conversion for safety
bbb_valid['is_wicket_bool'] = bbb_valid['is_wicket_bool'].astype(str).str.lower().isin(['true', '1'])
bbb_valid['is_four_bool'] = bbb_valid['is_four_bool'].astype(str).str.lower().isin(['true', '1'])
bbb_valid['is_six_bool'] = bbb_valid['is_six_bool'].astype(str).str.lower().isin(['true', '1'])
bbb_valid['is_batter_ball'] = bbb_valid['is_batter_ball'].astype(str).str.lower().isin(['true', '1'])
bbb_valid['is_legal_ball'] = bbb_valid['is_legal_ball'].astype(str).str.lower().isin(['true', '1'])
bbb_valid['is_high_pressure_batting'] = bbb_valid['is_high_pressure_batting'].astype(str).str.lower().isin(['true', '1'])
bbb_valid['is_high_pressure_bowling'] = bbb_valid['is_high_pressure_bowling'].astype(str).str.lower().isin(['true', '1'])

# Precompute exact dismissals
valid_d = bbb_valid[bbb_valid['is_wicket_bool'] & bbb_valid['dismissed_player_id'].notna()]
dismissed_tuples = set(zip(
    valid_d['match_id'],
    valid_d['innings'],
    valid_d['dismissed_player_id'].astype(float).astype(int)
))
print(f"  Precomputed {len(dismissed_tuples):,} unique match-innings dismissals.")

# ============================================================
# PHASE 4: BATTING ANALYSIS
# ============================================================
print("\n[PHASE 4] Batting Analysis...")

batting_df = bbb_valid[bbb_valid['is_batter_ball']].copy()

print("  Reconstructing innings-level batting performances...")

batting_innings = []
for (match_id, innings, striker_id), group in batting_df.groupby(['match_id', 'innings', 'striker_id']):
    if len(group) == 0:
        continue
    striker_name = group['striker_name'].iloc[0]
    balls = len(group)
    runs = group['batter_runs'].sum()
    fours = group['is_four_bool'].sum()
    sixes = group['is_six_bool'].sum()
    dots = (group['batter_runs'] == 0).sum()
    singles = (group['batter_runs'] == 1).sum()
    twos = (group['batter_runs'] == 2).sum()
    threes = (group['batter_runs'] == 3).sum()
    dismissed = (match_id, innings, int(striker_id)) in dismissed_tuples

    # Phase breakdown
    pp_balls = len(group[group['phase'] == 'Powerplay'])
    pp_runs = group[group['phase'] == 'Powerplay']['batter_runs'].sum()
    mid_balls = len(group[group['phase'] == 'Middle'])
    mid_runs = group[group['phase'] == 'Middle']['batter_runs'].sum()
    death_balls = len(group[group['phase'] == 'Death'])
    death_runs = group[group['phase'] == 'Death']['batter_runs'].sum()

    # Pressure performance
    hp = group[group['is_high_pressure_batting']]
    pressure_balls = len(hp)
    pressure_runs = hp['batter_runs'].sum()
    pressure_fours = hp['is_four_bool'].sum()
    pressure_sixes = hp['is_six_bool'].sum()
    pressure_dots = (hp['batter_runs'] == 0).sum()

    # Match info
    is_ipl = group['is_ipl'].iloc[0] if 'is_ipl' in group.columns else False
    is_t20i = group['is_t20i'].iloc[0] if 'is_t20i' in group.columns else False
    batting_order = group['batting_order'].iloc[0]
    batting_type = group['batting_type'].iloc[0]
    match_date = group['match_date'].iloc[0] if 'match_date' in group.columns else None

    batting_innings.append({
        'match_id': match_id,
        'innings': innings,
        'player_id': striker_id,
        'player_name': striker_name,
        'batting_order': batting_order,
        'batting_type': batting_type,
        'runs': runs,
        'balls': balls,
        'fours': fours,
        'sixes': sixes,
        'dots': dots,
        'singles': singles,
        'twos': twos,
        'threes': threes,
        'dismissed': dismissed,
        'strike_rate': round(runs / balls * 100, 2) if balls > 0 else 0,
        'boundary_runs': (fours * 4) + (sixes * 6),
        'non_boundary_runs': runs - (fours * 4) - (sixes * 6),
        'dot_pct': round(dots / balls * 100, 2) if balls > 0 else 0,
        'boundary_pct': round((fours + sixes) / balls * 100, 2) if balls > 0 else 0,
        'pp_balls': pp_balls, 'pp_runs': pp_runs,
        'mid_balls': mid_balls, 'mid_runs': mid_runs,
        'death_balls': death_balls, 'death_runs': death_runs,
        'pressure_balls': pressure_balls,
        'pressure_runs': pressure_runs,
        'pressure_fours': pressure_fours,
        'pressure_sixes': pressure_sixes,
        'pressure_dots': pressure_dots,
        'pressure_sr': round(pressure_runs / pressure_balls * 100, 2) if pressure_balls > 0 else np.nan,
        'pressure_dot_pct': round(pressure_dots / pressure_balls * 100, 2) if pressure_balls > 0 else np.nan,
        'is_ipl': is_ipl,
        'is_t20i': is_t20i,
        'match_date': match_date,
    })

bat_innings_df = pd.DataFrame(batting_innings)
bat_innings_df.to_csv(INTERIM_DIR / 'batting_innings.csv', index=False)
print(f"  Batting innings reconstructed: {len(bat_innings_df):,} (Dismissals: {bat_innings_df['dismissed'].sum():,})")

# Batting player stats function
def batting_player_stats(df, label='all'):
    grouped = df.groupby(['player_id', 'player_name'])

    stats = []
    for (pid, pname), grp in grouped:
        innings = len(grp)
        if innings < MIN_BATTER_INNINGS:
            continue

        total_runs = grp['runs'].sum()
        total_balls = grp['balls'].sum()
        if total_balls < MIN_BALLS_FACED:
            continue

        dismissed_innings = grp['dismissed'].sum()
        not_out = innings - dismissed_innings
        avg = total_runs / dismissed_innings if dismissed_innings > 0 else total_runs
        sr = total_runs / total_balls * 100 if total_balls > 0 else 0

        # Consistency metrics
        run_series = grp['runs'].values
        mean_runs = np.mean(run_series)
        median_runs = np.median(run_series)
        std_runs = np.std(run_series, ddof=1) if innings > 1 else 0
        cv = std_runs / mean_runs if mean_runs > 0 else 999
        iqr_runs = np.percentile(run_series, 75) - np.percentile(run_series, 25)
        mad_runs = np.median(np.abs(run_series - median_runs))

        # Frequency of contributions
        freq_0_9 = (run_series < 10).sum() / innings
        freq_10_19 = ((run_series >= 10) & (run_series < 20)).sum() / innings
        freq_20_plus = (run_series >= 20).sum() / innings
        freq_30_plus = (run_series >= 30).sum() / innings
        freq_50_plus = (run_series >= 50).sum() / innings

        # Pressure stats
        pressure_innings = grp[grp['pressure_balls'] >= 3]
        p_innings_count = len(pressure_innings)
        p_runs_total = pressure_innings['pressure_runs'].sum()
        p_balls_total = pressure_innings['pressure_balls'].sum()
        p_sr = p_runs_total / p_balls_total * 100 if p_balls_total > 0 else np.nan
        p_runs_per_innings = p_runs_total / p_innings_count if p_innings_count > 0 else np.nan
        p_dot_pct = pressure_innings['pressure_dot_pct'].median() if p_innings_count > 0 else np.nan

        # Pressure consistency
        p_sr_series = pressure_innings['pressure_sr'].dropna()
        p_sr_std = p_sr_series.std() if len(p_sr_series) > 1 else np.nan
        p_sr_cv = p_sr_std / p_sr_series.mean() if (len(p_sr_series) > 1 and p_sr_series.mean() > 0) else np.nan

        # Boundary stats
        total_fours = grp['fours'].sum()
        total_sixes = grp['sixes'].sum()
        boundary_pct = (total_fours + total_sixes) / total_balls * 100 if total_balls > 0 else 0

        # Strike rotation
        total_dots = grp['dots'].sum()
        total_singles = grp['singles'].sum()
        total_twos = grp['twos'].sum()
        dot_pct = total_dots / total_balls * 100 if total_balls > 0 else 0

        # Phase stats
        pp_balls_total = grp['pp_balls'].sum()
        pp_runs_total = grp['pp_runs'].sum()
        pp_sr = pp_runs_total / pp_balls_total * 100 if pp_balls_total > 0 else np.nan

        death_balls_total = grp['death_balls'].sum()
        death_runs_total = grp['death_runs'].sum()
        death_sr = death_runs_total / death_balls_total * 100 if death_balls_total > 0 else np.nan

        stats.append({
            'player_id': pid,
            'player_name': pname,
            'dataset': label,
            'innings': innings,
            'dismissed_innings': dismissed_innings,
            'not_out_innings': not_out,
            'total_runs': total_runs,
            'total_balls': total_balls,
            'average': round(avg, 2),
            'strike_rate': round(sr, 2),
            'mean_runs': round(mean_runs, 2),
            'median_runs': round(median_runs, 2),
            'std_runs': round(std_runs, 2),
            'cv_runs': round(cv, 3),
            'iqr_runs': round(iqr_runs, 2),
            'mad_runs': round(mad_runs, 2),
            'freq_sub10': round(freq_0_9, 3),
            'freq_10_19': round(freq_10_19, 3),
            'freq_20plus': round(freq_20_plus, 3),
            'freq_30plus': round(freq_30_plus, 3),
            'freq_50plus': round(freq_50_plus, 3),
            'highest_score': int(grp['runs'].max()),
            'total_fours': int(total_fours),
            'total_sixes': int(total_sixes),
            'boundary_pct': round(boundary_pct, 2),
            'dot_pct': round(dot_pct, 2),
            'total_dots': int(total_dots),
            'total_singles': int(total_singles),
            'total_twos': int(total_twos),
            'pp_balls': int(pp_balls_total),
            'pp_runs': int(pp_runs_total),
            'pp_sr': round(pp_sr, 2) if not np.isnan(pp_sr) else np.nan,
            'death_balls': int(death_balls_total),
            'death_runs': int(death_runs_total),
            'death_sr': round(death_sr, 2) if not np.isnan(death_sr) else np.nan,
            'pressure_innings_count': p_innings_count,
            'pressure_runs_total': round(p_runs_total, 2),
            'pressure_balls_total': round(p_balls_total, 2),
            'pressure_sr': round(p_sr, 2) if not np.isnan(p_sr) else np.nan,
            'pressure_runs_per_innings': round(p_runs_per_innings, 2) if not np.isnan(p_runs_per_innings) else np.nan,
            'pressure_dot_pct': round(p_dot_pct, 2) if not np.isnan(p_dot_pct) else np.nan,
            'pressure_sr_std': round(p_sr_std, 2) if not np.isnan(p_sr_std) else np.nan,
            'pressure_sr_cv': round(p_sr_cv, 3) if not np.isnan(p_sr_cv) else np.nan,
        })

    return pd.DataFrame(stats)

ipl_bat_innings = bat_innings_df[bat_innings_df['is_ipl'] == True]
t20i_bat_innings = bat_innings_df[bat_innings_df['is_t20i'] == True]
all_bat_innings = bat_innings_df.copy()

ipl_bat_stats = batting_player_stats(ipl_bat_innings, 'IPL')
t20i_bat_stats = batting_player_stats(t20i_bat_innings, 'T20I')
all_bat_stats = batting_player_stats(all_bat_innings, 'Combined')

ipl_bat_stats.to_csv(STATS_DIR / 'batting_stats_ipl.csv', index=False)
t20i_bat_stats.to_csv(STATS_DIR / 'batting_stats_t20i.csv', index=False)
all_bat_stats.to_csv(STATS_DIR / 'batting_stats_combined.csv', index=False)

print(f"  IPL qualifying batters:      {len(ipl_bat_stats)}")
print(f"  T20I qualifying batters:     {len(t20i_bat_stats)}")
print(f"  Combined qualifying batters: {len(all_bat_stats)}")
print("  Batting analysis complete and saved.")

