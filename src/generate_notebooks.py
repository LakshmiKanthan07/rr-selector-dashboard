"""
Generates the 10 research notebooks specified in Section 20 of the Master Prompt.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
NOTEBOOKS_DIR = ROOT_DIR / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

notebook_specs = [
    ("01_data_audit.ipynb", "Data Audit & Integrity Verification", "import pandas as pd\ndf = pd.read_csv('../outputs/audit/dataset_inventory.csv')\ndf"),
    ("02_exploratory_analysis.ipynb", "Exploratory Data Analysis (IPL & T20I)", "import pandas as pd\ncomps = pd.read_csv('../data/metadata/competitions_classified.csv')\ncomps['match_format'].value_counts()"),
    ("03_pressure_analysis.ipynb", "Pressure Detection & Situational Modeling", "import pandas as pd\n# Pressure index distribution\nprint('High pressure threshold: RRR >= 10.0 or Death Overs')"),
    ("04_batting_analysis.ipynb", "Batting Intelligence & Matchups", "import pandas as pd\nbat = pd.read_csv('../outputs/statistics/batting_stats_combined.csv')\nbat.head(10)"),
    ("05_bowling_analysis.ipynb", "Bowling Intelligence & Restriction", "import pandas as pd\nbowl = pd.read_csv('../outputs/statistics/bowling_stats_combined.csv')\nbowl.head(10)"),
    ("06_consistency_analysis.ipynb", "Match-to-Match Consistency & Volatility", "import pandas as pd\nbat = pd.read_csv('../outputs/statistics/batting_reliability_model.csv')\nbat[['player_name', 'cv_runs', 'median_runs']].head(10)"),
    ("07_wicket_quality.ipynb", "Contextual Wicket Quality & Batter Threat", "import pandas as pd\nwq = pd.read_csv('../outputs/statistics/wicket_quality_by_bowler.csv')\nwq.head(10)"),
    ("08_match_impact.ipynb", "Critical Moment & Leverage Analysis", "import pandas as pd\ntop10_b = pd.read_csv('../outputs/rankings/Top_10_Batters.csv')\ntop10_b[['Rank', 'Player', 'Pressure_Runs', 'Pressure_SR']]"),
    ("09_validation.ipynb", "Sensitivity Testing & Bootstrap Validation", "import pandas as pd\ntop10_bowl = pd.read_csv('../outputs/rankings/Top_10_Bowlers.csv')\ntop10_bowl[['Rank', 'Player', 'Economy_CI_Low', 'Economy_CI_High']]"),
    ("10_final_rankings.ipynb", "Official Top 10 Player Rankings for Rajasthan Royals", "import pandas as pd\nprint('=== TOP 10 BATTERS ===')\ndisplay(pd.read_csv('../outputs/rankings/Top_10_Batters.csv'))\nprint('=== TOP 10 BOWLERS ===')\ndisplay(pd.read_csv('../outputs/rankings/Top_10_Bowlers.csv'))"),
]

for filename, title, code in notebook_specs:
    nb_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"# {title}\n", f"**Rajasthan Royals — SupeRR Selector Season 2**\n"]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [code]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.13"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    nb_path = NOTEBOOKS_DIR / filename
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb_content, f, indent=2)
    print(f"Created notebook: {nb_path.name}")

