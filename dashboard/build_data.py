"""Builds dashboard_data.json for the single-page dashboard strictly from the supplied/derived CSVs.
Nothing in the dashboard is hand-typed: every number comes from here."""
import json, math
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "SupeRR_Selector_RR_2027_Final"
RES = ROOT / "SupeRR_Selector_Research"
RAW = ROOT / "data" / "raw"

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (float, np.floating)):
        return None if (math.isnan(o) or math.isinf(o)) else round(float(o), 4)
    return o

def recs(df): return clean(df.astype(object).where(df.notna(), None).to_dict("records"))

top_b = pd.read_csv(FINAL / "Top_10_Batters.csv")
top_w = pd.read_csv(FINAL / "Top_10_Bowlers.csv")
bat = pd.read_csv(RES / "outputs/statistics/batting_reliability_model.csv")
bow = pd.read_csv(RES / "outputs/statistics/bowling_reliability_model.csv")

BW = {"quality_score_shrunk": .20, "consistency_score_shrunk": .20, "pressure_perf_score": .25,
      "pressure_consistency": .15, "boundary_score": .10, "strike_rotation_score": .05, "acceleration_score": .05}
OW = {"quality_score_shrunk": .20, "consistency_score_shrunk": .20, "pressure_perf_score": .25,
      "pressure_consistency": .15, "wicket_quality_score": .10, "dot_ball_score": .05, "economy_control_score": .05}

def robustness(df, W, score_col, n=2000, seed=7):
    """Share of random weight perturbations (Dirichlet around official weights) in which a player stays in the Top 10."""
    rng = np.random.default_rng(seed)
    cols = list(W); base = np.array([W[c] for c in cols]); X = df[cols].fillna(df[cols].mean()).values
    hits = np.zeros(len(df))
    for _ in range(n):
        w = rng.dirichlet(base * 40)
        s = X @ w
        hits[np.argsort(-s)[:10]] += 1
    return dict(zip(df["player_id"], (hits / n * 100).round(1)))

def check_default(df, W, score_col):
    s = df[list(W)].fillna(0).values @ np.array(list(W.values()))
    assert np.abs(s - df[score_col].values).max() < 1e-3, "component weights do not reproduce official score"

check_default(bat, BW, "batting_reliability_score"); check_default(bow, OW, "bowling_reliability_score")
rb_b = robustness(bat, BW, "batting_reliability_score"); rb_w = robustness(bow, OW, "bowling_reliability_score")

def pool(df, W, kind):
    keep = ["player_id", "player_name", "dataset", "sample_reliability"] + list(W)
    extra = ["innings", "total_runs", "strike_rate", "pressure_sr", "pressure_innings_count", "boundary_pct", "dot_pct"] if kind == "bat" else ["matches", "total_wickets", "economy", "pressure_econ", "pressure_match_count", "pressure_wickets", "death_econ", "dot_pct"]
    out = df[keep + extra].copy()
    out["official_rank"] = df["batting_rank" if kind == "bat" else "bowling_rank"]
    return recs(out)

# Evidence per player
EV = FINAL / "Player_Ranking_Evidence"
ev = {}
for f in sorted(EV.glob("batter_rank_*")):
    d = pd.read_csv(f).sort_values("match_date")
    pid = int(d.player_id.iloc[0])
    ev[pid] = [[r.match_date, int(r.runs), int(r.balls), int(r.pressure_balls), int(r.pressure_runs), bool(r.is_ipl)] for r in d.itertuples()]
for f in sorted(EV.glob("bowler_rank_*")):
    d = pd.read_csv(f).sort_values("match_date")
    pid = int(d.player_id.iloc[0])
    ev[pid] = [[r.match_date, int(r.legal_balls), int(r.runs_conceded), int(r.wickets), int(r.pressure_balls), int(r.pressure_runs), int(r.pressure_wickets), bool(r.is_ipl)] for r in d.itertuples()]

def top_block(top, kind):
    out = []
    for r in top.itertuples(index=False):
        d = r._asdict()
        out.append(clean({k.lower(): v for k, v in d.items()}))
    return out

pb = pd.read_csv(RES / "data/interim/bbb_pressure.csv", low_memory=False,
                 usecols=["phase", "batting_pressure_class", "bowling_pressure_index", "is_high_pressure_batting", "innings"])
cls = pb.batting_pressure_class.value_counts(normalize=True).sort_index() * 100
bcls = pd.cut(pb.bowling_pressure_index, [-1, .10, .30, .50, .70, 2], right=False, labels=[0, 1, 2, 3, 4]).astype(int)
clsb = bcls.value_counts(normalize=True).sort_index() * 100
phase_hp = (pb.groupby("phase").is_high_pressure_batting.mean() * 100).round(1).to_dict()
bbb_n = len(pb)

matches = pd.read_csv(RAW / "matches.csv")
rr_m = matches[(matches.home_team_id == 3) | (matches.away_team_id == 3)]
n_matches = len(matches)
# RR record by listed result win_team_id==3 (IPL only in the pack)
rr_n, rr_w = len(rr_m), int((rr_m.win_team_id == 3).sum())

season = pd.read_csv(FINAL / "rr_season_evolution.csv")[["season", "regime", "matches_played", "matches_won", "win_rate_pct", "batting_sr", "batting_boundary_pct", "batting_dot_pct", "bowling_economy", "bowling_wickets", "bowling_dot_pct"]]
tenure = pd.read_csv(FINAL / "rr_coaching_tenure_comparison.csv")[["era_name", "seasons", "key_leadership", "matches_played", "matches_won", "win_rate_pct", "batting_sr", "batting_boundary_pct", "batting_dot_pct", "bowling_economy", "bowling_dot_pct", "strategic_hallmark"]]
rr_bat = pd.read_csv(FINAL / "rr_batting_identity.csv")[["player_name", "matches_for_rr", "runs", "batting_average", "strike_rate", "boundary_pct", "dot_pct", "tactical_archetype"]].head(10)
rr_bowl = pd.read_csv(FINAL / "rr_bowling_identity.csv")[["player_name", "matches_for_rr", "wickets", "economy", "bowling_average", "dot_pct", "tactical_archetype"]].head(10)

targets = pd.read_csv(FINAL / "rr_best_player_fits.csv")
real = pd.read_csv(FINAL / "rr_realistic_auction_targets.csv")[["player_id", "primary_role", "realistic_auction_rank"]]
targets = targets.merge(real, on=["player_id", "primary_role"], how="left")
targets["uid"] = targets.player_id.astype(str) + "-" + targets.primary_role
# Source file tags every bowler to GAP-03 regardless of type; assign by bowling type instead (pace -> GAP-03, spin -> GAP-04).
ps = bow[["player_id", "pace_or_spin"]].drop_duplicates("player_id")
targets = targets.merge(ps, on="player_id", how="left")
bm = (targets.primary_role == "Bowler") & targets.pace_or_spin.notna()
targets.loc[bm, "primary_gap_targeted"] = np.where(targets.loc[bm, "pace_or_spin"] == "Spin", "GAP-04 (Attacking Spin Choke)", "GAP-03 (High-Pace / Death Seam)")
keep = ["uid", "player_id", "player_name", "primary_role", "nationality", "primary_gap_targeted", "dci_score", "smi_score", "bdi_score", "rdi_score", "tfi_score",
        "cpas_score", "pri_score", "sgf_score", "vf_score", "cafs_score", "official_pri_rank", "cafs_overall_rank", "realistic_auction_rank", "target_category", "coaching_alignment_rationale"]
import sys
sys.path.insert(0, str(RES / "src"))
from feasibility_filter import build_master
MASTER = build_master().drop_duplicates("player_name").set_index("player_name")
for col, dflt in (("status", "G"), ("release_tier", "n/a"), ("team_2026", "")):
    targets[col] = targets.player_name.map(MASTER[col]).fillna(dflt)
keep += ["status", "release_tier", "team_2026", "rr_feasible", "rr_fail_reason"]
targets = targets[keep]
targets["rr_feasible"] = targets.rr_feasible.fillna(True).astype(bool)
targets["realistic"] = targets.realistic_auction_rank.notna() & targets.status.isin(["A", "B"]) & targets.rr_feasible

# ---- nationality from data: national team seen in T20I series (India => Indian, other => Overseas, IPL-only => Indian assumed) ----
_m = pd.read_csv(RAW / "competition_team_player_mapping.csv")
_c = pd.read_csv(RAW / "competitions.csv")
_t20i = _m.merge(_c[_c.match_format == "T20I"][["comp_id"]], on="comp_id")
def _nat(g):
    teams = set(g.team_name)
    return "Indian" if "India" in teams else "Overseas"
_natmap = _t20i.groupby("player_id").apply(_nat, include_groups=False).to_dict()
_old = targets.nationality.copy()
targets["nationality"] = targets.player_id.map(_natmap).fillna(_old)  # no T20I record in pack: keep the pipeline's name-list label
_ov = targets.player_name.map(MASTER["overseas"])
targets.loc[_ov.notna(), "nationality"] = np.where(_ov[_ov.notna()] == 1, "Overseas", "Indian")  # verified status master wins
print("nationality relabelled (T20I team evidence):", int((_old != targets.nationality).sum()), "of", len(targets), "| overseas now:", int((targets.nationality == "Overseas").sum()))
val = pd.read_csv(FINAL / "model_validation_report.csv")
FEAS = RES / "outputs" / "feasibility"
from ipl2027_lists import AS_OF, AUCTION, TEAMS, LAST_PRICE_CR, NOTES as SRC_NOTES
from feasibility_filter import RR_CONTEXT, PURSE_TOLERANCE
feas_log = pd.read_csv(FEAS / "filter_decision_log.csv")

# ---- picks: highest-CAFS realistic targets per gap, then the MANDATORY RR purse / overseas-slot portfolio check ----
import re as _re
_gid = lambda s: (_re.search(r"GAP-\d+", s or "") or [None])[0]
QUOTA = {"GAP-01": 2, "GAP-02": 2, "GAP-03": 3, "GAP-04": 2, "GAP-05": 1}
cand = targets[targets.realistic & (targets.cafs_score >= 70)].sort_values("cafs_score", ascending=False)
picks, fails, used, filled = [], [], set(), {g: 0 for g in QUOTA}
ov_used, spend = 0, 0.0
for _, t in cand.iterrows():
    g = _gid(t.primary_gap_targeted)
    if g not in QUOTA or filled[g] >= QUOTA[g] or t.player_id in used:
        continue
    is_ov = t.nationality == "Overseas"
    price = LAST_PRICE_CR.get(t.player_name)
    why = None
    if is_ov and ov_used + 1 > RR_CONTEXT["free_overseas_slots"]:
        why = f"needs an overseas slot but RR has only {RR_CONTEXT['free_overseas_slots']} free and the higher-CAFS picks already use {ov_used}"
    elif price is not None and spend + price > RR_CONTEXT["purse_cr"] * PURSE_TOLERANCE:
        why = f"last price Rs {price} cr would take picks to Rs {spend + price:.2f} cr, clearly above (more than 10% over) the Rs {RR_CONTEXT['purse_cr']} cr purse"
    if why:
        fails.append(dict(player=t.player_name, uid=t.uid, gap=g, cafs=round(float(t.cafs_score), 2), reason=why))
        continue
    used.add(t.player_id); filled[g] += 1
    ov_used += int(is_ov); spend += price or 0.0
    picks.append(dict(uid=t.uid, gap=g, price_cr=price))
picks.sort(key=lambda p: -float(targets.loc[targets.uid == p["uid"], "cafs_score"].iloc[0]))
constraint = dict(RR_CONTEXT, purse_tolerance=PURSE_TOLERANCE, picks_overseas=ov_used, picks_known_price_cr=round(spend, 2),
                  priced_picks=sum(1 for p in picks if p["price_cr"] is not None), fails=fails)
print("RR constraint: picks", len(picks), "| overseas", ov_used, "of", RR_CONTEXT["free_overseas_slots"], "free | feasibility fails:", [f["player"] for f in fails])

_ecols = ["shortlist_rank", "original_pri_rank", "player", "pri_pct", "team_2026", "overseas", "status", "release_tier", "last_price_cr", "evidence"]
_el_b = pd.read_csv(FEAS / "Eligible_Top10_Batters.csv")[_ecols]
_el_w = pd.read_csv(FEAS / "Eligible_Top10_Bowlers.csv")[_ecols]
feas = {
    "asOf": AS_OF,
    "auction": AUCTION,
    "eligBat": recs(_el_b), "eligBowl": recs(_el_w),
    "eligOverseas": {"bat": int(_el_b.overseas.sum()), "bowl": int(_el_w.overseas.sum())},
    "excluded": recs(feas_log[feas_log.decision == "EXCLUDED"][["list", "original_pri_rank", "player", "pri_pct", "status", "reason", "evidence"]]),
    "board": recs(pd.read_csv(FEAS / "Acquisition_Priority_Board.csv")[["list", "acq_rank", "player", "original_pri_rank", "pri_pct", "team_2026", "overseas", "status", "release_tier", "afs", "evidence"]]),
    "squadOutlook": recs(pd.read_csv(FINAL / "rr_current_squad.csv")),
    "rrReleased": recs(pd.read_csv(FINAL / "rr_released_players.csv")),
    "constraint": constraint, "notes": SRC_NOTES,
    "statusCounts": pd.read_csv(FEAS / "player_status_master.csv").status.value_counts().to_dict(),
}
val = pd.read_csv(FINAL / "model_validation_report.csv")

data = clean({
    "meta": {"deliveries": bbb_n, "matches": n_matches, "rr_matches": rr_n, "rr_wins": rr_w,
             "bat_pool": len(bat), "bowl_pool": len(bow), "auction_pool": len(targets),
             "realistic_pool": int(targets.realistic.sum())},
    "topBat": top_block(top_b, "bat"), "topBowl": top_block(top_w, "bowl"),
    "batPool": pool(bat, BW, "bat"), "bowlPool": pool(bow, OW, "bowl"),
    "robust": {"bat": {str(k): v for k, v in rb_b.items()}, "bowl": {str(k): v for k, v in rb_w.items()}},
    "evidence": {str(k): v for k, v in ev.items()},
    "pressure": {"batClass": [round(x, 1) for x in cls.reindex(range(5)).fillna(0)], "bowlClass": [round(x, 1) for x in clsb.reindex(range(5)).fillna(0)], "phaseHigh": phase_hp},
    "season": recs(season), "tenure": recs(tenure), "rrBat": recs(rr_bat), "rrBowl": recs(rr_bowl),
    "squad": recs(pd.read_csv(FINAL / "rr_current_squad.csv")), "gaps": recs(pd.read_csv(FINAL / "rr_squad_gaps.csv")),
    "targets": recs(targets), "picks": picks, "validation": recs(val), "feas": feas,
    "weights": {"bat": BW, "bowl": OW},
})
out = Path(__file__).with_name("dashboard_data.json")
out.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
print("wrote", out, out.stat().st_size, "bytes", "| RR matches", rr_n, "wins", rr_w)
print("robustness bat top10:", {r["player"]: rb_b[r["player_id"]] for r in data["topBat"]})

# ---- assemble single-file HTML ----
tpl = Path(__file__).with_name("template.html").read_text(encoding="utf-8")
payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
html = tpl.replace("__DATA__", payload)
for dest in [Path(__file__).with_name("index.html"),
             FINAL / "Interactive_Dashboard_Single_Page.html"]:
    dest.write_text(html, encoding="utf-8")
    print("wrote", dest, len(html), "bytes")

# ---- sanity: default coach weights reproduce CSV CPAS/CAFS ----
t = targets.copy()
bat_m = t.primary_role == "Batter"
cp = np.where(bat_m, .35*t.dci_score + .35*t.smi_score + .2*t.rdi_score.fillna(0) + .1*t.tfi_score,
              .4*t.bdi_score.fillna(0) + .35*t.dci_score + .15*t.smi_score + .1*t.tfi_score)
print("max CPAS diff vs CSV:", float(np.abs(cp - t.cpas_score).max()))
