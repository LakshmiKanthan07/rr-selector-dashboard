"""
SupeRR Selector Season 2 — Phase 1: Data Audit & Quality Report
Comprehensive data inspection, quality assessment, and feature availability matrix.
"""

import pandas as pd
import numpy as np
import warnings
import sys
import os
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import *

print("=" * 70)
print("PHASE 1: DATA AUDIT & QUALITY REPORT")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# ============================================================
# LOAD ALL DATASETS
# ============================================================
print("\n[1/8] Loading datasets...")

bbb = pd.read_csv(BBB_FILE)
matches = pd.read_csv(MATCHES_FILE)
playing11 = pd.read_csv(PLAYING_11_FILE)
competitions = pd.read_csv(COMPETITIONS_FILE)
teams = pd.read_csv(TEAMS_FILE)
ctpm = pd.read_csv(CTPM_FILE)

print(f"  ball_by_ball:                {len(bbb):,} rows")
print(f"  matches:                     {len(matches):,} rows")
print(f"  playing_eleven:              {len(playing11):,} rows")
print(f"  competitions:                {len(competitions):,} rows")
print(f"  teams:                       {len(teams):,} rows")
print(f"  competition_team_player_map: {len(ctpm):,} rows")

# ============================================================
# SCHEMA DOCUMENTATION
# ============================================================
print("\n[2/8] Documenting schemas...")

schema_info = []
for name, df in [('ball_by_ball', bbb), ('matches', matches),
                  ('playing_eleven', playing11), ('competitions', competitions),
                  ('teams', teams), ('competition_team_player_mapping', ctpm)]:
    for col in df.columns:
        null_count = df[col].isna().sum()
        unique_count = df[col].nunique()
        sample_values = str(df[col].dropna().iloc[:3].tolist()) if len(df[col].dropna()) > 0 else ''
        schema_info.append({
            'table': name,
            'column': col,
            'dtype': str(df[col].dtype),
            'null_count': null_count,
            'null_pct': round(null_count / len(df) * 100, 2),
            'unique_count': unique_count,
            'sample_values': sample_values[:100]
        })

schema_df = pd.DataFrame(schema_info)
schema_df.to_csv(METADATA_DIR / 'data_dictionary.csv', index=False)
print(f"  Saved data_dictionary.csv ({len(schema_df)} entries)")

# ============================================================
# COMPETITION CLASSIFICATION
# ============================================================
print("\n[3/8] Classifying competitions (IPL vs T20I)...")

competitions['is_ipl'] = competitions['comp_name'].str.contains('Indian Premier League|IPL', case=False, na=False)
competitions['is_t20i'] = competitions['match_format'] == 'T20I'
competitions['is_domestic_t20'] = (~competitions['is_ipl']) & (~competitions['is_t20i']) & (competitions['match_format'] == 'T20')

ipl_comps = competitions[competitions['is_ipl']]
t20i_comps = competitions[competitions['is_t20i']]
domestic_comps = competitions[competitions['is_domestic_t20']]

print(f"  IPL competitions:      {len(ipl_comps)}")
print(f"  T20I competitions:     {len(t20i_comps)}")
print(f"  Domestic T20 (OTHER):  {len(domestic_comps)}")
print(f"  Total competitions:    {len(competitions)}")

print("\n  IPL competitions found:")
for _, row in ipl_comps.iterrows():
    print(f"    - [{row['comp_id']}] {row['comp_name']} (Season: {row['season']})")

print("\n  T20I competition sample (first 10):")
for _, row in t20i_comps.head(10).iterrows():
    print(f"    - [{row['comp_id']}] {row['comp_name']} (Season: {row['season']})")

# Save competition classification
competitions.to_csv(METADATA_DIR / 'competitions_classified.csv', index=False)

# ============================================================
# MATCH COVERAGE
# ============================================================
print("\n[4/8] Analysing match coverage...")

matches_enriched = matches.merge(competitions[['comp_id', 'is_ipl', 'is_t20i', 'is_domestic_t20', 'comp_name']], on='comp_id', how='left')

ipl_matches = matches_enriched[matches_enriched['is_ipl'] == True]
t20i_matches = matches_enriched[matches_enriched['is_t20i'] == True]
domestic_matches = matches_enriched[matches_enriched['is_domestic_t20'] == True]

print(f"  IPL matches:      {len(ipl_matches)}")
print(f"  T20I matches:     {len(t20i_matches)}")
print(f"  Domestic T20:     {len(domestic_matches)}")
print(f"  Total matches:    {len(matches)}")

# Date range
matches['match_date'] = pd.to_datetime(matches['match_date'], errors='coerce')
print(f"  Date range: {matches['match_date'].min().date()} to {matches['match_date'].max().date()}")

# ============================================================
# BALL-BY-BALL ENRICHMENT & VALIDATION
# ============================================================
print("\n[5/8] Enriching ball-by-ball with competition context...")

bbb_enriched = bbb.merge(matches_enriched[['match_id', 'comp_id', 'is_ipl', 'is_t20i', 'is_domestic_t20',
                                            'match_date', 'win_team_id', 'home_team_id', 'away_team_id',
                                            'knock_out', 'result']], on='match_id', how='left')

ipl_bbb = bbb_enriched[bbb_enriched['is_ipl'] == True]
t20i_bbb = bbb_enriched[bbb_enriched['is_t20i'] == True]
domestic_bbb = bbb_enriched[bbb_enriched['is_domestic_t20'] == True]

print(f"  IPL deliveries:      {len(ipl_bbb):,}")
print(f"  T20I deliveries:     {len(t20i_bbb):,}")
print(f"  Domestic T20 deliveries: {len(domestic_bbb):,}")
print(f"  Unclassified:        {len(bbb_enriched[bbb_enriched['is_ipl'].isna()]):,}")

# ============================================================
# DATA QUALITY CHECKS
# ============================================================
print("\n[6/8] Running data quality checks...")

quality_issues = []

# Check 1: Missing match_ids in bbb
bbb_match_ids = set(bbb['match_id'].unique())
match_ids = set(matches['match_id'].unique())
orphan_bbb = bbb_match_ids - match_ids
print(f"  Deliveries with no match record: {len(bbb[bbb['match_id'].isin(orphan_bbb)])}")
if orphan_bbb:
    quality_issues.append({'check': 'orphan_bbb_match_ids', 'severity': 'HIGH',
                           'count': len(orphan_bbb), 'details': 'BBB rows with no match record'})

# Check 2: Runs field validation
print(f"  Runs field: min={bbb['runs'].min()}, max={bbb['runs'].max()}, nulls={bbb['runs'].isna().sum()}")
invalid_runs = bbb[bbb['runs'] < 0]
if len(invalid_runs) > 0:
    quality_issues.append({'check': 'negative_runs', 'severity': 'HIGH',
                           'count': len(invalid_runs), 'details': 'Deliveries with negative runs'})

# Check 3: is_four / is_six consistency
bbb['is_four_bool'] = bbb['is_four'].astype(str).str.lower().isin(['true', '1', 'yes'])
bbb['is_six_bool'] = bbb['is_six'].astype(str).str.lower().isin(['true', '1', 'yes'])
bbb['is_wicket_bool'] = bbb['is_wicket'].astype(str).str.lower().isin(['true', '1', 'yes'])

four_runs_mismatch = bbb[bbb['is_four_bool'] & (bbb['runs'] != 4)]
six_runs_mismatch = bbb[bbb['is_six_bool'] & (bbb['runs'] != 6)]
print(f"  is_four=True but runs!=4: {len(four_runs_mismatch)}")
print(f"  is_six=True but runs!=6: {len(six_runs_mismatch)}")

# Check 4: Wicket flag vs dismissal type consistency
wicket_no_type = bbb[bbb['is_wicket_bool'] & bbb['dismissal_type'].isna()]
no_wicket_has_type = bbb[~bbb['is_wicket_bool'] & bbb['dismissal_type'].notna()]
print(f"  is_wicket=True but no dismissal_type: {len(wicket_no_type)}")
print(f"  is_wicket=False but has dismissal_type: {len(no_wicket_has_type)}")

# Check 5: Extras types
print(f"  Extras types: {bbb['extras_type'].value_counts().to_dict()}")

# Check 6: Over number validity
invalid_overs = bbb[(bbb['overid'] < 1) | (bbb['overid'] > 20)]
print(f"  Invalid over numbers (< 1 or > 20): {len(invalid_overs)}")

# Check 7: Ball number validity
invalid_balls = bbb[(bbb['over_ball_num'] < 1) | (bbb['over_ball_num'] > 10)]
print(f"  Unusual ball numbers per over (> 6, possibly wides/no-balls): {len(bbb[bbb['over_ball_num'] > 6])}")

# Check 8: Duplicate deliveries
dup_deliveries = bbb[bbb.duplicated(['match_id', 'innings', 'overid', 'over_ball_num', 'innings_ball_num'])]
print(f"  Duplicate delivery records: {len(dup_deliveries)}")
if len(dup_deliveries) > 0:
    quality_issues.append({'check': 'duplicate_deliveries', 'severity': 'HIGH',
                           'count': len(dup_deliveries), 'details': 'Duplicate BBB records'})

# Save quality report
quality_df = pd.DataFrame(quality_issues) if quality_issues else pd.DataFrame(
    columns=['check', 'severity', 'count', 'details'])
quality_df.to_csv(AUDIT_DIR / 'data_quality_report.csv', index=False)

# ============================================================
# FEATURE AVAILABILITY MATRIX
# ============================================================
print("\n[7/8] Building feature availability matrix...")

features = [
    # BATTING FEATURES
    {'feature': 'batter_runs', 'source': 'bbb.runs', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'runs column contains batter runs for non-extras deliveries', 'available': True},
    {'feature': 'balls_faced', 'source': 'bbb.extras_type', 'type': 'DERIVED',
     'notes': 'Legal balls = deliveries where extras_type is None, wide or no-ball (but no-balls still count as balls faced by batter)', 'available': True},
    {'feature': 'singles', 'source': 'bbb.runs + extras check', 'type': 'DERIVED',
     'notes': 'runs==1 and not a boundary and not a wide', 'available': True},
    {'feature': 'twos', 'source': 'bbb.runs', 'type': 'DERIVED',
     'notes': 'runs==2', 'available': True},
    {'feature': 'threes', 'source': 'bbb.runs', 'type': 'DERIVED',
     'notes': 'runs==3', 'available': True},
    {'feature': 'fours', 'source': 'bbb.is_four', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'is_four column', 'available': True},
    {'feature': 'sixes', 'source': 'bbb.is_six', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'is_six column', 'available': True},
    {'feature': 'dot_balls', 'source': 'bbb.runs', 'type': 'DERIVED',
     'notes': 'runs==0 and not a wide', 'available': True},
    {'feature': 'dismissal_type', 'source': 'bbb.dismissal_type', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'dismissal_type column', 'available': True},
    {'feature': 'dismissed_player', 'source': 'bbb.dismissed_player_id', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'dismissed_player_id column', 'available': True},
    {'feature': 'batting_position', 'source': 'bbb.batting_order', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'batting_order column', 'available': True},
    {'feature': 'batting_type', 'source': 'bbb.batting_type', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'RHB/LHB', 'available': True},
    {'feature': 'innings_phase', 'source': 'bbb.overid', 'type': 'DERIVED',
     'notes': 'PP=1-6, Middle=7-15, Death=16-20', 'available': True},
    {'feature': 'catches', 'source': 'bbb.dismissal_type', 'type': 'DERIVED',
     'notes': 'Only catches WHERE dismissed_player is known. Cannot identify fielder from BBB.', 'available': False},
    {'feature': 'dropped_catches', 'source': 'N/A', 'type': 'UNAVAILABLE',
     'notes': 'No fielding error data in supplied datasets', 'available': False},
    {'feature': 'strike_rotation_detail', 'source': 'bbb.runs', 'type': 'DERIVED',
     'notes': 'Singles and twos derived from runs field', 'available': True},
    {'feature': 'partnership_runs', 'source': 'bbb.striker_id+non_striker_id+runs', 'type': 'DERIVED',
     'notes': 'Accumulate while same pair at crease', 'available': True},
    {'feature': 'required_run_rate', 'source': 'match reconstruction', 'type': 'DERIVED',
     'notes': 'Requires match target, balls remaining, runs needed', 'available': True},
    {'feature': 'win_probability', 'source': 'N/A', 'type': 'MODEL_ESTIMATED',
     'notes': 'No WP model in data; will be derived from match state', 'available': True},
    {'feature': 'pitch_conditions', 'source': 'N/A', 'type': 'UNAVAILABLE',
     'notes': 'Not in supplied datasets', 'available': False},
    {'feature': 'weather_conditions', 'source': 'N/A', 'type': 'UNAVAILABLE',
     'notes': 'Not in supplied datasets', 'available': False},
    # BOWLING FEATURES
    {'feature': 'legal_balls_bowled', 'source': 'bbb.extras_type', 'type': 'DERIVED',
     'notes': 'Exclude wides and no-balls from legal ball count', 'available': True},
    {'feature': 'runs_conceded', 'source': 'bbb.runs + extras', 'type': 'DERIVED',
     'notes': 'runs + extras1_runs (wides/no-balls) but NOT byes/leg-byes', 'available': True},
    {'feature': 'wickets_taken', 'source': 'bbb.is_wicket + dismissal_type', 'type': 'DERIVED',
     'notes': 'Exclude run-outs not credited to bowler', 'available': True},
    {'feature': 'bowling_type', 'source': 'bbb.bowling_type', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'Full bowling type description', 'available': True},
    {'feature': 'pace_or_spin', 'source': 'bbb.pace_or_spin', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'Pace/Spin classification', 'available': True},
    {'feature': 'delivery_style', 'source': 'bbb.delivery_style', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'Swing/seam/etc.', 'available': True},
    {'feature': 'bowl_speed', 'source': 'bbb.bowl_speed', 'type': 'DIRECTLY_AVAILABLE',
     'notes': 'Many zeros — may be missing/not measured', 'available': False},
    {'feature': 'stumpings', 'source': 'bbb.dismissal_type', 'type': 'DERIVED',
     'notes': 'Filter dismissal_type == Stumped', 'available': True},
    {'feature': 'missed_stumpings', 'source': 'N/A', 'type': 'UNAVAILABLE',
     'notes': 'Not in supplied datasets', 'available': False},
    {'feature': 'fielding_errors', 'source': 'N/A', 'type': 'UNAVAILABLE',
     'notes': 'Not in supplied datasets', 'available': False},
    {'feature': 'captaincy_decisions', 'source': 'matches.captain_ids', 'type': 'PARTIALLY_AVAILABLE',
     'notes': 'Captain identified but tactical decisions not in data', 'available': False},
    {'feature': 'opposition_quality', 'source': 'historical performance', 'type': 'MODEL_ESTIMATED',
     'notes': 'Can estimate from prior innings performance', 'available': True},
]

feat_df = pd.DataFrame(features)
feat_df.to_csv(METADATA_DIR / 'feature_availability_matrix.csv', index=False)
print(f"  Feature availability matrix: {len(feat_df)} features documented")
print(f"  Available: {feat_df['available'].sum()}, Unavailable: {(~feat_df['available']).sum()}")

# ============================================================
# DATASET INVENTORY
# ============================================================
print("\n[8/8] Creating dataset inventory...")

inventory = []
for name, df, filepath in [
    ('ball_by_ball', bbb, BBB_FILE),
    ('matches', matches, MATCHES_FILE),
    ('playing_eleven', playing11, PLAYING_11_FILE),
    ('competitions', competitions, COMPETITIONS_FILE),
    ('teams', teams, TEAMS_FILE),
    ('competition_team_player_mapping', ctpm, CTPM_FILE)
]:
    inventory.append({
        'table': name,
        'filepath': str(filepath),
        'rows': len(df),
        'columns': len(df.columns),
        'size_mb': round(filepath.stat().st_size / 1024 / 1024, 2),
        'null_total': df.isna().sum().sum(),
        'duplicate_rows': df.duplicated().sum(),
        'column_list': ', '.join(df.columns.tolist())
    })

inv_df = pd.DataFrame(inventory)
inv_df.to_csv(AUDIT_DIR / 'dataset_inventory.csv', index=False)

# ============================================================
# SAVE ENRICHED DATASETS
# ============================================================
print("\n  Saving enriched BBB to interim...")
bbb_enriched.to_csv(INTERIM_DIR / 'bbb_enriched.csv', index=False)
matches_enriched.to_csv(INTERIM_DIR / 'matches_enriched.csv', index=False)

# Save filtered datasets
ipl_bbb.to_csv(INTERIM_DIR / 'ipl_bbb.csv', index=False)
t20i_bbb.to_csv(INTERIM_DIR / 't20i_bbb.csv', index=False)

print(f"\n  IPL deliveries saved: {len(ipl_bbb):,}")
print(f"  T20I deliveries saved: {len(t20i_bbb):,}")

# ============================================================
# PRINT SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("PHASE 1 COMPLETE — DATA AUDIT SUMMARY")
print("=" * 70)
print(f"  Total deliveries analysed:  {len(bbb):,}")
print(f"  IPL deliveries:             {len(ipl_bbb):,}")
print(f"  T20I deliveries:            {len(t20i_bbb):,}")
print(f"  IPL matches:                {len(ipl_matches)}")
print(f"  T20I matches:               {len(t20i_matches)}")
print(f"  IPL competitions:           {len(ipl_comps)}")
print(f"  T20I competitions:          {len(t20i_comps)}")
print(f"  Quality issues found:       {len(quality_issues)}")
print(f"  Features documented:        {len(feat_df)}")
print(f"\nFiles saved:")
print(f"  {METADATA_DIR / 'data_dictionary.csv'}")
print(f"  {METADATA_DIR / 'feature_availability_matrix.csv'}")
print(f"  {METADATA_DIR / 'competitions_classified.csv'}")
print(f"  {AUDIT_DIR / 'dataset_inventory.csv'}")
print(f"  {AUDIT_DIR / 'data_quality_report.csv'}")
print(f"  {INTERIM_DIR / 'bbb_enriched.csv'}")
print(f"  {INTERIM_DIR / 'ipl_bbb.csv'}")
print(f"  {INTERIM_DIR / 't20i_bbb.csv'}")
print(f"\nPhase 1 completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

