"""
SupeRR Selector Season 2 — Rajasthan Royals IPL 2027 Auction Intelligence
Component 1: Historical RR Franchise Intelligence (2022–2026)

Reconstructs Rajasthan Royals (team_id == 3) franchise history across 77 matches:
- 61 playing XI players + impact player analysis
- Player profiles by phase, bowling type, pressure
- Multi-dimensional tactical archetypes
- Season-wise tactical evolution (2022–2026)
- Coaching tenure comparison (Sangakkara era vs Dravid/Bond era)
"""

import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parent))
from config import (
    ROOT_DIR, RESEARCH_DIR, RAW_DATA_DIR, INTERIM_DIR,
    OUTPUTS_DIR, SUBMISSION_DIR
)

HISTORICAL_DIR = OUTPUTS_DIR / "historical_rr"
HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
FINAL_DIR = ROOT_DIR / "SupeRR_Selector_RR_2027_Final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)

def run_rr_franchise_history():
    print("=" * 70)
    print("RUNNING RR FRANCHISE HISTORICAL INTELLIGENCE (2022-2026)")
    print("=" * 70)

    # 1. Load Data
    bbb_path = INTERIM_DIR / "bbb_pressure.csv"
    if not bbb_path.exists():
        raise FileNotFoundError(f"Missing {bbb_path}. Run phase2_5_analysis.py first.")
    
    print("Loading ball-by-ball and match metadata...")
    df_bbb = pd.read_csv(bbb_path, low_memory=False)
    df_matches = pd.read_csv(RAW_DATA_DIR / "matches.csv")
    df_pe = pd.read_csv(RAW_DATA_DIR / "playing_eleven.csv")
    df_comp = pd.read_csv(RAW_DATA_DIR / "competitions.csv")

    # Map comp_id to season
    comp_season_map = {
        1358: 2022,
        1715: 2023,
        2193: 2024,
        2725: 2025,
        3298: 2026
    }
    df_bbb['season'] = df_bbb['comp_id'].map(comp_season_map)
    df_matches['season'] = df_matches['comp_id'].map(comp_season_map)

    # 2. Filter RR Matches (team_id == 3)
    rr_matches = df_matches[(df_matches['home_team_id'] == 3) | (df_matches['away_team_id'] == 3)].copy()
    rr_match_ids = set(rr_matches['match_id'])
    print(f"Total RR Matches Identified: {len(rr_matches)} across 5 seasons (2022-2026).")

    # Reconstruct dismissals set
    dismissed_tuples = set()
    for _, row in df_bbb.iterrows():
        if pd.notna(row['dismissed_player_id']) and row['dismissed_player_id'] not in ('', 'nan', None):
            try:
                pid = int(float(row['dismissed_player_id']))
                dismissed_tuples.add((int(row['match_id']), int(row['innings']), pid))
            except (ValueError, TypeError):
                pass

    # 3. Analyze Playing XI and Impact Players
    rr_pe = df_pe[df_pe['team_id'] == 3].copy()
    unique_rr_players = rr_pe['player_id'].nunique()
    print(f"Unique RR players in playing XI / impact roster: {unique_rr_players}")

    # Player names lookup
    name_lookup = {}
    for _, row in df_bbb.iterrows():
        if pd.notna(row['striker_name']):
            name_lookup[row['striker_id']] = row['striker_name']
        if pd.notna(row['bowler_name']):
            name_lookup[row['bowler_id']] = row['bowler_name']

    # 4. RR Batting Intelligence
    rr_bat_balls = df_bbb[(df_bbb['match_id'].isin(rr_match_ids)) & (df_bbb['batting_team_id'] == 3)].copy()
    
    bat_profiles = []
    for pid, group in rr_bat_balls.groupby('striker_id'):
        pname = name_lookup.get(pid, f"Player_{pid}")
        matches_played = group['match_id'].nunique()
        innings_batted = group.groupby(['match_id', 'innings']).ngroups
        balls_faced = (group['is_batter_ball'] == 1).sum()
        runs = group['batter_runs'].sum()
        fours = (group['is_four_bool'] == 1).sum()
        sixes = (group['is_six_bool'] == 1).sum()
        dots = ((group['is_batter_ball'] == 1) & (group['batter_runs'] == 0)).sum()
        
        # Calculate dismissals
        dismissals = sum(1 for (m, inn) in group[['match_id', 'innings']].drop_duplicates().values 
                         if (m, inn, pid) in dismissed_tuples)
        
        avg = round(runs / max(1, dismissals), 2) if dismissals > 0 else round(float(runs), 2)
        sr = round((runs / balls_faced) * 100, 2) if balls_faced > 0 else 0.0
        boundary_pct = round(((fours * 4 + sixes * 6) / max(1, runs)) * 100, 2)
        dot_pct = round((dots / max(1, balls_faced)) * 100, 2)

        # Phase breakdowns
        pp = group[group['phase'] == 'powerplay']
        mid = group[group['phase'] == 'middle']
        dth = group[group['phase'] == 'death']

        pp_runs = pp['batter_runs'].sum()
        pp_balls = (pp['is_batter_ball'] == 1).sum()
        pp_sr = round((pp_runs / pp_balls) * 100, 2) if pp_balls > 0 else 0.0

        mid_runs = mid['batter_runs'].sum()
        mid_balls = (mid['is_batter_ball'] == 1).sum()
        mid_sr = round((mid_runs / mid_balls) * 100, 2) if mid_balls > 0 else 0.0

        dth_runs = dth['batter_runs'].sum()
        dth_balls = (dth['is_batter_ball'] == 1).sum()
        dth_sr = round((dth_runs / dth_balls) * 100, 2) if dth_balls > 0 else 0.0

        # Pace vs Spin
        pace = group[group['pace_or_spin'] == 'pace']
        spin = group[group['pace_or_spin'] == 'spin']

        pace_runs = pace['batter_runs'].sum()
        pace_balls = (pace['is_batter_ball'] == 1).sum()
        pace_sr = round((pace_runs / pace_balls) * 100, 2) if pace_balls > 0 else 0.0

        spin_runs = spin['batter_runs'].sum()
        spin_balls = (spin['is_batter_ball'] == 1).sum()
        spin_sr = round((spin_runs / spin_balls) * 100, 2) if spin_balls > 0 else 0.0

        # Pressure performance
        press = group[group['is_high_pressure_batting'] == 1]
        press_runs = press['batter_runs'].sum()
        press_balls = (press['is_batter_ball'] == 1).sum()
        press_sr = round((press_runs / press_balls) * 100, 2) if press_balls > 0 else 0.0

        # Archetype rule
        if dth_balls >= 25 and dth_sr >= 165:
            archetype = "Death Finisher"
        elif pp_balls >= 40 and pp_sr >= 140:
            archetype = "Powerplay Demolisher"
        elif spin_balls >= 30 and spin_sr >= 140:
            archetype = "Spin Basher"
        elif pace_balls >= 40 and pace_sr >= 145:
            archetype = "Pace Enforcer"
        elif balls_faced >= 60 and dot_pct <= 36.0 and avg >= 30.0:
            archetype = "Anchor / Stabilizer"
        else:
            archetype = "Versatile Middle-Order"

        bat_profiles.append({
            'player_id': pid,
            'player_name': pname,
            'role_primary': 'Batter',
            'matches_for_rr': matches_played,
            'innings': innings_batted,
            'runs': runs,
            'balls_faced': balls_faced,
            'dismissals': dismissals,
            'batting_average': avg,
            'strike_rate': sr,
            'boundary_pct': boundary_pct,
            'dot_pct': dot_pct,
            'fours': fours,
            'sixes': sixes,
            'pp_balls': pp_balls,
            'pp_sr': pp_sr,
            'middle_balls': mid_balls,
            'middle_sr': mid_sr,
            'death_balls': dth_balls,
            'death_sr': dth_sr,
            'pace_sr': pace_sr,
            'spin_sr': spin_sr,
            'pressure_sr': press_sr,
            'tactical_archetype': archetype
        })

    df_bat_profiles = pd.DataFrame(bat_profiles)

    # 5. RR Bowling Intelligence
    rr_bowl_balls = df_bbb[(df_bbb['match_id'].isin(rr_match_ids)) & (df_bbb['bowling_team_id'] == 3)].copy()

    bowl_profiles = []
    for pid, group in rr_bowl_balls.groupby('bowler_id'):
        pname = name_lookup.get(pid, f"Player_{pid}")
        matches_played = group['match_id'].nunique()
        innings_bowled = group.groupby(['match_id', 'innings']).ngroups
        balls_bowled = (group['is_legal_ball'] == 1).sum()
        runs_conceded = group['bowler_runs_conceded'].sum()
        wickets = group['bowler_wicket'].sum()
        dots = ((group['is_legal_ball'] == 1) & (group['bowler_runs_conceded'] == 0)).sum()

        econ = round((runs_conceded / max(1, balls_bowled)) * 6.0, 2)
        sr = round(balls_bowled / max(1, wickets), 2) if wickets > 0 else 999.0
        avg = round(runs_conceded / max(1, wickets), 2) if wickets > 0 else 999.0
        dot_pct = round((dots / max(1, balls_bowled)) * 100, 2)

        # Phase breakdowns
        pp = group[group['phase'] == 'powerplay']
        mid = group[group['phase'] == 'middle']
        dth = group[group['phase'] == 'death']

        pp_balls = (pp['is_legal_ball'] == 1).sum()
        pp_runs = pp['bowler_runs_conceded'].sum()
        pp_wkts = pp['bowler_wicket'].sum()
        pp_econ = round((pp_runs / max(1, pp_balls)) * 6.0, 2) if pp_balls > 0 else 0.0

        mid_balls = (mid['is_legal_ball'] == 1).sum()
        mid_runs = mid['bowler_runs_conceded'].sum()
        mid_wkts = mid['bowler_wicket'].sum()
        mid_econ = round((mid_runs / max(1, mid_balls)) * 6.0, 2) if mid_balls > 0 else 0.0

        dth_balls = (dth['is_legal_ball'] == 1).sum()
        dth_runs = dth['bowler_runs_conceded'].sum()
        dth_wkts = dth['bowler_wicket'].sum()
        dth_econ = round((dth_runs / max(1, dth_balls)) * 6.0, 2) if dth_balls > 0 else 0.0

        # Style & Pressure
        bowl_style = group['pace_or_spin'].iloc[0] if 'pace_or_spin' in group.columns else 'pace'
        press = group[group['is_high_pressure_bowling'] == 1]
        press_balls = (press['is_legal_ball'] == 1).sum()
        press_runs = press['bowler_runs_conceded'].sum()
        press_wkts = press['bowler_wicket'].sum()
        press_econ = round((press_runs / max(1, press_balls)) * 6.0, 2) if press_balls > 0 else 0.0

        # Archetype rule
        if dth_balls >= 30 and dth_econ <= 9.6:
            archetype = "Death Yorker Specialist"
        elif pp_balls >= 40 and pp_econ <= 7.6:
            archetype = "Powerplay Swing Enforcer"
        elif bowl_style == 'spin' and wickets >= 8:
            archetype = "Wrist-Spin Magician / Attacking Spinner"
        elif mid_balls >= 40 and mid_econ <= 7.8:
            archetype = "Middle-Overs Enforcer"
        else:
            archetype = "All-Phase Seam / Utility"

        bowl_profiles.append({
            'player_id': pid,
            'player_name': pname,
            'role_primary': 'Bowler',
            'matches_for_rr': matches_played,
            'innings': innings_bowled,
            'balls_bowled': balls_bowled,
            'runs_conceded': runs_conceded,
            'wickets': wickets,
            'bowling_average': avg,
            'economy': econ,
            'bowling_sr': sr,
            'dot_pct': dot_pct,
            'pp_balls': pp_balls,
            'pp_econ': pp_econ,
            'pp_wkts': pp_wkts,
            'middle_balls': mid_balls,
            'middle_econ': mid_econ,
            'middle_wkts': mid_wkts,
            'death_balls': dth_balls,
            'death_econ': dth_econ,
            'death_wkts': dth_wkts,
            'pressure_econ': press_econ,
            'pressure_wkts': press_wkts,
            'tactical_archetype': archetype
        })

    df_bowl_profiles = pd.DataFrame(bowl_profiles)

    # Combine profiles for full RR roster
    all_rr_profiles = pd.concat([
        df_bat_profiles[['player_id', 'player_name', 'role_primary', 'matches_for_rr', 'tactical_archetype', 'runs', 'strike_rate', 'batting_average']],
        df_bowl_profiles[['player_id', 'player_name', 'role_primary', 'matches_for_rr', 'tactical_archetype', 'wickets', 'economy', 'bowling_average']]
    ], ignore_index=True)

    # 6. Season Evolution (2022-2026)
    season_stats = []
    for season in [2022, 2023, 2024, 2025, 2026]:
        s_matches = rr_matches[rr_matches['season'] == season]
        m_played = len(s_matches)
        m_won = (s_matches['win_team_id'] == 3).sum()
        win_pct = round((m_won / max(1, m_played)) * 100, 2)

        s_bat = rr_bat_balls[rr_bat_balls['season'] == season]
        bat_runs = s_bat['batter_runs'].sum()
        bat_balls = (s_bat['is_batter_ball'] == 1).sum()
        bat_sr = round((bat_runs / max(1, bat_balls)) * 100, 2)
        bat_boundary_pct = round((((s_bat['is_four_bool'] == 1).sum() * 4 + (s_bat['is_six_bool'] == 1).sum() * 6) / max(1, bat_runs)) * 100, 2)
        bat_dot_pct = round((((s_bat['is_batter_ball'] == 1) & (s_bat['batter_runs'] == 0)).sum() / max(1, bat_balls)) * 100, 2)

        # Phase bat SR
        pp_b = s_bat[s_bat['phase'] == 'powerplay']
        pp_sr = round((pp_b['batter_runs'].sum() / max(1, (pp_b['is_batter_ball'] == 1).sum())) * 100, 2)
        mid_b = s_bat[s_bat['phase'] == 'middle']
        mid_sr = round((mid_b['batter_runs'].sum() / max(1, (mid_b['is_batter_ball'] == 1).sum())) * 100, 2)
        dth_b = s_bat[s_bat['phase'] == 'death']
        dth_sr = round((dth_b['batter_runs'].sum() / max(1, (dth_b['is_batter_ball'] == 1).sum())) * 100, 2)

        s_bowl = rr_bowl_balls[rr_bowl_balls['season'] == season]
        bowl_runs = s_bowl['bowler_runs_conceded'].sum()
        bowl_balls = (s_bowl['is_legal_ball'] == 1).sum()
        bowl_wkts = s_bowl['bowler_wicket'].sum()
        bowl_econ = round((bowl_runs / max(1, bowl_balls)) * 6.0, 2)
        bowl_dot_pct = round((((s_bowl['is_legal_ball'] == 1) & (s_bowl['bowler_runs_conceded'] == 0)).sum() / max(1, bowl_balls)) * 100, 2)

        # Phase bowl econ
        pp_w = s_bowl[s_bowl['phase'] == 'powerplay']
        pp_econ = round((pp_w['bowler_runs_conceded'].sum() / max(1, (pp_w['is_legal_ball'] == 1).sum())) * 6.0, 2)
        mid_w = s_bowl[s_bowl['phase'] == 'middle']
        mid_econ = round((mid_w['bowler_runs_conceded'].sum() / max(1, (mid_w['is_legal_ball'] == 1).sum())) * 6.0, 2)
        dth_w = s_bowl[s_bowl['phase'] == 'death']
        dth_econ = round((dth_w['bowler_runs_conceded'].sum() / max(1, (dth_w['is_legal_ball'] == 1).sum())) * 6.0, 2)

        # Head coach / regime
        if season <= 2024:
            regime = "Kumar Sangakkara (Director & Lead Strategist)"
        else:
            regime = "Rahul Dravid (Head Coach) + Shane Bond (Bowling Coach)"

        season_stats.append({
            'season': season,
            'regime': regime,
            'matches_played': m_played,
            'matches_won': m_won,
            'win_rate_pct': win_pct,
            'batting_sr': bat_sr,
            'batting_boundary_pct': bat_boundary_pct,
            'batting_dot_pct': bat_dot_pct,
            'pp_batting_sr': pp_sr,
            'middle_batting_sr': mid_sr,
            'death_batting_sr': dth_sr,
            'bowling_economy': bowl_econ,
            'bowling_wickets': bowl_wkts,
            'bowling_dot_pct': bowl_dot_pct,
            'pp_bowling_econ': pp_econ,
            'middle_bowling_econ': mid_econ,
            'death_bowling_econ': dth_econ
        })

    df_season_evo = pd.DataFrame(season_stats)

    # 7. Coaching Tenure Comparison
    tenure_stats = []
    # Era 1: Sangakkara Era (2022-2024, 47 matches)
    # Era 2: Dravid / Bond Era (2025-2026, 30 matches)
    for era_name, seasons, leadership in [
        ("Sangakkara Director Era", [2022, 2023, 2024], "Kumar Sangakkara (Director of Cricket)"),
        ("Dravid & Bond Era", [2025, 2026], "Rahul Dravid (Head Coach) & Shane Bond (Bowling Coach)")
    ]:
        e_matches = rr_matches[rr_matches['season'].isin(seasons)]
        m_played = len(e_matches)
        m_won = (e_matches['win_team_id'] == 3).sum()
        win_pct = round((m_won / max(1, m_played)) * 100, 2)

        e_bat = rr_bat_balls[rr_bat_balls['season'].isin(seasons)]
        bat_runs = e_bat['batter_runs'].sum()
        bat_balls = (e_bat['is_batter_ball'] == 1).sum()
        bat_sr = round((bat_runs / max(1, bat_balls)) * 100, 2)
        bat_boundary_pct = round((((e_bat['is_four_bool'] == 1).sum() * 4 + (e_bat['is_six_bool'] == 1).sum() * 6) / max(1, bat_runs)) * 100, 2)
        bat_dot_pct = round((((e_bat['is_batter_ball'] == 1) & (e_bat['batter_runs'] == 0)).sum() / max(1, bat_balls)) * 100, 2)

        e_bowl = rr_bowl_balls[rr_bowl_balls['season'].isin(seasons)]
        bowl_runs = e_bowl['bowler_runs_conceded'].sum()
        bowl_balls = (e_bowl['is_legal_ball'] == 1).sum()
        bowl_wkts = e_bowl['bowler_wicket'].sum()
        bowl_econ = round((bowl_runs / max(1, bowl_balls)) * 6.0, 2)
        bowl_dot_pct = round((((e_bowl['is_legal_ball'] == 1) & (e_bowl['bowler_runs_conceded'] == 0)).sum() / max(1, bowl_balls)) * 100, 2)

        # Death metrics
        dth_bat = e_bat[e_bat['phase'] == 'death']
        dth_sr = round((dth_bat['batter_runs'].sum() / max(1, (dth_bat['is_batter_ball'] == 1).sum())) * 100, 2)
        dth_bowl = e_bowl[e_bowl['phase'] == 'death']
        dth_econ = round((dth_bowl['bowler_runs_conceded'].sum() / max(1, (dth_bowl['is_legal_ball'] == 1).sum())) * 6.0, 2)

        tenure_stats.append({
            'era_name': era_name,
            'seasons': f"{min(seasons)}-{max(seasons)}",
            'key_leadership': leadership,
            'matches_played': m_played,
            'matches_won': m_won,
            'win_rate_pct': win_pct,
            'batting_sr': bat_sr,
            'batting_boundary_pct': bat_boundary_pct,
            'batting_dot_pct': bat_dot_pct,
            'death_batting_sr': dth_sr,
            'bowling_economy': bowl_econ,
            'bowling_dot_pct': bowl_dot_pct,
            'death_bowling_econ': dth_econ,
            'strategic_hallmark': "Boundary intent & aggressive matchup targeting" if "Sangakkara" in era_name else "Situational composure, death discipline & domestic core stability"
        })

    df_tenure = pd.DataFrame(tenure_stats)

    # 8. Save CSV Outputs to outputs/historical_rr/ and SupeRR_Selector_RR_2027_Final/
    outputs = {
        'rr_historical_player_profiles.csv': all_rr_profiles,
        'rr_player_archetypes.csv': pd.concat([
            df_bat_profiles[['player_id', 'player_name', 'role_primary', 'tactical_archetype', 'strike_rate', 'boundary_pct', 'dot_pct']],
            df_bowl_profiles[['player_id', 'player_name', 'role_primary', 'tactical_archetype', 'economy', 'bowling_sr', 'dot_pct']]
        ], ignore_index=True),
        'rr_season_evolution.csv': df_season_evo,
        'rr_batting_identity.csv': df_bat_profiles.sort_values(by='runs', ascending=False),
        'rr_bowling_identity.csv': df_bowl_profiles.sort_values(by='wickets', ascending=False),
        'rr_coaching_tenure_comparison.csv': df_tenure
    }

    for fname, df_out in outputs.items():
        p1 = HISTORICAL_DIR / fname
        p2 = FINAL_DIR / fname
        df_out.to_csv(p1, index=False)
        df_out.to_csv(p2, index=False)
        print(f"Generated: {fname} ({len(df_out)} rows)")

    print("Historical RR Franchise Intelligence completed successfully.\n")

if __name__ == '__main__':
    run_rr_franchise_history()

