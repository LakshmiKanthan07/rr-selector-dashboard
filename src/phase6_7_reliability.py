"""
SupeRR Selector Season 2 — Phase 6-7: Wicket Quality & Reliability Modelling
Contextual wicket quality scoring + composite reliability model with Bayesian shrinkage
"""

import pandas as pd
import numpy as np
import warnings
import sys
from pathlib import Path
from datetime import datetime
from scipy import stats

warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import *

print("=" * 70)
print("PHASES 6-7: WICKET QUALITY & RELIABILITY MODELLING")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ============================================================
# LOAD
# ============================================================
print("\n[LOAD] Loading processed data...")
bbb = pd.read_csv(INTERIM_DIR / 'bbb_pressure.csv', low_memory=False)
bat_innings = pd.read_csv(INTERIM_DIR / 'batting_innings.csv')
bowl_innings = pd.read_csv(INTERIM_DIR / 'bowling_innings.csv')
all_bat_stats = pd.read_csv(STATS_DIR / 'batting_stats_combined.csv')
all_bowl_stats = pd.read_csv(STATS_DIR / 'bowling_stats_combined.csv')
ipl_bat_stats = pd.read_csv(STATS_DIR / 'batting_stats_ipl.csv')
t20i_bat_stats = pd.read_csv(STATS_DIR / 'batting_stats_t20i.csv')
ipl_bowl_stats = pd.read_csv(STATS_DIR / 'bowling_stats_ipl.csv')
t20i_bowl_stats = pd.read_csv(STATS_DIR / 'bowling_stats_t20i.csv')

print(f"  BBB rows: {len(bbb):,}")
print(f"  Combined batting qualifying players: {len(all_bat_stats)}")
print(f"  Combined bowling qualifying players: {len(all_bowl_stats)}")

# ============================================================
# PHASE 6A: BATTER THREAT ESTIMATION (for wicket quality)
# ============================================================
print("\n[PHASE 6A] Computing batter threat estimates...")

# Batter threat = weighted combination of:
# 1. Historical average (quality of scorer)
# 2. Historical strike rate (scoring speed)
# 3. Frequency of meaningful contributions (30+)
# This is computed from ALL innings in the dataset, then used as a lookup

# Build batter historical profile from innings data
batter_profiles = []
for (pid, pname), grp in bat_innings.groupby(['player_id', 'player_name']):
    total_innings = len(grp)
    total_runs = grp['runs'].sum()
    total_balls = grp['balls'].sum()
    dismissed = grp['dismissed'].sum()
    avg = total_runs / dismissed if dismissed > 0 else total_runs
    sr = total_runs / total_balls * 100 if total_balls > 0 else 0
    freq_30plus = (grp['runs'] >= 30).sum() / total_innings if total_innings > 0 else 0

    # Threat score = normalised composite
    batter_profiles.append({
        'player_id': pid,
        'player_name': pname,
        'hist_innings': total_innings,
        'hist_avg': round(avg, 2),
        'hist_sr': round(sr, 2),
        'hist_freq_30plus': round(freq_30plus, 3),
    })

batter_profile_df = pd.DataFrame(batter_profiles)

# Normalise threat components
def robust_minmax(series):
    q5 = series.quantile(0.05)
    q95 = series.quantile(0.95)
    normed = (series - q5) / (q95 - q5)
    return normed.clip(0, 1)

batter_profile_df['threat_avg'] = robust_minmax(batter_profile_df['hist_avg'])
batter_profile_df['threat_sr'] = robust_minmax(batter_profile_df['hist_sr'])
batter_profile_df['threat_freq'] = robust_minmax(batter_profile_df['hist_freq_30plus'])

# Bayesian shrinkage on threat avg (shrink towards population mean for low-sample players)
pop_mean_avg = batter_profile_df['hist_avg'].mean()
batter_profile_df['threat_avg_shrunk'] = (
    (batter_profile_df['hist_innings'] * batter_profile_df['hist_avg'] +
     SHRINKAGE_K * pop_mean_avg) /
    (batter_profile_df['hist_innings'] + SHRINKAGE_K)
)
batter_profile_df['threat_avg_shrunk_norm'] = robust_minmax(batter_profile_df['threat_avg_shrunk'])

# Combined batter threat score
batter_profile_df['batter_threat_score'] = (
    0.45 * batter_profile_df['threat_avg_shrunk_norm'] +
    0.35 * batter_profile_df['threat_sr'] +
    0.20 * batter_profile_df['threat_freq']
).clip(0, 1)

batter_profile_df.to_csv(STATS_DIR / 'batter_threat_profiles.csv', index=False)
print(f"  Batter threat profiles computed: {len(batter_profile_df)}")

# ============================================================
# PHASE 6B: CONTEXTUAL WICKET QUALITY
# ============================================================
print("\n[PHASE 6B] Computing contextual wicket quality...")

# For each dismissal, compute:
# 1. Batter threat score (pre-match historical)
# 2. Batter's runs scored before dismissal in this innings
# 3. Balls faced before dismissal (established batter)
# 4. Bowling pressure at time of dismissal
# 5. Wickets remaining (how critical was this wicket?)
# 6. Phase of innings

# Get all wicket deliveries
wicket_bbb = bbb[bbb['is_wicket_bool'].astype(str).str.lower().isin(['true', '1'])].copy()
NON_BOWLER_DISMISSALS = ['Run Out', 'run out', 'Retired Hurt', 'retired hurt',
                          'Retired Out', 'retired out', 'Obstructing the field']
bowler_wickets = wicket_bbb[
    ~wicket_bbb['dismissal_type'].isin(NON_BOWLER_DISMISSALS) &
    wicket_bbb['dismissal_type'].notna()
].copy()

print(f"  Total wickets: {len(wicket_bbb):,}")
print(f"  Bowler-credited wickets: {len(bowler_wickets):,}")

# Merge batter threat
bowler_wickets = bowler_wickets.merge(
    batter_profile_df[['player_id', 'batter_threat_score', 'hist_innings']],
    left_on='striker_id',
    right_on='player_id',
    how='left'
)

# Compute runs scored before dismissal (cumulative batter runs in that innings up to this delivery)
# We reconstruct from bbb: sum of batter_runs for this striker in this match-innings before this delivery
# Use innings_ball_num to identify order
# Note: dismissed_player_id tells us WHO was dismissed (may differ from striker for some edge cases)
bowler_wickets['batter_threat_score'] = bowler_wickets['batter_threat_score'].fillna(0.3)  # unknown = average threat

# Established batter flag (faced > 15 balls before dismissal)
# Use score_before as a proxy — if batter scored significant runs, they were established
# (actual balls faced by batter before dismissal requires more complex tracking)
# We use wickets_before as a rough proxy: if fewer wickets have fallen, batter more likely established

bowler_wickets['was_established'] = (
    (bowler_wickets['batting_order'].fillna(5) <= 5) &
    (bowler_wickets.get('score_before', 0) > 20)
)

# Bowling pressure at wicket
bowler_wickets['pressure_at_wicket'] = bowler_wickets.get('bowling_pressure_index', 0.3).fillna(0.3)
bowler_wickets['wickets_remaining_at_wicket'] = bowler_wickets.get('wickets_remaining', 10).fillna(10)

# Phase weight
phase_weight = {'Powerplay': 0.9, 'Middle': 0.8, 'Death': 1.0}
bowler_wickets['phase_weight'] = bowler_wickets['phase'].map(phase_weight).fillna(0.8)

# Wicket quality score = multi-factor
bowler_wickets['wicket_quality'] = (
    0.40 * bowler_wickets['batter_threat_score'] +  # quality of dismissed batter
    0.25 * bowler_wickets['pressure_at_wicket'] +  # match pressure context
    0.20 * bowler_wickets['phase_weight'] +         # phase importance
    0.15 * np.where(                                # critical wicket (few remaining)
        bowler_wickets['wickets_remaining_at_wicket'] <= 4, 1.0,
        np.where(bowler_wickets['wickets_remaining_at_wicket'] <= 7, 0.6, 0.3)
    )
).clip(0, 1)

# Save wicket-level quality
bowler_wickets[['match_id', 'innings', 'overid', 'phase', 'bowler_id', 'bowler_name',
                'striker_id', 'striker_name', 'dismissal_type', 'batter_threat_score',
                'pressure_at_wicket', 'phase_weight', 'wickets_remaining_at_wicket',
                'wicket_quality', 'is_ipl', 'is_t20i']].to_csv(
    STATS_DIR / 'wicket_quality_all.csv', index=False)

# Player-level wicket quality aggregates
wq_stats = bowler_wickets.groupby(['bowler_id', 'bowler_name']).agg(
    total_wickets=('wicket_quality', 'count'),
    mean_wicket_quality=('wicket_quality', 'mean'),
    median_wicket_quality=('wicket_quality', 'median'),
    total_wicket_quality=('wicket_quality', 'sum'),
    high_quality_wickets=('wicket_quality', lambda x: (x >= 0.6).sum()),
    high_threat_dismissals=('batter_threat_score', lambda x: (x >= 0.6).sum()),
    pressure_wickets=('pressure_at_wicket', lambda x: (x >= 0.5).sum()),
).reset_index()
wq_stats.columns = ['player_id', 'player_name'] + list(wq_stats.columns[2:])

wq_stats_ipl = bowler_wickets[bowler_wickets['is_ipl'] == True].groupby(['bowler_id', 'bowler_name']).agg(
    ipl_wickets=('wicket_quality', 'count'),
    ipl_wicket_quality_sum=('wicket_quality', 'sum'),
    ipl_mean_wq=('wicket_quality', 'mean'),
).reset_index()
wq_stats_ipl.columns = ['player_id', 'player_name'] + list(wq_stats_ipl.columns[2:])

wq_stats = wq_stats.merge(wq_stats_ipl, on=['player_id', 'player_name'], how='left')
wq_stats.to_csv(STATS_DIR / 'wicket_quality_by_bowler.csv', index=False)
print(f"  Wicket quality computed for {len(wq_stats)} bowlers")

# ============================================================
# PHASE 7: RELIABILITY MODELLING
# ============================================================
print("\n[PHASE 7] Building reliability models...")

# ============================================================
# BATTING RELIABILITY MODEL
# ============================================================
print("\n  [7A] Batting reliability model...")

bat_df = all_bat_stats.copy()

# ---- COMPONENT 1: Quality Score ----
# Composite of average, strike rate, frequency of contributions
bat_df['qual_avg_norm'] = robust_minmax(bat_df['average'].fillna(0))
bat_df['qual_sr_norm'] = robust_minmax(bat_df['strike_rate'].fillna(0))
bat_df['qual_freq_norm'] = robust_minmax(bat_df['freq_30plus'].fillna(0))
bat_df['quality_score'] = (
    0.45 * bat_df['qual_avg_norm'] +
    0.35 * bat_df['qual_sr_norm'] +
    0.20 * bat_df['qual_freq_norm']
).clip(0, 1)

# ---- COMPONENT 2: Consistency Score ----
# Lower CV = more consistent; higher median = better floor; lower freq_sub10 = more reliable
# Invert CV (high CV = low consistency)
bat_df['cv_inv'] = 1 - robust_minmax(bat_df['cv_runs'].fillna(bat_df['cv_runs'].median()))
bat_df['median_norm'] = robust_minmax(bat_df['median_runs'].fillna(0))
bat_df['sub10_inv'] = 1 - robust_minmax(bat_df['freq_sub10'].fillna(bat_df['freq_sub10'].median()))
bat_df['freq20_norm'] = robust_minmax(bat_df['freq_20plus'].fillna(0))
bat_df['consistency_score'] = (
    0.30 * bat_df['cv_inv'] +
    0.30 * bat_df['sub10_inv'] +
    0.25 * bat_df['median_norm'] +
    0.15 * bat_df['freq20_norm']
).clip(0, 1)

# ---- COMPONENT 3: Pressure Performance Score ----
# High pressure SR, high pressure runs per innings
bat_df['p_sr_norm'] = robust_minmax(bat_df['pressure_sr'].fillna(bat_df['pressure_sr'].median()))
bat_df['p_runs_norm'] = robust_minmax(bat_df['pressure_runs_per_innings'].fillna(0))
bat_df['p_dot_inv'] = 1 - robust_minmax(bat_df['pressure_dot_pct'].fillna(bat_df['pressure_dot_pct'].median()))
bat_df['pressure_perf_score'] = (
    0.45 * bat_df['p_sr_norm'] +
    0.35 * bat_df['p_runs_norm'] +
    0.20 * bat_df['p_dot_inv']
).clip(0, 1)

# Replace NaN with 0 for players with no pressure innings data
bat_df['pressure_perf_score'] = bat_df['pressure_perf_score'].fillna(0)

# ---- COMPONENT 4: Pressure Consistency ----
# Low CV in pressure SR = consistent under pressure
# High pressure innings count = sample reliability
bat_df['p_sr_cv_inv'] = 1 - robust_minmax(bat_df['pressure_sr_cv'].fillna(bat_df['pressure_sr_cv'].median()))
bat_df['p_innings_norm'] = robust_minmax(bat_df['pressure_innings_count'].fillna(0))
bat_df['pressure_consistency'] = (
    0.60 * bat_df['p_sr_cv_inv'] +
    0.40 * bat_df['p_innings_norm']
).clip(0, 1)
bat_df['pressure_consistency'] = bat_df['pressure_consistency'].fillna(0)

# ---- COMPONENT 5: Boundary Conversion Score ----
bat_df['boundary_score'] = robust_minmax(bat_df['boundary_pct'].fillna(0)).clip(0, 1)

# ---- COMPONENT 6: Strike Rotation Score ----
# Low dot ball % = good rotation
bat_df['strike_rotation_score'] = (1 - robust_minmax(bat_df['dot_pct'].fillna(bat_df['dot_pct'].median()))).clip(0, 1)

# ---- COMPONENT 7: Acceleration Score ----
# Death SR vs overall SR proxy for acceleration
bat_df['death_sr_fillna'] = bat_df['death_sr'].fillna(bat_df['strike_rate'])
bat_df['accel_ratio'] = bat_df['death_sr_fillna'] / bat_df['strike_rate'].replace(0, np.nan)
bat_df['acceleration_score'] = robust_minmax(bat_df['accel_ratio'].fillna(1)).clip(0, 1)

# ---- BAYESIAN SHRINKAGE on quality and consistency ----
# Shrink towards population mean based on sample size
pop_qual = bat_df['quality_score'].mean()
pop_cons = bat_df['consistency_score'].mean()

bat_df['innings_weight'] = bat_df['innings'] / (bat_df['innings'] + SHRINKAGE_K)
bat_df['quality_score_shrunk'] = (
    bat_df['innings_weight'] * bat_df['quality_score'] +
    (1 - bat_df['innings_weight']) * pop_qual
)
bat_df['consistency_score_shrunk'] = (
    bat_df['innings_weight'] * bat_df['consistency_score'] +
    (1 - bat_df['innings_weight']) * pop_cons
)

# ---- FINAL BATTING RELIABILITY SCORE ----
bat_df['batting_reliability_score'] = (
    BATTING_WEIGHTS['quality_score'] * bat_df['quality_score_shrunk'] +
    BATTING_WEIGHTS['consistency_score'] * bat_df['consistency_score_shrunk'] +
    BATTING_WEIGHTS['pressure_perf_score'] * bat_df['pressure_perf_score'] +
    BATTING_WEIGHTS['pressure_consistency'] * bat_df['pressure_consistency'] +
    BATTING_WEIGHTS['boundary_score'] * bat_df['boundary_score'] +
    BATTING_WEIGHTS['strike_rotation_score'] * bat_df['strike_rotation_score'] +
    BATTING_WEIGHTS['acceleration_score'] * bat_df['acceleration_score']
)
bat_df['batting_reliability_score'] = bat_df['batting_reliability_score'].clip(0, 1)
bat_df['batting_reliability_pct'] = (bat_df['batting_reliability_score'] * 100).round(2)

# ---- SAMPLE SIZE RELIABILITY ----
bat_df['sample_reliability'] = np.where(
    bat_df['innings'] >= 30, 'High',
    np.where(bat_df['innings'] >= 20, 'Medium',
    np.where(bat_df['innings'] >= 10, 'Moderate', 'Low'))
)

# ---- BOOTSTRAP CONFIDENCE INTERVALS ----
print("    Computing bootstrap confidence intervals for batting scores...")
np.random.seed(42)
bat_cis = []
for _, row in bat_df.iterrows():
    pid = row['player_id']
    player_innings = bat_innings[bat_innings['player_id'] == pid]['runs'].values
    if len(player_innings) >= 5:
        boot_means = [np.mean(np.random.choice(player_innings, len(player_innings), replace=True))
                      for _ in range(500)]
        ci_low = np.percentile(boot_means, 2.5)
        ci_high = np.percentile(boot_means, 97.5)
    else:
        ci_low, ci_high = np.nan, np.nan
    bat_cis.append({'player_id': pid, 'runs_ci_low': round(ci_low, 2) if not np.isnan(ci_low) else np.nan,
                    'runs_ci_high': round(ci_high, 2) if not np.isnan(ci_high) else np.nan})

bat_ci_df = pd.DataFrame(bat_cis)
bat_df = bat_df.merge(bat_ci_df, on='player_id', how='left')

# Sort and rank
bat_df = bat_df.sort_values('batting_reliability_score', ascending=False).reset_index(drop=True)
bat_df['batting_rank'] = bat_df.index + 1

bat_df.to_csv(STATS_DIR / 'batting_reliability_model.csv', index=False)
print(f"  Batting reliability model saved: {len(bat_df)} players")

# ============================================================
# BOWLING RELIABILITY MODEL
# ============================================================
print("\n  [7B] Bowling reliability model...")

bowl_df = all_bowl_stats.copy()
bowl_df = bowl_df.merge(wq_stats[['player_id', 'mean_wicket_quality', 'high_threat_dismissals',
                                    'pressure_wickets', 'total_wickets']]
                         .rename(columns={'total_wickets': 'wq_total_wickets', 'pressure_wickets': 'wq_pressure_wickets'}),
                         on='player_id', how='left')

# ---- COMPONENT 1: Bowling Quality Score ----
# Lower economy = better; higher wickets per match = better; lower bowling_avg = better
bowl_df['econ_inv'] = 1 - robust_minmax(bowl_df['economy'].fillna(bowl_df['economy'].median()))
bowl_df['wkts_norm'] = robust_minmax(bowl_df['wkts_per_match'].fillna(0))
bowl_df['avg_inv'] = 1 - robust_minmax(bowl_df['bowling_average'].fillna(bowl_df['bowling_average'].median()))
bowl_df['quality_score'] = (
    0.40 * bowl_df['econ_inv'] +
    0.35 * bowl_df['wkts_norm'] +
    0.25 * bowl_df['avg_inv']
).clip(0, 1)

# ---- COMPONENT 2: Consistency Score ----
# Low CV economy = consistent; high freq of wicket-taking
bowl_df['econ_cv_inv'] = 1 - robust_minmax(bowl_df['cv_economy'].fillna(bowl_df['cv_economy'].median()))
bowl_df['freq1wkt_norm'] = robust_minmax(bowl_df['freq_1plus_wkt'].fillna(0))
bowl_df['freq0wkt_inv'] = 1 - robust_minmax(bowl_df['freq_0wkt_match'].fillna(bowl_df['freq_0wkt_match'].median()))
bowl_df['consistency_score'] = (
    0.40 * bowl_df['econ_cv_inv'] +
    0.35 * bowl_df['freq1wkt_norm'] +
    0.25 * bowl_df['freq0wkt_inv']
).clip(0, 1)

# ---- COMPONENT 3: Pressure Performance Score ----
# Lower pressure economy, more pressure wickets
bowl_df['p_econ_inv'] = 1 - robust_minmax(bowl_df['pressure_econ'].fillna(bowl_df['pressure_econ'].median()))
bowl_df['p_wkt_norm'] = robust_minmax(bowl_df['pressure_wickets'].fillna(0))
bowl_df['p_dot_norm'] = robust_minmax(bowl_df['pressure_dot_pct'].fillna(0))
bowl_df['pressure_perf_score'] = (
    0.45 * bowl_df['p_econ_inv'] +
    0.35 * bowl_df['p_wkt_norm'] +
    0.20 * bowl_df['p_dot_norm']
).clip(0, 1)
bowl_df['pressure_perf_score'] = bowl_df['pressure_perf_score'].fillna(0)

# ---- COMPONENT 4: Pressure Consistency ----
bowl_df['p_econ_cv_inv'] = 1 - robust_minmax(bowl_df['pressure_econ_cv'].fillna(bowl_df['pressure_econ_cv'].median()))
bowl_df['p_match_norm'] = robust_minmax(bowl_df['pressure_match_count'].fillna(0))
bowl_df['pressure_consistency'] = (
    0.60 * bowl_df['p_econ_cv_inv'] +
    0.40 * bowl_df['p_match_norm']
).clip(0, 1)
bowl_df['pressure_consistency'] = bowl_df['pressure_consistency'].fillna(0)

# ---- COMPONENT 5: Wicket Quality Score ----
bowl_df['wq_norm'] = robust_minmax(bowl_df['mean_wicket_quality'].fillna(0))
bowl_df['ht_wkt_norm'] = robust_minmax(bowl_df['high_threat_dismissals'].fillna(0))
bowl_df['wicket_quality_score'] = (
    0.60 * bowl_df['wq_norm'] +
    0.40 * bowl_df['ht_wkt_norm']
).clip(0, 1)

# ---- COMPONENT 6: Dot Ball Score ----
bowl_df['dot_ball_score'] = robust_minmax(bowl_df['dot_pct'].fillna(0)).clip(0, 1)

# ---- COMPONENT 7: Economy Control Score ----
bowl_df['economy_control_score'] = bowl_df['econ_inv'].clip(0, 1)

# ---- BAYESIAN SHRINKAGE ----
pop_qual_b = bowl_df['quality_score'].mean()
pop_cons_b = bowl_df['consistency_score'].mean()

bowl_df['match_weight'] = bowl_df['matches'] / (bowl_df['matches'] + SHRINKAGE_K)
bowl_df['quality_score_shrunk'] = (
    bowl_df['match_weight'] * bowl_df['quality_score'] +
    (1 - bowl_df['match_weight']) * pop_qual_b
)
bowl_df['consistency_score_shrunk'] = (
    bowl_df['match_weight'] * bowl_df['consistency_score'] +
    (1 - bowl_df['match_weight']) * pop_cons_b
)

# ---- FINAL BOWLING RELIABILITY SCORE ----
bowl_df['bowling_reliability_score'] = (
    BOWLING_WEIGHTS['quality_score'] * bowl_df['quality_score_shrunk'] +
    BOWLING_WEIGHTS['consistency_score'] * bowl_df['consistency_score_shrunk'] +
    BOWLING_WEIGHTS['pressure_perf_score'] * bowl_df['pressure_perf_score'] +
    BOWLING_WEIGHTS['pressure_consistency'] * bowl_df['pressure_consistency'] +
    BOWLING_WEIGHTS['wicket_quality_score'] * bowl_df['wicket_quality_score'] +
    BOWLING_WEIGHTS['dot_ball_score'] * bowl_df['dot_ball_score'] +
    BOWLING_WEIGHTS['economy_control_score'] * bowl_df['economy_control_score']
)
bowl_df['bowling_reliability_score'] = bowl_df['bowling_reliability_score'].clip(0, 1)
bowl_df['bowling_reliability_pct'] = (bowl_df['bowling_reliability_score'] * 100).round(2)

# ---- SAMPLE SIZE ----
bowl_df['sample_reliability'] = np.where(
    bowl_df['matches'] >= 30, 'High',
    np.where(bowl_df['matches'] >= 20, 'Medium',
    np.where(bowl_df['matches'] >= 10, 'Moderate', 'Low'))
)

# ---- BOOTSTRAP CIs ----
print("    Computing bootstrap confidence intervals for bowling scores...")
np.random.seed(42)
bowl_cis = []
for _, row in bowl_df.iterrows():
    pid = row['player_id']
    player_spells = bowl_innings[bowl_innings['player_id'] == pid]['economy'].dropna().values
    if len(player_spells) >= 5:
        boot_means = [np.mean(np.random.choice(player_spells, len(player_spells), replace=True))
                      for _ in range(500)]
        ci_low = np.percentile(boot_means, 2.5)
        ci_high = np.percentile(boot_means, 97.5)
    else:
        ci_low, ci_high = np.nan, np.nan
    bowl_cis.append({'player_id': pid,
                     'econ_ci_low': round(ci_low, 2) if not np.isnan(ci_low) else np.nan,
                     'econ_ci_high': round(ci_high, 2) if not np.isnan(ci_high) else np.nan})

bowl_ci_df = pd.DataFrame(bowl_cis)
bowl_df = bowl_df.merge(bowl_ci_df, on='player_id', how='left')

# Sort and rank
bowl_df = bowl_df.sort_values('bowling_reliability_score', ascending=False).reset_index(drop=True)
bowl_df['bowling_rank'] = bowl_df.index + 1

bowl_df.to_csv(STATS_DIR / 'bowling_reliability_model.csv', index=False)
print(f"  Bowling reliability model saved: {len(bowl_df)} players")

# ============================================================
# GENERATE TOP-10 LISTS
# ============================================================
print("\n[RANKINGS] Generating Top-10 lists...")

# TOP 10 BATTERS
top10_bat = bat_df.head(10).copy()
top10_bat_output = top10_bat[[
    'batting_rank', 'player_name', 'player_id', 'innings', 'total_runs', 'average', 'strike_rate',
    'pressure_runs_total', 'pressure_sr', 'pressure_sr_cv', 'cv_runs',
    'total_singles', 'total_twos', 'boundary_pct', 'dot_pct', 'death_sr',
    'pressure_innings_count', 'pressure_dot_pct',
    'batting_reliability_score', 'batting_reliability_pct',
    'sample_reliability', 'runs_ci_low', 'runs_ci_high',
    'quality_score_shrunk', 'consistency_score_shrunk',
    'pressure_perf_score', 'pressure_consistency',
    'boundary_score', 'strike_rotation_score', 'acceleration_score'
]].rename(columns={
    'batting_rank': 'Rank',
    'player_name': 'Player',
    'player_id': 'Player_ID',
    'innings': 'Innings',
    'total_runs': 'Total_Runs',
    'average': 'Average',
    'strike_rate': 'Strike_Rate',
    'pressure_runs_total': 'Pressure_Runs',
    'pressure_sr': 'Pressure_SR',
    'pressure_sr_cv': 'Pressure_SR_CV',
    'cv_runs': 'Runs_CV',
    'total_singles': 'Singles',
    'total_twos': 'Twos',
    'boundary_pct': 'Boundary_Pct',
    'dot_pct': 'Dot_Pct',
    'death_sr': 'Death_SR',
    'pressure_innings_count': 'Pressure_Innings',
    'pressure_dot_pct': 'Pressure_Dot_Pct',
    'batting_reliability_score': 'Reliability_Score',
    'batting_reliability_pct': 'Reliability_Pct',
    'sample_reliability': 'Sample_Reliability',
    'runs_ci_low': 'Runs_CI_Low',
    'runs_ci_high': 'Runs_CI_High',
    'quality_score_shrunk': 'Quality_Component',
    'consistency_score_shrunk': 'Consistency_Component',
    'pressure_perf_score': 'Pressure_Perf_Component',
    'pressure_consistency': 'Pressure_Consistency_Component',
    'boundary_score': 'Boundary_Component',
    'strike_rotation_score': 'Strike_Rotation_Component',
    'acceleration_score': 'Acceleration_Component',
})

# TOP 10 BOWLERS
top10_bowl = bowl_df.head(10).copy()
top10_bowl_output = top10_bowl[[
    'bowling_rank', 'player_name', 'player_id', 'matches', 'total_balls', 'total_runs', 'total_wickets',
    'economy', 'pressure_wickets', 'pressure_econ', 'pressure_econ_cv', 'cv_economy',
    'mean_wicket_quality', 'high_threat_dismissals', 'dot_pct', 'boundary_pct',
    'pressure_match_count', 'pressure_dot_pct',
    'bowling_reliability_score', 'bowling_reliability_pct',
    'sample_reliability', 'econ_ci_low', 'econ_ci_high',
    'quality_score_shrunk', 'consistency_score_shrunk',
    'pressure_perf_score', 'pressure_consistency',
    'wicket_quality_score', 'dot_ball_score', 'economy_control_score'
]].rename(columns={
    'bowling_rank': 'Rank',
    'player_name': 'Player',
    'player_id': 'Player_ID',
    'matches': 'Matches',
    'total_balls': 'Legal_Balls',
    'total_runs': 'Runs_Conceded',
    'total_wickets': 'Wickets',
    'economy': 'Economy',
    'pressure_wickets': 'Pressure_Wickets',
    'pressure_econ': 'Pressure_Economy',
    'pressure_econ_cv': 'Pressure_Econ_CV',
    'cv_economy': 'Economy_CV',
    'mean_wicket_quality': 'Avg_Wicket_Quality',
    'high_threat_dismissals': 'High_Threat_Dismissals',
    'dot_pct': 'Dot_Ball_Pct',
    'boundary_pct': 'Boundary_Conceded_Pct',
    'pressure_match_count': 'Pressure_Match_Count',
    'pressure_dot_pct': 'Pressure_Dot_Pct',
    'bowling_reliability_score': 'Reliability_Score',
    'bowling_reliability_pct': 'Reliability_Pct',
    'sample_reliability': 'Sample_Reliability',
    'econ_ci_low': 'Economy_CI_Low',
    'econ_ci_high': 'Economy_CI_High',
    'quality_score_shrunk': 'Quality_Component',
    'consistency_score_shrunk': 'Consistency_Component',
    'pressure_perf_score': 'Pressure_Perf_Component',
    'pressure_consistency': 'Pressure_Consistency_Component',
    'wicket_quality_score': 'Wicket_Quality_Component',
    'dot_ball_score': 'Dot_Ball_Component',
    'economy_control_score': 'Economy_Control_Component',
})

# Save final rankings
top10_bat_output.to_csv(RANKINGS_DIR / 'Top_10_Batters.csv', index=False)
top10_bowl_output.to_csv(RANKINGS_DIR / 'Top_10_Bowlers.csv', index=False)

# Also save to final submission folder
top10_bat_output.to_csv(SUBMISSION_DIR / 'Top_10_Batters.csv', index=False)
top10_bowl_output.to_csv(SUBMISSION_DIR / 'Top_10_Bowlers.csv', index=False)

print("\n" + "=" * 70)
print("TOP 10 BATTERS UNDER PRESSURE")
print("=" * 70)
print(top10_bat_output[['Rank', 'Player', 'Innings', 'Total_Runs', 'Average',
                          'Strike_Rate', 'Pressure_SR', 'Reliability_Pct', 'Sample_Reliability']].to_string(index=False))

print("\n" + "=" * 70)
print("TOP 10 BOWLERS UNDER PRESSURE")
print("=" * 70)
print(top10_bowl_output[['Rank', 'Player', 'Matches', 'Wickets',
                          'Economy', 'Pressure_Economy', 'Avg_Wicket_Quality',
                          'Reliability_Pct', 'Sample_Reliability']].to_string(index=False))

print(f"\n  Phases 6-7 completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

