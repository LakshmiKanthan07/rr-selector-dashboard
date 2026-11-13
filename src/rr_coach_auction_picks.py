"""
SupeRR Selector Season 2 — Rajasthan Royals IPL 2027 Auction Intelligence
Component 5: Auction Candidate Intelligence Engine

Synthesizes all four quantitative pillars into the Combined Auction Fit Score (CAFS):
    CAFS = 0.40 * PRI + 0.30 * CPAS + 0.20 * SGF + 0.10 * VF

Segregates targets strictly into:
- Category A: Best Cricketing & Coaching Fits (Hypothetical / Pure Tactical)
- Category B: Realistic Auction Targets (Verified Auction Feasibility)
Generates role-specific target lists and data-driven scouting dossiers.
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
RANKINGS_DIR = OUTPUTS_DIR / "rankings"

# Known franchise retention locks for IPL cycles (Bumrah, Suryakumar Yadav, Klaasen, Tilak Varma)
# These represent Category A (Hypothetical/Benchmark Fits) unless released.
FRANCHISE_RETENTION_LOCKS = {
    "Jasprit Bumrah", "Suryakumar Yadav", "Heinrich Klaasen", "Tilak Varma",
    "Namboori Tilak Varma", "Ruturaj Gaikwad", "Virat Kohli", "Rohit Sharma",
    "Hardik Pandya", "Rashid Khan", "Shubman Gill", "Sanju Samson", "Yashasvi Jaiswal"
}

def determine_nationality(name):
    """Classify player nationality (Indian vs Overseas)."""
    overseas_names = {
        "Phil Salt", "Jos Buttler", "Heinrich Klaasen", "Tim David", "Tristan Stubbs",
        "Matheesha Pathirana", "Josh Hazlewood", "Mustafizur Rahman", "Jofra Archer",
        "Nathan Ellis", "Haris Rauf", "Trent Boult", "Sam Curran", "Mitchell Starc",
        "Travis Head", "Glenn Maxwell", "David Warner", "Nicholas Pooran", "Marcus Stoinis",
        "Liam Livingstone", "Andre Russell", "Sunil Narine", "Quinton de Kock", "Faf du Plessis",
        "Kagiso Rabada", "Anrich Nortje", "Lockie Ferguson", "Noor Ahmad", "Maheesh Theekshana",
        "Shaheen Afridi", "Tim Southee", "Aiden Markram", "Glenn Phillips", "Mitchell Marsh",
        "Daryl Mitchell", "Devon Conway", "Rachin Ravindra", "Wanindu Hasaranga", "Gerald Coetzee",
        "Fazalhaq Farooqi", "Naveen-ul-Haq", "Romario Shepherd", "Alzarri Joseph", "Spencer Johnson",
        "Lungi Ngidi", "Tabraiz Shamsi", "Moeen Ali", "Jonny Bairstow", "Harry Brook", "Will Jacks"
    }
    return "Overseas" if name in overseas_names else "Indian"

def run_auction_intelligence_engine():
    print("=" * 70)
    print("RUNNING AUCTION CANDIDATE INTELLIGENCE ENGINE (CAFS)")
    print("=" * 70)

    # 1. Load All Upstream Datasets
    cpas_df = pd.read_csv(COACHING_DIR / "rr_coach_persona_scores.csv")
    sgf_df = pd.read_csv(AUCTION_DIR / "rr_squad_gap_scores.csv")

    # Merge CPAS and SGF matching player_id AND role
    merged = pd.merge(
        cpas_df, 
        sgf_df[['player_id', 'role', 'primary_gap_targeted', 'sgf_score', 'versatility_factor']], 
        left_on=['player_id', 'primary_role'], 
        right_on=['player_id', 'role'], 
        how='inner'
    )

    # Rename reliability score to pri_score
    merged['pri_score'] = merged['reliability_pct'].round(2)
    merged['cpas_score'] = merged['cpas_score'].round(2)
    merged['sgf_score'] = merged['sgf_score'].round(2)
    merged['vf_score'] = merged['versatility_factor'].round(2)

    # 2. Compute Combined Auction Fit Score (CAFS)
    # CAFS = 0.40 * PRI + 0.30 * CPAS + 0.20 * SGF + 0.10 * VF
    merged['cafs_score'] = (
        0.40 * merged['pri_score'] +
        0.30 * merged['cpas_score'] +
        0.20 * merged['sgf_score'] +
        0.10 * merged['vf_score']
    ).round(2)

    # Add nationality
    merged['nationality'] = merged['player_name'].apply(determine_nationality)

    # Classify Target Category:
    # Category A: Pure Cricketing & Coaching Fits (includes retention locks)
    # Category B: Realistic Auction Targets (auction eligible / potential targets)
    merged['target_category'] = merged['player_name'].apply(
        lambda name: "Category A: Pure Benchmark Fit" if name in FRANCHISE_RETENTION_LOCKS else "Category B: Realistic Auction Target"
    )

    # Add Coaching & Tactical Rationale
    def build_rationale(row):
        role = row['primary_role']
        pname = row['player_name']
        gap = row['primary_gap_targeted']
        pri = row['pri_score']
        cpas = row['cpas_score']

        if role == 'Batter':
            if "GAP-01" in gap:
                return f"Elite powerplay pace attack intent (CPAS: {cpas}%). Directly fulfills Sangakkara's requirement for aggressive opening boundary generation alongside Yashasvi Jaiswal."
            else:
                return f"Ice-cold situational composure under pressure (PRI: {pri}%). Aligns with Dravid's high scoring floor and Rathour's technical discipline against hard lengths."
        else:
            if "GAP-03" in gap:
                return f"Disciplined death execution and dot-ball choke (CPAS: {cpas}%). Embodies Shane Bond's pace hostility and defensive wide-yorker accuracy at the death."
            else:
                return f"Attacking middle-overs spin weapon (PRI: {pri}%). High-threat wicket-taker who breaks partnerships and chokes run rates through overs 7-15."

    merged['coaching_alignment_rationale'] = merged.apply(build_rationale, axis=1)

    # Sort and rank
    merged = merged.sort_values(by='cafs_score', ascending=False).reset_index(drop=True)
    merged['cafs_overall_rank'] = merged.index + 1

    # 3. Segregate Category A vs Category B
    cat_a_fits = merged.sort_values(by='cafs_score', ascending=False).reset_index(drop=True)
    cat_b_targets = merged[merged['target_category'] == "Category B: Realistic Auction Target"].sort_values(by='cafs_score', ascending=False).reset_index(drop=True)

    cat_b_targets['realistic_auction_rank'] = cat_b_targets.index + 1

    # 4. Role-Specific Target Lists for Auction Table
    batting_targets = cat_b_targets[cat_b_targets['primary_role'] == 'Batter'].copy().reset_index(drop=True)
    batting_targets['role_rank'] = batting_targets.index + 1

    bowling_targets = cat_b_targets[cat_b_targets['primary_role'] == 'Bowler'].copy().reset_index(drop=True)
    bowling_targets['role_rank'] = bowling_targets.index + 1

    # All-Rounder Candidates (High versatility factor >= 60.0%)
    all_rounder_targets = cat_b_targets[cat_b_targets['vf_score'] >= 55.0].copy().reset_index(drop=True)
    all_rounder_targets['role_rank'] = all_rounder_targets.index + 1

    # 5. Save Datasets to outputs/auction and SupeRR_Selector_RR_2027_Final
    output_files = {
        'rr_best_player_fits.csv': cat_a_fits,
        'rr_realistic_auction_targets.csv': cat_b_targets,
        'rr_batting_targets.csv': batting_targets,
        'rr_bowling_targets.csv': bowling_targets,
        'rr_all_rounder_targets.csv': all_rounder_targets
    }

    for fname, df_out in output_files.items():
        p1 = AUCTION_DIR / fname
        p2 = FINAL_DIR / fname
        df_out.to_csv(p1, index=False)
        df_out.to_csv(p2, index=False)
        print(f"Generated: {fname} ({len(df_out)} targets)")

    print("Auction Candidate Intelligence Engine completed successfully.\n")

if __name__ == '__main__':
    run_auction_intelligence_engine()
