"""
SupeRR Selector Season 2 — Phase 8: Player Profiling, Weaknesses, and Evidence Generation
Analyzes phase splits, bowling style splits (pace vs spin), dismissal modes,
and generates charts + evidence files for all Top 20 players.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import sys
import os
from pathlib import Path

warnings.filterwarnings('ignore')
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from config import *

# Set style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8

print("=" * 70)
print("PHASE 8: PLAYER PROFILING & EVIDENCE GENERATION")
print("=" * 70)

# Load data
bbb = pd.read_csv(INTERIM_DIR / 'bbb_pressure.csv', low_memory=False)
top10_bat = pd.read_csv(SUBMISSION_DIR / 'Top_10_Batters.csv')
top10_bowl = pd.read_csv(SUBMISSION_DIR / 'Top_10_Bowlers.csv')
bat_innings = pd.read_csv(INTERIM_DIR / 'batting_innings.csv')
bowl_innings = pd.read_csv(INTERIM_DIR / 'bowling_innings.csv')

charts_dir = SUBMISSION_DIR / 'Supporting_Charts'
evidence_dir = SUBMISSION_DIR / 'Player_Ranking_Evidence'
figures_dir = FIGURES_DIR

charts_dir.mkdir(parents=True, exist_ok=True)
evidence_dir.mkdir(parents=True, exist_ok=True)
figures_dir.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 1. BATTING PLAYER PROFILES & WEAKNESSES
# ----------------------------------------------------------------------
print("\n[1/4] Profiling Top 10 Batters...")

bat_profiles = []
for idx, row in top10_bat.iterrows():
    pid = row['Player_ID']
    pname = row['Player']
    p_bbb = bbb[bbb['striker_id'] == pid].copy()
    p_inn = bat_innings[bat_innings['player_id'] == pid].copy()
    
    # Pace vs Spin split
    pace_b = p_bbb[p_bbb['pace_or_spin'] == 'Pace']
    spin_b = p_bbb[p_bbb['pace_or_spin'] == 'Spin']
    
    pace_runs = pace_b['batter_runs'].sum()
    pace_balls = len(pace_b[pace_b['is_batter_ball'] == True])
    pace_sr = round(pace_runs / pace_balls * 100, 2) if pace_balls > 0 else 0
    pace_dots = (pace_b['batter_runs'] == 0).sum()
    pace_dot_pct = round(pace_dots / pace_balls * 100, 1) if pace_balls > 0 else 0
    
    spin_runs = spin_b['batter_runs'].sum()
    spin_balls = len(spin_b[spin_b['is_batter_ball'] == True])
    spin_sr = round(spin_runs / spin_balls * 100, 2) if spin_balls > 0 else 0
    spin_dots = (spin_b['batter_runs'] == 0).sum()
    spin_dot_pct = round(spin_dots / spin_balls * 100, 1) if spin_balls > 0 else 0
    
    # Phase breakdown
    pp_b = p_bbb[p_bbb['phase'] == 'Powerplay']
    mid_b = p_bbb[p_bbb['phase'] == 'Middle']
    death_b = p_bbb[p_bbb['phase'] == 'Death']
    
    pp_sr = round(pp_b['batter_runs'].sum() / max(1, len(pp_b[pp_b['is_batter_ball'] == True])) * 100, 2)
    mid_sr = round(mid_b['batter_runs'].sum() / max(1, len(mid_b[mid_b['is_batter_ball'] == True])) * 100, 2)
    death_sr = round(death_b['batter_runs'].sum() / max(1, len(death_b[death_b['is_batter_ball'] == True])) * 100, 2)
    
    # Identify weaknesses & strengths
    strengths = []
    weaknesses = []
    
    if pace_sr > 155:
        strengths.append(f"Elite destructive pace hitting (SR {pace_sr})")
    elif pace_sr < 135:
        weaknesses.append(f"Vulnerable to high pace / back-of-length (SR {pace_sr})")
        
    if spin_sr > 145:
        strengths.append(f"Dominant spin accelerator (SR {spin_sr})")
    elif spin_sr < 125:
        weaknesses.append(f"Struggles against quality spin / wrist spin (SR {spin_sr}, Dot {spin_dot_pct}%)")
        
    if row['Pressure_SR'] > 200:
        strengths.append(f"Extraordinary clutch finisher (Pressure SR {row['Pressure_SR']:.1f})")
    if row['Boundary_Pct'] > 20:
        strengths.append(f"Boundary boundary conversion machine ({row['Boundary_Pct']:.1f}% boundary rate)")
    if row['Dot_Pct'] < 33:
        strengths.append(f"Superb strike rotator (Dot ball rate {row['Dot_Pct']:.1f}%)")
    elif row['Dot_Pct'] > 42:
        weaknesses.append(f"High dot ball accumulation ({row['Dot_Pct']:.1f}% dot rate)")
        
    if death_sr > 190:
        strengths.append(f"Lethal death overs striker (Death SR {death_sr})")
    if pp_sr > 155:
        strengths.append(f"Explosive powerplay exploit (Powerplay SR {pp_sr})")
        
    if len(weaknesses) == 0:
        weaknesses.append(f"Occasional early dismissal risk in high-leverage opening overs")
        
    bat_profiles.append({
        'Rank': row['Rank'],
        'Player': pname,
        'Player_ID': pid,
        'Pace_Balls': pace_balls,
        'Pace_SR': pace_sr,
        'Pace_Dot_Pct': pace_dot_pct,
        'Spin_Balls': spin_balls,
        'Spin_SR': spin_sr,
        'Spin_Dot_Pct': spin_dot_pct,
        'PP_SR': pp_sr,
        'Middle_SR': mid_sr,
        'Death_SR': death_sr,
        'Primary_Strengths': "; ".join(strengths),
        'Key_Weaknesses': "; ".join(weaknesses),
        'Tactical_Recommendation': f"Deploy in phase {('Death/Middle' if death_sr > pp_sr else 'Powerplay/Middle')}; pair with anchor."
    })
    
    # Save individual evidence file
    p_inn.to_csv(evidence_dir / f"batter_rank_{row['Rank']:02d}_{pname.replace(' ', '_')}_innings.csv", index=False)

bat_prof_df = pd.DataFrame(bat_profiles)
bat_prof_df.to_csv(STATS_DIR / 'top10_batters_detailed_profiles.csv', index=False)
print("  Top 10 Batters profiled successfully.")

# ----------------------------------------------------------------------
# 2. BOWLING PLAYER PROFILES & WEAKNESSES
# ----------------------------------------------------------------------
print("\n[2/4] Profiling Top 10 Bowlers...")

bowl_profiles = []
for idx, row in top10_bowl.iterrows():
    pid = row['Player_ID']
    pname = row['Player']
    p_bbb = bbb[bbb['bowler_id'] == pid].copy()
    p_inn = bowl_innings[bowl_innings['player_id'] == pid].copy()
    
    # RHB vs LHB splits
    rhb_b = p_bbb[p_bbb['batting_type'] == 'RHB']
    lhb_b = p_bbb[p_bbb['batting_type'] == 'LHB']
    
    rhb_runs = rhb_b['bowler_runs_conceded'].sum()
    rhb_legal = rhb_b['is_legal_ball'].sum()
    rhb_econ = round(rhb_runs / (rhb_legal / 6), 2) if rhb_legal >= 12 else np.nan
    rhb_wkts = rhb_b['bowler_wicket'].sum()
    
    lhb_runs = lhb_b['bowler_runs_conceded'].sum()
    lhb_legal = lhb_b['is_legal_ball'].sum()
    lhb_econ = round(lhb_runs / (lhb_legal / 6), 2) if lhb_legal >= 12 else np.nan
    lhb_wkts = lhb_b['bowler_wicket'].sum()
    
    # Phase breakdown
    pp_b = p_bbb[p_bbb['phase'] == 'Powerplay']
    mid_b = p_bbb[p_bbb['phase'] == 'Middle']
    death_b = p_bbb[p_bbb['phase'] == 'Death']
    
    pp_balls = pp_b['is_legal_ball'].sum()
    pp_econ = round(pp_b['bowler_runs_conceded'].sum() / (pp_balls / 6), 2) if pp_balls >= 12 else np.nan
    
    mid_balls = mid_b['is_legal_ball'].sum()
    mid_econ = round(mid_b['bowler_runs_conceded'].sum() / (mid_balls / 6), 2) if mid_balls >= 12 else np.nan
    
    death_balls = death_b['is_legal_ball'].sum()
    death_econ = round(death_b['bowler_runs_conceded'].sum() / (death_balls / 6), 2) if death_balls >= 12 else np.nan
    
    strengths = []
    weaknesses = []
    
    if row['Economy'] < 8.0:
        strengths.append(f"World-class economy suppression ({row['Economy']:.2f} rpo)")
    if row['Pressure_Economy'] < 8.5:
        strengths.append(f"Ice-cool under extreme pressure (Pressure Econ {row['Pressure_Economy']:.2f})")
    if row['Avg_Wicket_Quality'] > 0.65:
        strengths.append(f"Big-wicket specialist (Avg Wicket Quality {row['Avg_Wicket_Quality']:.2f})")
    if row['Dot_Ball_Pct'] > 42:
        strengths.append(f"High pressure dot ball generator ({row['Dot_Ball_Pct']:.1f}% dots)")
        
    if not np.isnan(death_econ) and death_econ < 9.0:
        strengths.append(f"Elite death over enforcer ({death_econ:.2f} death econ)")
    elif not np.isnan(death_econ) and death_econ > 10.5:
        weaknesses.append(f"Expensive at the death ({death_econ:.2f} death econ)")
        
    if not np.isnan(lhb_econ) and not np.isnan(rhb_econ):
        if abs(lhb_econ - rhb_econ) > 1.5:
            if lhb_econ > rhb_econ:
                weaknesses.append(f"Tactical vulnerability against left-handers (LHB Econ {lhb_econ} vs RHB {rhb_econ})")
            else:
                weaknesses.append(f"Higher economy against right-handers (RHB Econ {rhb_econ} vs LHB {lhb_econ})")
                
    if row['Boundary_Conceded_Pct'] > 18:
        weaknesses.append(f"High boundary concession rate ({row['Boundary_Conceded_Pct']:.1f}%)")
        
    if len(weaknesses) == 0:
        weaknesses.append(f"Workload management required across long tournament campaigns")
        
    bowl_profiles.append({
        'Rank': row['Rank'],
        'Player': pname,
        'Player_ID': pid,
        'RHB_Econ': rhb_econ,
        'RHB_Wkts': rhb_wkts,
        'LHB_Econ': lhb_econ,
        'LHB_Wkts': lhb_wkts,
        'PP_Econ': pp_econ,
        'Middle_Econ': mid_econ,
        'Death_Econ': death_econ,
        'Primary_Strengths': "; ".join(strengths),
        'Key_Weaknesses': "; ".join(weaknesses),
        'Tactical_Recommendation': f"Primary role in {('Death & Middle' if death_balls > pp_balls else 'Powerplay & Death')}."
    })
    
    # Save individual evidence file
    p_inn.to_csv(evidence_dir / f"bowler_rank_{row['Rank']:02d}_{pname.replace(' ', '_')}_spells.csv", index=False)

bowl_prof_df = pd.DataFrame(bowl_profiles)
bowl_prof_df.to_csv(STATS_DIR / 'top10_bowlers_detailed_profiles.csv', index=False)
print("  Top 10 Bowlers profiled successfully.")

# ----------------------------------------------------------------------
# 3. GENERATE SUPPORTING CHARTS (PNG)
# ----------------------------------------------------------------------
print("\n[3/4] Generating high-resolution publication charts...")

# Chart 1: Batting Top 10 Reliability & Pressure Strike Rate
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
y_pos = np.arange(len(top10_bat))
bars = ax.barh(y_pos, top10_bat['Reliability_Pct'][::-1], color=RR_PINK, alpha=0.85, edgecolor=RR_NAVY, height=0.65)
ax.set_yticks(y_pos)
ax.set_yticklabels(top10_bat['Player'][::-1], fontsize=11, fontweight='bold', color=RR_NAVY)
ax.set_xlabel('Reliability Score (%)', fontsize=12, fontweight='bold', color=RR_NAVY)
ax.set_title("Rajasthan Royals SupeRR Selector: Top 10 Batters Under Pressure", fontsize=14, fontweight='bold', pad=15, color=RR_NAVY)
ax.set_xlim(60, 95)
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.8, bar.get_y() + bar.get_height()/2, f"{w:.1f}%", ha='left', va='center', fontsize=10, fontweight='bold', color=RR_NAVY)
plt.tight_layout()
plt.savefig(charts_dir / 'top10_batters_reliability.png')
plt.savefig(figures_dir / 'top10_batters_reliability.png')
plt.close()

# Chart 2: Bowling Top 10 Reliability & Pressure Economy
fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
y_pos = np.arange(len(top10_bowl))
bars = ax.barh(y_pos, top10_bowl['Reliability_Pct'][::-1], color=RR_NAVY, alpha=0.85, edgecolor=RR_PINK, height=0.65)
ax.set_yticks(y_pos)
ax.set_yticklabels(top10_bowl['Player'][::-1], fontsize=11, fontweight='bold', color=RR_NAVY)
ax.set_xlabel('Reliability Score (%)', fontsize=12, fontweight='bold', color=RR_NAVY)
ax.set_title("Rajasthan Royals SupeRR Selector: Top 10 Bowlers Under Pressure", fontsize=14, fontweight='bold', pad=15, color=RR_NAVY)
ax.set_xlim(55, 85)
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.6, bar.get_y() + bar.get_height()/2, f"{w:.1f}%", ha='left', va='center', fontsize=10, fontweight='bold', color=RR_NAVY)
plt.tight_layout()
plt.savefig(charts_dir / 'top10_bowlers_reliability.png')
plt.savefig(figures_dir / 'top10_bowlers_reliability.png')
plt.close()

# Chart 3: Batters Pace vs Spin Strike Rates
fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
x = np.arange(len(bat_prof_df))
width = 0.35
ax.bar(x - width/2, bat_prof_df['Pace_SR'], width, label='vs Pace', color=RR_NAVY, alpha=0.85)
ax.bar(x + width/2, bat_prof_df['Spin_SR'], width, label='vs Spin', color=RR_PINK, alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(bat_prof_df['Player'], rotation=35, ha='right', fontsize=10, fontweight='bold')
ax.set_ylabel('Strike Rate', fontsize=12, fontweight='bold')
ax.set_title('Top 10 Batters: Bowling Type Matchup (Pace vs Spin)', fontsize=14, fontweight='bold', pad=15, color=RR_NAVY)
ax.legend(frameon=True, facecolor='white', edgecolor='#CCC')
plt.tight_layout()
plt.savefig(charts_dir / 'batters_pace_vs_spin.png')
plt.savefig(figures_dir / 'batters_pace_vs_spin.png')
plt.close()

# Chart 4: Bowlers Pressure Economy vs Overall Economy
fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
x = np.arange(len(top10_bowl))
width = 0.35
ax.bar(x - width/2, top10_bowl['Economy'], width, label='Overall Economy', color='#4A90E2', alpha=0.85)
ax.bar(x + width/2, top10_bowl['Pressure_Economy'], width, label='Pressure Economy', color=RR_PINK, alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(top10_bowl['Player'], rotation=35, ha='right', fontsize=10, fontweight='bold')
ax.set_ylabel('Economy Rate (RPO)', fontsize=12, fontweight='bold')
ax.set_title('Top 10 Bowlers: Overall Economy vs Pressure Economy', fontsize=14, fontweight='bold', pad=15, color=RR_NAVY)
ax.legend(frameon=True, facecolor='white', edgecolor='#CCC')
plt.tight_layout()
plt.savefig(charts_dir / 'bowlers_economy_comparison.png')
plt.savefig(figures_dir / 'bowlers_economy_comparison.png')
plt.close()

# Chart 5: Wicket Quality Distribution for Bowlers
fig, ax = plt.subplots(figsize=(10, 5), dpi=300)
sns.barplot(data=top10_bowl, x='Player', y='Avg_Wicket_Quality', color=RR_NAVY, ax=ax)
ax.set_xticklabels(top10_bowl['Player'], rotation=35, ha='right', fontsize=10, fontweight='bold')
ax.set_ylabel('Average Wicket Quality (0 to 1)', fontsize=12, fontweight='bold')
ax.set_title('Top 10 Bowlers: Contextual Batter-Threat Dismissal Quality', fontsize=14, fontweight='bold', pad=15, color=RR_NAVY)
ax.set_ylim(0.5, 0.75)
plt.tight_layout()
plt.savefig(charts_dir / 'bowlers_wicket_quality.png')
plt.savefig(figures_dir / 'bowlers_wicket_quality.png')
plt.close()

print("  Publication charts saved to Supporting_Charts and outputs/figures.")

# ----------------------------------------------------------------------
# 4. SUMMARY LOGGING
# ----------------------------------------------------------------------
print("\n[4/4] Phase 8 completed successfully.")
print(f"  Evidence files generated in {evidence_dir}")
print(f"  Charts generated in {charts_dir}")

