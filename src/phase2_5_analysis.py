"""
SupeRR Selector Season 2 — Phases 2-5: Match Reconstruction, Pressure Detection,
Batting & Bowling Analysis
Complete analytical pipeline for reliability modelling.
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
print("PHASES 2-5: MATCH RECONSTRUCTION, PRESSURE, BATTING & BOWLING")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ============================================================
# LOAD DATA
# ============================================================
if (INTERIM_DIR / 'bbb_pressure.csv').exists():
    print("\n[LOAD] Loading cached bbb_pressure.csv...")
    bbb_valid = pd.read_csv(INTERIM_DIR / 'bbb_pressure.csv', low_memory=False)
    print(f"  Loaded {len(bbb_valid):,} deliveries with pressure.")
else:
    print("\n[LOAD] Loading enriched datasets...")
    bbb = pd.read_csv(INTERIM_DIR / 'bbb_enriched.csv', low_memory=False)
    matches = pd.read_csv(INTERIM_DIR / 'matches_enriched.csv')

    # Keep only IPL + T20I
    bbb_valid = bbb[bbb['is_domestic_t20'] != True].copy()
    print(f"  Working dataset: {len(bbb_valid):,} deliveries (IPL + T20I)")

    # ============================================================
    # PHASE 2: MATCH RECONSTRUCTION
    # ============================================================
    print("\n[PHASE 2] Reconstructing match context delivery-by-delivery...")

# Sort correctly
bbb_valid = bbb_valid.sort_values(['match_id', 'innings', 'overid', 'over_ball_num']).reset_index(drop=True)

# Identify legal balls (count toward overs):
# Wides and Overstep (no-balls) are NOT legal balls faced by batter
# But all deliveries count in our dataset
bbb_valid['is_wide'] = bbb_valid['extras_type'] == 'wide'
bbb_valid['is_noball'] = bbb_valid['extras_type'] == 'Overstep'
bbb_valid['is_bye'] = bbb_valid['extras_type'] == 'byes'
bbb_valid['is_legbye'] = bbb_valid['extras_type'] == 'legbyes'
bbb_valid['is_penalty'] = bbb_valid['extras_type'] == 'Penalty'

# Legal ball = NOT a wide and NOT a no-ball (from bowling perspective: wides + no-balls are extras)
# From BATTER perspective: wides are not balls faced; no-balls ARE balls faced
# From BOWLER perspective: wides + no-balls are illegal deliveries (not counted in over)
bbb_valid['is_legal_ball'] = ~bbb_valid['is_wide'] & ~bbb_valid['is_noball']
bbb_valid['is_batter_ball'] = ~bbb_valid['is_wide']  # wides not faced by batter

# Boolean wicket flag
bbb_valid['is_wicket_bool'] = bbb_valid['is_wicket'].astype(str).str.lower().isin(['true', '1'])
bbb_valid['is_four_bool'] = bbb_valid['is_four'].astype(str).str.lower().isin(['true', '1'])
bbb_valid['is_six_bool'] = bbb_valid['is_six'].astype(str).str.lower().isin(['true', '1'])

# Batter runs: runs where not wide (wides are team extras, not batter runs)
# When is_wide=True, batter doesn't face ball, so batter_runs=0
# When is_noball=True, batter does face, batter gets run credit
# runs field = batter runs (we validate by is_four/is_six)
bbb_valid['batter_runs'] = bbb_valid['runs'].copy()
bbb_valid.loc[bbb_valid['is_wide'], 'batter_runs'] = 0

# Bowler conceded: batter_runs + wides + no-balls (but NOT byes or leg-byes which aren't charged to bowler)
bbb_valid['bowler_runs_conceded'] = bbb_valid['batter_runs'].copy()
bbb_valid.loc[bbb_valid['is_wide'], 'bowler_runs_conceded'] = bbb_valid.loc[bbb_valid['is_wide'], 'extras1_runs']
bbb_valid.loc[bbb_valid['is_noball'], 'bowler_runs_conceded'] += bbb_valid.loc[bbb_valid['is_noball'], 'extras1_runs']

# Bowler wicket credit: excludes run-outs
NON_BOWLER_DISMISSALS = ['Run Out', 'run out', 'Retired Hurt', 'retired hurt',
                          'Retired Out', 'retired out', 'Obstructing the field']
bbb_valid['bowler_wicket'] = (
    bbb_valid['is_wicket_bool'] &
    ~bbb_valid['dismissal_type'].isin(NON_BOWLER_DISMISSALS) &
    bbb_valid['dismissal_type'].notna()
)

# Team runs per delivery (team total)
bbb_valid['team_runs_delivery'] = bbb_valid['runs'] + bbb_valid['extras1_runs'] + bbb_valid['extras_2_runs']

# Innings phase
bbb_valid['phase'] = 'Middle'
bbb_valid.loc[bbb_valid['overid'] <= 6, 'phase'] = 'Powerplay'
bbb_valid.loc[bbb_valid['overid'] >= 16, 'phase'] = 'Death'

print("  Match context columns computed.")

# ============================================================
# CUMULATIVE MATCH STATE RECONSTRUCTION
# ============================================================
print("  Computing cumulative match state...")

# For each delivery, compute running totals within each match-innings
# We use groupby + cumsum for efficiency
bbb_valid['cum_team_runs'] = bbb_valid.groupby(['match_id', 'innings'])['team_runs_delivery'].cumsum()
bbb_valid['cum_wickets'] = bbb_valid.groupby(['match_id', 'innings'])['is_wicket_bool'].cumsum()
bbb_valid['cum_legal_balls'] = bbb_valid.groupby(['match_id', 'innings'])['is_legal_ball'].cumsum()

# State BEFORE this delivery (shift by 1 within group)
bbb_valid['score_before'] = bbb_valid.groupby(['match_id', 'innings'])['cum_team_runs'].shift(1).fillna(0)
bbb_valid['wickets_before'] = bbb_valid.groupby(['match_id', 'innings'])['cum_wickets'].shift(1).fillna(0)
bbb_valid['legal_balls_before'] = bbb_valid.groupby(['match_id', 'innings'])['cum_legal_balls'].shift(1).fillna(0)

bbb_valid['wickets_remaining'] = 10 - bbb_valid['wickets_before']
bbb_valid['overs_bowled'] = bbb_valid['legal_balls_before'] / 6
bbb_valid['balls_remaining'] = 120 - bbb_valid['legal_balls_before']  # for standard 20-over match

print("  Match state computed.")

# ============================================================
# FIRST INNINGS TOTALS (for second innings targets)
# ============================================================
print("  Computing first innings targets for second innings...")

first_innings_scores = (
    bbb_valid[bbb_valid['innings'] == 1]
    .groupby('match_id')['team_runs_delivery']
    .sum()
    .reset_index()
    .rename(columns={'team_runs_delivery': 'first_innings_total'})
)
first_innings_scores['target'] = first_innings_scores['first_innings_total'] + 1

bbb_valid = bbb_valid.merge(first_innings_scores, on='match_id', how='left')

# For 2nd innings: runs required, RRR
bbb_valid['runs_required'] = np.nan
bbb_valid.loc[bbb_valid['innings'] == 2, 'runs_required'] = (
    bbb_valid.loc[bbb_valid['innings'] == 2, 'target'] -
    bbb_valid.loc[bbb_valid['innings'] == 2, 'score_before']
)
bbb_valid['runs_required'] = bbb_valid['runs_required'].clip(lower=0)

bbb_valid['required_run_rate'] = np.nan
valid_2nd = (bbb_valid['innings'] == 2) & (bbb_valid['balls_remaining'] > 0)
bbb_valid.loc[valid_2nd, 'required_run_rate'] = (
    bbb_valid.loc[valid_2nd, 'runs_required'] * 6 /
    bbb_valid.loc[valid_2nd, 'balls_remaining']
)

# Current run rate (1st innings)
valid_crr = bbb_valid['legal_balls_before'] > 0
bbb_valid['current_run_rate'] = np.nan
bbb_valid.loc[valid_crr, 'current_run_rate'] = (
    bbb_valid.loc[valid_crr, 'score_before'] * 6 /
    bbb_valid.loc[valid_crr, 'legal_balls_before']
)

print("  RRR and CRR computed.")

# ============================================================
# PHASE 3: PRESSURE DETECTION
# ============================================================
print("\n[PHASE 3] Computing pressure index...")

# --- BATTING PRESSURE ---
# Pressure increases when:
# 1. RRR is high (chasing)
# 2. Wickets are falling
# 3. Balls remaining are few
# 4. First innings: required run rate projected vs par score
# 5. Death overs

bbb_valid['batting_pressure'] = 0.0

# Component 1: RRR-based pressure (second innings)
# RRR < 7: low, 7-10: moderate, 10-14: high, 14+: extreme
def rrr_pressure(rrr):
    if pd.isna(rrr):
        return 0.0
    if rrr >= 14:
        return 1.0
    elif rrr >= 10:
        return 0.7
    elif rrr >= 7:
        return 0.4
    else:
        return 0.1

bbb_valid['rrr_pressure'] = bbb_valid['required_run_rate'].apply(rrr_pressure)

# Component 2: Wickets in hand
bbb_valid['wicket_pressure'] = np.where(
    bbb_valid['wickets_remaining'] <= 2, 1.0,
    np.where(bbb_valid['wickets_remaining'] <= 4, 0.7,
    np.where(bbb_valid['wickets_remaining'] <= 6, 0.4, 0.1))
)

# Component 3: Phase-based pressure (death overs inherently higher)
bbb_valid['phase_pressure'] = np.where(
    bbb_valid['phase'] == 'Death', 0.6,
    np.where(bbb_valid['phase'] == 'Middle', 0.3, 0.2)
)

# Component 4: First innings par pressure
# If batting first, pressure rises if behind projected par (par = 8 rpo)
PAR_RATE = 8.0  # par score per over for typical T20
bbb_valid['par_deficit_pressure'] = 0.0
mask_inn1 = (bbb_valid['innings'] == 1) & (bbb_valid['legal_balls_before'] > 12)
bbb_valid.loc[mask_inn1, 'par_deficit_pressure'] = np.where(
    bbb_valid.loc[mask_inn1, 'current_run_rate'] < (PAR_RATE - 2), 0.5,
    np.where(bbb_valid.loc[mask_inn1, 'current_run_rate'] < (PAR_RATE - 1), 0.3, 0.1)
)

# Combined batting pressure index (weighted sum)
bbb_valid['batting_pressure_index'] = (
    0.40 * bbb_valid['rrr_pressure'] +
    0.25 * bbb_valid['wicket_pressure'] +
    0.20 * bbb_valid['phase_pressure'] +
    0.15 * bbb_valid['par_deficit_pressure']
)
bbb_valid['batting_pressure_index'] = bbb_valid['batting_pressure_index'].clip(0, 1)

# Batting pressure class
def classify_batting_pressure(idx):
    if idx >= 0.70: return 4  # Extreme
    elif idx >= 0.50: return 3  # High
    elif idx >= 0.30: return 2  # Moderate
    elif idx >= 0.10: return 1  # Low
    else: return 0  # Negligible

bbb_valid['batting_pressure_class'] = bbb_valid['batting_pressure_index'].apply(classify_batting_pressure)
bbb_valid['is_high_pressure_batting'] = bbb_valid['batting_pressure_class'] >= 3  # High or Extreme

# --- BOWLING PRESSURE ---
# Bowling pressure rises when:
# 1. Batting team has high RRR (need to defend close target)
# 2. Death overs
# 3. Few wickets have fallen (dangerous batting partnerships)
# 4. First innings: set a good total (defending a good score)

bbb_valid['bowling_pressure_index'] = 0.0

# Component 1: Close game - second innings
# If RRR < 10 (batting team can reach target comfortably), bowling under less pressure
# If RRR > 10, game is tight and bowling under more pressure
bbb_valid['bowling_rrr_pressure'] = np.where(
    bbb_valid['innings'] == 2,
    bbb_valid['rrr_pressure'],
    0.3  # first innings bowling always has some pressure
)

# Component 2: Wickets standing (fewer wickets = less bowling pressure, more batting pressure)
bbb_valid['bowling_wicket_pressure'] = np.where(
    bbb_valid['wickets_remaining'] >= 8, 0.5,  # lots of wickets = bowling needs to work hard
    np.where(bbb_valid['wickets_remaining'] >= 5, 0.4, 0.3)
)

# Component 3: Death over bowling pressure
bbb_valid['bowling_phase_pressure'] = np.where(
    bbb_valid['phase'] == 'Death', 0.8,
    np.where(bbb_valid['phase'] == 'Powerplay', 0.5, 0.3)
)

# Combined bowling pressure
bbb_valid['bowling_pressure_index'] = (
    0.35 * bbb_valid['bowling_rrr_pressure'] +
    0.25 * bbb_valid['bowling_wicket_pressure'] +
    0.40 * bbb_valid['bowling_phase_pressure']
)
bbb_valid['bowling_pressure_index'] = bbb_valid['bowling_pressure_index'].clip(0, 1)

bbb_valid['bowling_pressure_class'] = bbb_valid['batting_pressure_index'].apply(classify_batting_pressure)
bbb_valid['is_high_pressure_bowling'] = bbb_valid['bowling_pressure_index'] >= 0.5

print(f"  High-pressure batting deliveries: {bbb_valid['is_high_pressure_batting'].sum():,}")
print(f"  High-pressure bowling deliveries: {bbb_valid['is_high_pressure_bowling'].sum():,}")
print(f"  Pressure distribution (batting):")
for cls, label in PRESSURE_LEVELS.items():
    cnt = (bbb_valid['batting_pressure_class'] == cls).sum()
    print(f"    {label}: {cnt:,} ({cnt/len(bbb_valid)*100:.1f}%)")

# Save enriched BBB with pressure
bbb_valid.to_csv(INTERIM_DIR / 'bbb_pressure.csv', index=False)
print(f"\n  Saved bbb_pressure.csv")

# ============================================================
# PHASE 4: BATTING ANALYSIS
# ============================================================
print("\n[PHASE 4] Batting Analysis...")

# Only legal balls faced by batter
batting_df = bbb_valid[bbb_valid['is_batter_ball']].copy()

# Precompute all dismissals (handles striker and non-striker dismissals)
valid_d = bbb_valid[bbb_valid['is_wicket_bool'] & bbb_valid['dismissed_player_id'].notna()]
dismissed_tuples = set(zip(
    valid_d['match_id'],
    valid_d['innings'],
    valid_d['dismissed_player_id'].astype(float).astype(int)
))

# Match-level batting reconstruction
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
print(f"  Batting innings reconstructed: {len(bat_innings_df):,}")

# ============================================================
# BATTING PLAYER AGGREGATES
# ============================================================
print("  Computing player-level batting aggregates...")

def batting_player_stats(df, label='all'):
    # Filter: enough innings
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
        avg = total_runs / dismissed_innings if dismissed_innings > 0 else total_runs  # infinite avg
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
        pressure_innings = grp[grp['pressure_balls'] >= 3]  # min 3 pressure balls
        p_innings_count = len(pressure_innings)
        p_runs_total = pressure_innings['pressure_runs'].sum()
        p_balls_total = pressure_innings['pressure_balls'].sum()
        p_sr = p_runs_total / p_balls_total * 100 if p_balls_total > 0 else np.nan
        p_runs_per_innings = p_runs_total / p_innings_count if p_innings_count > 0 else np.nan
        p_dot_pct = pressure_innings['pressure_dot_pct'].median() if p_innings_count > 0 else np.nan

        # Pressure consistency (std of pressure SR across matches)
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

# Compute separately
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

# ============================================================
# PHASE 5: BOWLING ANALYSIS
# ============================================================
print("\n[PHASE 5] Bowling Analysis...")

bowling_df = bbb_valid.copy()

print("  Reconstructing innings-level bowling performances...")

bowling_innings = []
for (match_id, innings, bowler_id), group in bowling_df.groupby(['match_id', 'innings', 'bowler_id']):
    if len(group) == 0:
        continue
    bowler_name = group['bowler_name'].iloc[0]
    bowling_type = group['bowling_type'].iloc[0]
    pace_or_spin = group['pace_or_spin'].iloc[0]

    legal_balls = group['is_legal_ball'].sum()
    if legal_balls < 6:  # skip partial spells of < 1 over for per-spell analysis
        pass  # still include but flag

    runs_conceded = group['bowler_runs_conceded'].sum()
    wickets = group['bowler_wicket'].sum()
    dots = (group['is_legal_ball'] & (group['batter_runs'] == 0) & ~group['is_wide']).sum()
    fours_conceded = (group['is_four_bool']).sum()
    sixes_conceded = (group['is_six_bool']).sum()
    wides = group['is_wide'].sum()
    noballs = group['is_noball'].sum()

    overs = legal_balls / 6
    economy = runs_conceded / overs if overs > 0 else np.nan
    dot_pct = dots / legal_balls * 100 if legal_balls > 0 else np.nan
    boundary_pct = (fours_conceded + sixes_conceded) / legal_balls * 100 if legal_balls > 0 else np.nan

    # Phase breakdown
    pp = group[group['phase'] == 'Powerplay']
    mid = group[group['phase'] == 'Middle']
    death = group[group['phase'] == 'Death']

    pp_balls = pp['is_legal_ball'].sum()
    pp_runs = pp['bowler_runs_conceded'].sum()
    pp_wickets = pp['bowler_wicket'].sum()
    pp_econ = pp_runs / (pp_balls / 6) if pp_balls >= 6 else np.nan

    mid_balls = mid['is_legal_ball'].sum()
    mid_runs = mid['bowler_runs_conceded'].sum()
    mid_wickets = mid['bowler_wicket'].sum()
    mid_econ = mid_runs / (mid_balls / 6) if mid_balls >= 6 else np.nan

    death_balls = death['is_legal_ball'].sum()
    death_runs = death['bowler_runs_conceded'].sum()
    death_wickets = death['bowler_wicket'].sum()
    death_econ = death_runs / (death_balls / 6) if death_balls >= 6 else np.nan

    # Pressure bowling
    hp = group[group['is_high_pressure_bowling']]
    pressure_balls = hp['is_legal_ball'].sum()
    pressure_runs = hp['bowler_runs_conceded'].sum()
    pressure_wickets = hp['bowler_wicket'].sum()
    pressure_dots = (hp['is_legal_ball'] & (hp['batter_runs'] == 0) & ~hp['is_wide']).sum()
    pressure_econ = pressure_runs / (pressure_balls / 6) if pressure_balls >= 6 else np.nan

    is_ipl = group['is_ipl'].iloc[0] if 'is_ipl' in group.columns else False
    is_t20i = group['is_t20i'].iloc[0] if 'is_t20i' in group.columns else False
    match_date = group['match_date'].iloc[0] if 'match_date' in group.columns else None

    bowling_innings.append({
        'match_id': match_id,
        'innings': innings,
        'player_id': bowler_id,
        'player_name': bowler_name,
        'bowling_type': bowling_type,
        'pace_or_spin': pace_or_spin,
        'legal_balls': int(legal_balls),
        'overs': round(overs, 1),
        'runs_conceded': int(runs_conceded),
        'wickets': int(wickets),
        'dots': int(dots),
        'fours_conceded': int(fours_conceded),
        'sixes_conceded': int(sixes_conceded),
        'wides': int(wides),
        'noballs': int(noballs),
        'economy': round(economy, 2) if not np.isnan(economy) else np.nan,
        'dot_pct': round(dot_pct, 2) if not np.isnan(dot_pct) else np.nan,
        'boundary_pct': round(boundary_pct, 2) if not np.isnan(boundary_pct) else np.nan,
        'pp_balls': int(pp_balls), 'pp_runs': int(pp_runs),
        'pp_wickets': int(pp_wickets), 'pp_econ': pp_econ,
        'mid_balls': int(mid_balls), 'mid_runs': int(mid_runs),
        'mid_wickets': int(mid_wickets), 'mid_econ': mid_econ,
        'death_balls': int(death_balls), 'death_runs': int(death_runs),
        'death_wickets': int(death_wickets), 'death_econ': death_econ,
        'pressure_balls': int(pressure_balls),
        'pressure_runs': int(pressure_runs),
        'pressure_wickets': int(pressure_wickets),
        'pressure_dots': int(pressure_dots),
        'pressure_econ': round(pressure_econ, 2) if not np.isnan(pressure_econ) else np.nan,
        'is_ipl': is_ipl,
        'is_t20i': is_t20i,
        'match_date': match_date,
    })

bowl_innings_df = pd.DataFrame(bowling_innings)
bowl_innings_df.to_csv(INTERIM_DIR / 'bowling_innings.csv', index=False)
print(f"  Bowling innings reconstructed: {len(bowl_innings_df):,}")

# ============================================================
# BOWLING PLAYER AGGREGATES
# ============================================================
print("  Computing player-level bowling aggregates...")

def bowling_player_stats(df, label='all'):
    # At least MIN_BOWLER_INNINGS matches
    # Filter to spells with at least 6 legal balls
    df_valid = df[df['legal_balls'] >= 6].copy()
    grouped = df_valid.groupby(['player_id', 'player_name'])

    stats = []
    for (pid, pname), grp in grouped:
        matches = len(grp)
        if matches < MIN_BOWLER_INNINGS:
            continue

        total_balls = grp['legal_balls'].sum()
        if total_balls < MIN_BALLS_BOWLED:
            continue

        total_runs = grp['runs_conceded'].sum()
        total_wickets = grp['wickets'].sum()
        total_overs = total_balls / 6
        economy = total_runs / total_overs if total_overs > 0 else np.nan
        bowling_sr = total_balls / total_wickets if total_wickets > 0 else np.nan
        bowling_avg = total_runs / total_wickets if total_wickets > 0 else np.nan

        # Consistency metrics
        econ_series = grp['economy'].dropna().values
        mean_econ = np.mean(econ_series) if len(econ_series) > 0 else np.nan
        median_econ = np.median(econ_series) if len(econ_series) > 0 else np.nan
        std_econ = np.std(econ_series, ddof=1) if len(econ_series) > 1 else np.nan
        cv_econ = std_econ / mean_econ if (mean_econ and mean_econ > 0) else np.nan

        # Wicket consistency
        wicket_series = grp['wickets'].values
        wkts_per_match = wicket_series.mean()
        freq_0_wkt = (wicket_series == 0).sum() / matches
        freq_1plus = (wicket_series >= 1).sum() / matches
        freq_2plus = (wicket_series >= 2).sum() / matches
        freq_3plus = (wicket_series >= 3).sum() / matches

        # Dot balls
        total_dots = grp['dots'].sum()
        dot_pct = total_dots / total_balls * 100 if total_balls > 0 else np.nan

        # Boundary conceded
        total_fours = grp['fours_conceded'].sum()
        total_sixes = grp['sixes_conceded'].sum()
        boundary_pct = (total_fours + total_sixes) / total_balls * 100 if total_balls > 0 else np.nan

        # Extras
        total_wides = grp['wides'].sum()
        total_noballs = grp['noballs'].sum()

        # Phase stats
        pp_balls_total = grp['pp_balls'].sum()
        pp_runs_total = grp['pp_runs'].sum()
        pp_wickets_total = grp['pp_wickets'].sum()
        pp_econ = pp_runs_total / (pp_balls_total / 6) if pp_balls_total >= 12 else np.nan

        death_balls_total = grp['death_balls'].sum()
        death_runs_total = grp['death_runs'].sum()
        death_wickets_total = grp['death_wickets'].sum()
        death_econ = death_runs_total / (death_balls_total / 6) if death_balls_total >= 12 else np.nan

        # Pressure stats
        pressure_grp = grp[grp['pressure_balls'] >= 6]
        p_count = len(pressure_grp)
        p_balls = pressure_grp['pressure_balls'].sum()
        p_runs = pressure_grp['pressure_runs'].sum()
        p_wickets = pressure_grp['pressure_wickets'].sum()
        p_dots = pressure_grp['pressure_dots'].sum()
        p_econ = p_runs / (p_balls / 6) if p_balls >= 6 else np.nan
        p_dot_pct = p_dots / p_balls * 100 if p_balls > 0 else np.nan

        # Pressure consistency
        p_econ_series = pressure_grp['pressure_econ'].dropna().values
        p_econ_std = np.std(p_econ_series, ddof=1) if len(p_econ_series) > 1 else np.nan
        p_econ_cv = p_econ_std / np.mean(p_econ_series) if (len(p_econ_series) > 1 and np.mean(p_econ_series) > 0) else np.nan

        # Bowling type
        bowl_type = grp['bowling_type'].mode()[0] if len(grp) > 0 else 'Unknown'
        pace_spin = grp['pace_or_spin'].mode()[0] if len(grp) > 0 else 'Unknown'

        stats.append({
            'player_id': pid,
            'player_name': pname,
            'dataset': label,
            'bowling_type': bowl_type,
            'pace_or_spin': pace_spin,
            'matches': matches,
            'total_balls': int(total_balls),
            'total_overs': round(total_overs, 1),
            'total_runs': int(total_runs),
            'total_wickets': int(total_wickets),
            'economy': round(economy, 2) if not np.isnan(economy) else np.nan,
            'bowling_average': round(bowling_avg, 2) if not np.isnan(bowling_avg) else np.nan,
            'bowling_sr': round(bowling_sr, 2) if not np.isnan(bowling_sr) else np.nan,
            'mean_economy': round(mean_econ, 2) if not np.isnan(mean_econ) else np.nan,
            'median_economy': round(median_econ, 2) if not np.isnan(median_econ) else np.nan,
            'std_economy': round(std_econ, 2) if not np.isnan(std_econ) else np.nan,
            'cv_economy': round(cv_econ, 3) if not np.isnan(cv_econ) else np.nan,
            'wkts_per_match': round(wkts_per_match, 2),
            'freq_0wkt_match': round(freq_0_wkt, 3),
            'freq_1plus_wkt': round(freq_1plus, 3),
            'freq_2plus_wkt': round(freq_2plus, 3),
            'freq_3plus_wkt': round(freq_3plus, 3),
            'total_dots': int(total_dots),
            'dot_pct': round(dot_pct, 2) if not np.isnan(dot_pct) else np.nan,
            'fours_conceded': int(total_fours),
            'sixes_conceded': int(total_sixes),
            'boundary_pct': round(boundary_pct, 2) if not np.isnan(boundary_pct) else np.nan,
            'wides': int(total_wides),
            'noballs': int(total_noballs),
            'pp_balls': int(pp_balls_total),
            'pp_runs': int(pp_runs_total),
            'pp_wickets': int(pp_wickets_total),
            'pp_econ': round(pp_econ, 2) if not np.isnan(pp_econ) else np.nan,
            'death_balls': int(death_balls_total),
            'death_runs': int(death_runs_total),
            'death_wickets': int(death_wickets_total),
            'death_econ': round(death_econ, 2) if not np.isnan(death_econ) else np.nan,
            'pressure_match_count': p_count,
            'pressure_balls': int(p_balls),
            'pressure_runs': int(p_runs),
            'pressure_wickets': int(p_wickets),
            'pressure_dots': int(p_dots),
            'pressure_econ': round(p_econ, 2) if not np.isnan(p_econ) else np.nan,
            'pressure_dot_pct': round(p_dot_pct, 2) if not np.isnan(p_dot_pct) else np.nan,
            'pressure_econ_std': round(p_econ_std, 2) if not np.isnan(p_econ_std) else np.nan,
            'pressure_econ_cv': round(p_econ_cv, 3) if not np.isnan(p_econ_cv) else np.nan,
        })

    return pd.DataFrame(stats)

ipl_bowl_innings = bowl_innings_df[bowl_innings_df['is_ipl'] == True]
t20i_bowl_innings = bowl_innings_df[bowl_innings_df['is_t20i'] == True]
all_bowl_innings = bowl_innings_df.copy()

ipl_bowl_stats = bowling_player_stats(ipl_bowl_innings, 'IPL')
t20i_bowl_stats = bowling_player_stats(t20i_bowl_innings, 'T20I')
all_bowl_stats = bowling_player_stats(all_bowl_innings, 'Combined')

ipl_bowl_stats.to_csv(STATS_DIR / 'bowling_stats_ipl.csv', index=False)
t20i_bowl_stats.to_csv(STATS_DIR / 'bowling_stats_t20i.csv', index=False)
all_bowl_stats.to_csv(STATS_DIR / 'bowling_stats_combined.csv', index=False)

print(f"  IPL qualifying bowlers:      {len(ipl_bowl_stats)}")
print(f"  T20I qualifying bowlers:     {len(t20i_bowl_stats)}")
print(f"  Combined qualifying bowlers: {len(all_bowl_stats)}")

print(f"\n  Phases 2-5 completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("  All intermediate files saved.")

