"""
SupeRR Selector Season 2 — Rajasthan Royals IPL 2027 Auction Intelligence
Configuration and constants module
"""

import os
from pathlib import Path

# ============================================================
# ROOT PATHS
# ============================================================
ROOT_DIR = Path(r"d:\Priyan\EVENTS\hacathon\rr hackathon")
RESEARCH_DIR = ROOT_DIR / "SupeRR_Selector_Research"
SUBMISSION_DIR = ROOT_DIR / "SupeRR_Selector_Final_Submission"

# Data paths
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
INTERIM_DIR = RESEARCH_DIR / "data" / "interim"
PROCESSED_DIR = RESEARCH_DIR / "data" / "processed"
METADATA_DIR = RESEARCH_DIR / "data" / "metadata"
OUTPUTS_DIR = RESEARCH_DIR / "outputs"
LOGS_DIR = RESEARCH_DIR / "logs"

# Output sub-directories
AUDIT_DIR = OUTPUTS_DIR / "audit"
STATS_DIR = OUTPUTS_DIR / "statistics"
RANKINGS_DIR = OUTPUTS_DIR / "rankings"
FIGURES_DIR = OUTPUTS_DIR / "figures"

# ============================================================
# RAW DATA FILES
# ============================================================
BBB_FILE = RAW_DATA_DIR / "ball_by_ball.csv"
MATCHES_FILE = RAW_DATA_DIR / "matches.csv"
PLAYING_11_FILE = RAW_DATA_DIR / "playing_eleven.csv"
COMPETITIONS_FILE = RAW_DATA_DIR / "competitions.csv"
TEAMS_FILE = RAW_DATA_DIR / "teams.csv"
CTPM_FILE = RAW_DATA_DIR / "competition_team_player_mapping.csv"

# ============================================================
# COMPETITION FILTERS
# ============================================================
# IPL competition names contain 'Indian Premier League' or 'IPL'
IPL_KEYWORDS = ['Indian Premier League', 'IPL']
T20I_FORMAT = 'T20I'
IPL_FORMAT = 'T20'

# Minimum qualifying thresholds
MIN_BATTER_INNINGS = 10          # minimum innings to qualify as a batter
MIN_BOWLER_INNINGS = 10          # minimum innings to qualify as a bowler
MIN_BALLS_FACED = 50             # minimum balls faced for batter
MIN_BALLS_BOWLED = 60            # minimum balls bowled for bowler (10 overs)

# ============================================================
# INNINGS PHASES
# ============================================================
POWERPLAY_OVERS = range(1, 7)    # Overs 1-6
MIDDLE_OVERS = range(7, 16)      # Overs 7-15
DEATH_OVERS = range(16, 21)      # Overs 16-20

# ============================================================
# PRESSURE THRESHOLDS
# ============================================================
# Required Run Rate thresholds
RRR_HIGH = 10.0      # RRR >= 10 = high pressure for batting
RRR_EXTREME = 14.0   # RRR >= 14 = extreme pressure for batting
RRR_LOW = 7.0        # RRR <= 7 = low pressure for batting

# Economy pressure thresholds for bowling (defending)
# Target run rate (batting team needs X per over)
TARGET_HIGH = 9.0    # Target RR >= 9 = high pressure for bowling

# Match closeness (within N runs with M overs left)
CLOSE_RUNS_THRESHOLD = 20   # within 20 runs at death
CLOSE_OVERS_REMAINING = 4   # in last 4 overs

# Wickets in hand (batting pressure increases as wickets fall)
LOW_WICKETS = 3   # 3 or fewer wickets remaining = high pressure

# Wickets lost recently (last 3 balls)
RECENT_WICKETS_THRESHOLD = 2  # 2+ wickets in last 10 balls = collapse

# ============================================================
# PRESSURE CLASSIFICATION LABELS
# ============================================================
PRESSURE_LEVELS = {
    0: 'No Pressure',
    1: 'Low Pressure',
    2: 'Moderate Pressure',
    3: 'High Pressure',
    4: 'Extreme Pressure'
}

# ============================================================
# RELIABILITY MODEL WEIGHTS
# ============================================================
# Batting reliability weights (sum = 1.0)
BATTING_WEIGHTS = {
    'quality_score': 0.20,          # overall batting quality
    'consistency_score': 0.20,      # match-to-match consistency
    'pressure_perf_score': 0.25,    # performance under pressure
    'pressure_consistency': 0.15,   # consistency under pressure
    'boundary_score': 0.10,         # boundary conversion
    'strike_rotation_score': 0.05,  # dot ball avoidance / rotation
    'acceleration_score': 0.05,     # ability to accelerate
}

# Bowling reliability weights (sum = 1.0)
BOWLING_WEIGHTS = {
    'quality_score': 0.20,          # overall bowling quality
    'consistency_score': 0.20,      # match-to-match consistency
    'pressure_perf_score': 0.25,    # performance under pressure
    'pressure_consistency': 0.15,   # consistency under pressure
    'wicket_quality_score': 0.10,   # contextual wicket quality
    'dot_ball_score': 0.05,         # dot ball generation
    'economy_control_score': 0.05,  # economy rate control
}

# ============================================================
# BAYESIAN SHRINKAGE
# ============================================================
# Empirical Bayes shrinkage — prior based on population mean
SHRINKAGE_K = 15  # number of matches for half-weight to prior

# ============================================================
# BOOTSTRAP SETTINGS
# ============================================================
N_BOOTSTRAP = 1000
BOOTSTRAP_CI = 0.95

# ============================================================
# COLOURS (Rajasthan Royals theme)
# ============================================================
RR_PINK = '#E8336D'
RR_NAVY = '#254AA5'
RR_GOLD = '#FFD700'
RR_WHITE = '#FFFFFF'
RR_LIGHT_BLUE = '#7BC4E2'

