"""
SupeRR Selector Season 2 - Acquisition-feasibility filter and dynamic Top-10 replacement.

Reads the original PRI rankings, joins the player status master and runs the sequential eligibility pipeline.
Status data: IPL 2027 retention/release lists as of 17 Nov 2026 (src/ipl2027_lists.py) + MANUAL rows below.

Status codes
  A  Available: officially in the auction pool (NONE yet: the register is due 3 Dec 2026)
  B  Potentially available - released by a franchise (or reported registered) but pool not yet official
  C  Retained / contracted by another franchise (IPL 2027 lists, incl. completed trades)
  D  Ineligible (verified nationality / regulatory restriction)
  E  Already with Rajasthan Royals
  F  Withdrawn / retired / opted out of IPL 2027
  G  Status unverified (also the default for any player not in the master)

Mandatory exclusions: C, D, E, F, G.  Plus the RR purse / overseas-slot check (rr_check).
Re-run after the official auction register is published (3 Dec 2026): move players in the register from B to A.
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from config import STATS_DIR, OUTPUTS_DIR
import ipl2027_lists as L

OUT = OUTPUTS_DIR / "feasibility"
OUT.mkdir(parents=True, exist_ok=True)
MASTER = OUT / "player_status_master.csv"

# ---------------------------------------------------------------- status master
# MANUAL rows: players who are not on any franchise list (ineligible, withdrawn, unverified, Bangladesh registrations).
# name|2026 team|nationality|overseas(1/0)|status|release_tier|evidence
PAK = "Pakistani national; no Pakistani player has been selected in the IPL since 2008 (de facto bar, no written rule found)"
MANUAL = f"""
Mohammad Rizwan|Pakistan|Pakistan|1|D|n/a|{PAK}
Babar Azam|Pakistan|Pakistan|1|D|n/a|{PAK}
Fakhar Zaman|Pakistan|Pakistan|1|D|n/a|{PAK}
Haris Rauf|Pakistan|Pakistan|1|D|n/a|{PAK}
Shaheen Afridi|Pakistan|Pakistan|1|D|n/a|{PAK}
Abrar Ahmed|Pakistan|Pakistan|1|D|n/a|{PAK}
Naseem Shah|Pakistan|Pakistan|1|D|n/a|{PAK}
Travis Head|SRH|Australia|1|F|n/a|Released by SRH and skipping IPL 2027 (owner list 17 Nov; Cricket News/Yahoo 17 Nov: opted out of IPL 2027)
Mahendra Singh Dhoni|CSK|India|0|F|n/a|Retired from playing, released by CSK and becomes mentor (owner list 17 Nov; Cricket News/Yahoo 17 Nov: retirement frees Rs 4 cr)
Ajinkya Rahane|KKR|India|0|F|n/a|Retired (owner list 17 Nov; Cricket News/Yahoo 17 Nov)
Andre Russell||West Indies|1|F|n/a|Retired from IPL 30 Nov 2025 (Wikipedia personnel changes; carried from 13 Nov snapshot, not re-checked)
Dinesh Karthik||India|0|F|n/a|Retired from all cricket in Jun 2025 (prior knowledge, NOT re-verified this session)
Mitchell Starc|DC|Australia|1|B|n/a|Released by DC (Rs 11.75 cr). Cricket News/Yahoo 17 Nov says he opted out: unclear whether that means unavailable for IPL 2027, so treated as unconfirmed
Taskin Ahmed||Bangladesh|1|B|n/a|One of 7 Bangladeshi players reported registered for the auction (BCB confirmation 12-13 Nov; Outlook/SportsCafe/Daily Star). Registration is not the official auction list; 2026 team not found
Hasan Mahmud||Bangladesh|1|B|n/a|One of 7 Bangladeshi players reported registered for the auction (BCB 12-13 Nov, press). Not the official auction list; 2026 team not found
Towhid Hridoy||Bangladesh|1|B|n/a|One of 7 Bangladeshi players reported registered for the auction (BCB 12-13 Nov, press). Not the official auction list; 2026 team not found
Reeza Hendricks||South Africa|1|G|n/a|On no franchise list; only item found is a 2026 PSL Karachi Kings replacement; no IPL 2027 registration info
David Warner||Australia|1|G|n/a|On no franchise list; did not register for IPL 2026 auction (Wisden/Olympics.com); no IPL 2027 info
Glenn Maxwell||Australia|1|G|n/a|On no franchise list; skipped IPL 2026 auction registration (Wisden/Olympics.com); no IPL 2027 info
Moeen Ali||England|1|G|n/a|On no franchise list; chose PSL over IPL in 2026; no IPL 2027 info
Harry Brook||England|1|G|n/a|On no franchise list; no IPL 2026 record found; no IPL 2027 info
Adam Zampa||Australia|1|G|n/a|On no franchise list; no IPL 2026 record found; no IPL 2027 info
Reece Topley||England|1|G|n/a|On no franchise list; no IPL 2027 info found
Chris Woakes||England|1|G|n/a|On no franchise list; no IPL 2027 info found
Shakib Al Hasan||Bangladesh|1|G|n/a|Not among the 7 Bangladeshi players reported registered; no IPL 2027 info
Shai Hope||West Indies|1|G|n/a|On no franchise list; no IPL 2027 info found
Sikandar Raza||Zimbabwe|1|G|n/a|On no franchise list; no IPL 2027 info found
Matthew Wade||Australia|1|G|n/a|On no franchise list; no IPL 2027 info found
Jaker Ali Anik||Bangladesh|1|G|n/a|On no franchise list; not among the 7 reported Bangladeshi registrations
Asif Khan||UAE|1|G|n/a|On no franchise list; no IPL 2027 info found
Vijay Shankar||India|0|G|n/a|On no franchise list; no IPL 2027 info found
Tim Southee||New Zealand|1|G|n/a|On no franchise list; 13 Nov snapshot had him as an incoming KKR coach (unverified)
Mujeeb Ur Rahman||Afghanistan|1|G|n/a|On no franchise list; no IPL 2027 info found
Maheesh Theekshana||Sri Lanka|1|G|n/a|On no franchise list; no IPL 2027 info found
Salman Mirza||Afghanistan|1|G|n/a|On no franchise list; no IPL 2027 info found
Mark Adair||Ireland|1|G|n/a|On no franchise list; no IPL 2027 info found
Mark Wood||England|1|G|n/a|On no franchise list; no IPL 2027 info found
Craig Young||Ireland|1|G|n/a|On no franchise list; no IPL 2027 info found
Naveen ul Haq||Afghanistan|1|G|n/a|On no franchise list; no IPL 2027 info found
Richard Ngarava||Zimbabwe|1|G|n/a|On no franchise list; no IPL 2027 info found
Jason Behrendorff||Australia|1|G|n/a|On no franchise list; no IPL 2027 info found
Matthew Humphreys||England|1|G|n/a|On no franchise list; no IPL 2027 info found
Adil Rashid||England|1|G|n/a|On no franchise list; no IPL 2027 info found
Dwayne Bravo||West Indies|1|G|n/a|On no franchise list; no IPL 2027 info found
Jonny Bairstow||England|1|G|n/a|Unsold at 2026 auction; on no list; no IPL 2027 registration info
Daryl Mitchell||New Zealand|1|G|n/a|Unsold at 2026 auction; on no list; no IPL 2027 registration info
Alzarri Joseph||West Indies|1|G|n/a|Unsold at 2026 auction; on no list; no IPL 2027 registration info
"""

# overseas players appearing on the franchise lists (everyone else on the lists is Indian)
OVERSEAS_LISTED = {x.strip() for x in """Dewald Brevis|Noor Ahmad|Jamie Overton|Akeal Hosein|Matthew Short|Matt Henry|Zak Foulkes|Spencer Johnson|Dian Forrester|Liam Livingstone|Jack Edwards|
Ryan Rickelton|Quinton de Kock|Corbin Bosch|Mitchell Santner|Sherfane Rutherford|Will Jacks|Trent Boult|Allah Ghazanfar|Keshav Maharaj|
Phil Salt|Tim David|Jordan Cox|Romario Shepherd|Josh Hazlewood|Jacob Duffy|Nuwan Thushara|Jacob Bethell|Richard Gleeson|
Cameron Green|Sunil Narine|Finn Allen|Rovman Powell|Tim Seifert|Matheesha Pathirana|Mustafizur Rahman|Rachin Ravindra|Blessing Muzarabani|
Tristan Stubbs|David Miller|Lungi Ngidi|Kyle Jamieson|Pathum Nissanka|Ben Duckett|Dushmantha Chameera|Rehan Ahmed|
Marco Jansen|Marcus Stoinis|Azmatullah Omarzai|Cooper Connolly|Ben Dwarshuis|Xavier Bartlett|Lockie Ferguson|Mitch Owen|
Pat Cummins|Heinrich Klaasen|Brydon Carse|Nathan Ellis|Kamindu Mendis|Dilshan Madushanka|Gerald Coetzee|David Payne|
Jofra Archer|Nandre Burger|Dasun Shanaka|Donovan Ferreira|Lhuan-dre Pretorius|Shimron Hetmyer|Adam Milne|Kwena Maphaka|
Jos Buttler|Rashid Khan|Kagiso Rabada|Jason Holder|Glenn Phillips|Tom Banton|Luke Wood|Connor Esterhuizen|
Nicholas Pooran|Mitchell Marsh|Josh Inglis|Aiden Markram|Anrich Nortje|Wanindu Hasaranga|Matthew Breetzke|George Linde|Sam Curran""".replace("\n", "").split("|") if x.strip()}


def _manual_rows():
    rows = {}
    for line in MANUAL.strip().splitlines():
        p = line.split("|")
        rows[p[0]] = dict(player_name=p[0], team_2026=p[1], nationality=p[2], overseas=int(p[3]) if p[3] else None,
                          status=p[4], release_tier=p[5], evidence=p[6])
    return rows


def build_master():
    rows = _manual_rows()
    manual_names = set(rows)
    trades = {t[0]: t for t in L.TRADES}
    for team, d in L.TEAMS.items():
        for kind in ("retained", "traded_in", "released"):
            for raw in d[kind]:
                nm = L.ALIAS.get(raw, raw)
                if nm in manual_names:
                    continue
                ov = 1 if raw in OVERSEAS_LISTED else 0
                if kind == "released":
                    status = "B"
                    price = L.LAST_PRICE_CR.get(raw)
                    ev = (f"Released by {team} (IPL 2027 lists, {L.AS_OF}; press-compiled, official page not reachable)"
                          + (f"; last price Rs {price} cr" if price else "")
                          + "; official auction register not published until 3 Dec 2026, so B not A")
                    if raw == "Mustafizur Rahman":
                        ev += "; BCB confirmed he registered for the auction (12-13 Nov, press)"
                    if raw == "Wanindu Hasaranga":
                        ev += "; withdrew from IPL 2026 (NOC denied)"
                else:
                    status = "E" if team == "RR" else "C"
                    if kind == "traded_in":
                        t = trades.get(raw)
                        src = f" from {t[1]}" if t else ""
                        val = f" (Rs {t[3]} cr)" if t and t[3] else ""
                        ev = f"Traded in{src} to {team}{val}; completed trade ({L.AS_OF} lists; press-compiled)"
                    else:
                        ev = f"Retained by {team} (IPL 2027 lists, {L.AS_OF}; press-compiled, official page not reachable)"
                    if status == "E":
                        ev += " - on RR squad"
                    if raw in ("Kyle Jamieson", "Lungi Ngidi"):
                        ev += "; reported by SportsTak/Cricket Times only, Wisden silent"
                rows[nm] = dict(player_name=nm, team_2026=team, nationality="", overseas=ov, status=status,
                                release_tier="n/a", evidence=ev)
    for team, raw in L.EXTRA_RELEASED:
        nm = L.ALIAS.get(raw, raw)
        if nm not in rows:
            rows[nm] = dict(player_name=nm, team_2026=team, nationality="", overseas=0, status="B", release_tier="n/a",
                            evidence=f"Released by {team} per Cricket News/Yahoo 17 Nov only (not in owner list); official page not reachable; auction register not published until 3 Dec 2026, so B not A")
    for nm, note in L.CONFLICTS.items():
        if nm in rows:
            rows[nm]["evidence"] += "; SOURCE CONFLICT: " + note
    if "T Natarajan" in rows:
        rows["Natarajan T"] = dict(rows["T Natarajan"], player_name="Natarajan T")
    return pd.DataFrame(list(rows.values()))

# ---------------------------------------------------------------- RR context (from the 17 Nov lists)
_RR = L.TEAMS["RR"]
RR_CONTEXT = dict(
    as_of=L.AS_OF, max_overseas=8,
    purse_cr=_RR["purse"], open_slots=_RR["open_slots"],
    free_overseas_slots=_RR["overseas_free"],
    rr_overseas_retained=8 - _RR["overseas_free"],
)
AVAIL = {"A": 1.0, "B": 0.8}   # A = in the official auction pool (none yet); B = released, pool not yet official (judgement weight)
MAX_BOARD_RANK = 60      # only players inside the original PRI top-60 enter the priority board
OVERSEAS_FACTOR = 0.85   # RR can add at most 3 overseas players
PURSE_TOLERANCE = 1.10   # a price "clearly exceeds" the purse only when more than 10% over (last prices are not 2027 forecasts)

MANDATORY_FAIL = {"C": "Retained / contracted by another franchise (IPL 2027 lists)",
                  "D": "Ineligible",
                  "E": "Already with RR",
                  "F": "Withdrawn / retired / opted out",
                  "G": "Status unverified"}


def rr_check(player, overseas, price_cr=None):
    """Mandatory RR feasibility check on purse and overseas slots. Returns (ok, reason).
    Price = last disclosed price (not a 2027 forecast); unknown price is not failed but flagged elsewhere."""
    price = price_cr if price_cr is not None else L.LAST_PRICE_CR.get(player)
    if price is not None and price > RR_CONTEXT["purse_cr"] * PURSE_TOLERANCE:
        return False, f"last price Rs {price} cr exceeds RR purse Rs {RR_CONTEXT['purse_cr']} cr"
    if overseas == 1 and RR_CONTEXT["free_overseas_slots"] <= 0:
        return False, "needs an overseas slot; RR has none free"
    return True, ""


def run(df_rank, name_col, rank_col, pri_col, master, label, n=10):
    m = master.drop_duplicates("player_name").set_index("player_name")
    log, shortlist = [], []
    for _, r in df_rank.sort_values(pri_col, ascending=False).iterrows():
        nm = r[name_col]
        st = m.loc[nm] if nm in m.index else None
        status = st["status"] if st is not None else "G"
        tier = st["release_tier"] if st is not None else "n/a"
        ev = st["evidence"] if st is not None else "Not in status master: no reliable information"
        over = st["overseas"] if st is not None else None
        team = st["team_2026"] if st is not None else ""
        if status in MANDATORY_FAIL:
            decision, reason = "EXCLUDED", MANDATORY_FAIL[status]
        else:
            ok, why = rr_check(nm, over)
            if not ok:
                decision, reason = "EXCLUDED", "RR feasibility fail: " + why
            else:
                decision, reason = "INCLUDED", "Eligible; " + ("in official auction pool" if status == "A" else "released, auction pool not yet official")
        price = L.LAST_PRICE_CR.get(nm)
        rec = dict(list=label, original_pri_rank=int(r[rank_col]), player=nm, pri_pct=r[pri_col],
                   team_2026=team, overseas=over, status=status, release_tier=tier,
                   last_price_cr=price, decision=decision, reason=reason, evidence=ev)
        if decision == "INCLUDED" and len(shortlist) < n:
            rec["shortlist_rank"] = len(shortlist) + 1
            shortlist.append(rec)
        log.append(rec)
        if len(shortlist) >= n:
            break
    return pd.DataFrame(shortlist), pd.DataFrame(log)


def afs_board(df_rank, name_col, rank_col, pri_col, master, label, n=10):
    """Acquisition Feasibility Score = PRI x availability weight x overseas factor (heuristic); RR check applied."""
    m = master.drop_duplicates("player_name").set_index("player_name")
    rows = []
    for _, r in df_rank.iterrows():
        nm = r[name_col]
        if nm not in m.index:
            continue
        s = m.loc[nm]
        if s["status"] not in ("A", "B") or r[rank_col] > MAX_BOARD_RANK:
            continue
        if not rr_check(nm, s["overseas"])[0]:
            continue
        av = AVAIL[s["status"]]
        f = OVERSEAS_FACTOR if s["overseas"] == 1 else 1.0
        rows.append(dict(list=label, player=nm, original_pri_rank=int(r[rank_col]), pri_pct=r[pri_col],
                         team_2026=s["team_2026"], overseas=int(s["overseas"]), status=s["status"],
                         release_tier=s["release_tier"], availability_weight=av,
                         overseas_factor=f, afs=round(r[pri_col] * av * f, 2), evidence=s["evidence"]))
    b = pd.DataFrame(rows).sort_values("afs", ascending=False).head(n).reset_index(drop=True)
    b.insert(0, "acq_rank", b.index + 1)
    return b


def main():
    master = build_master()
    master.to_csv(MASTER, index=False)
    bat = pd.read_csv(STATS_DIR / "batting_reliability_model.csv")
    bowl = pd.read_csv(STATS_DIR / "bowling_reliability_model.csv")
    sb, lb = run(bat, "player_name", "batting_rank", "batting_reliability_pct", master, "Batters")
    sw, lw = run(bowl, "player_name", "bowling_rank", "bowling_reliability_pct", master, "Bowlers")
    sb.to_csv(OUT / "Eligible_Top10_Batters.csv", index=False)
    sw.to_csv(OUT / "Eligible_Top10_Bowlers.csv", index=False)
    pd.concat([lb, lw]).to_csv(OUT / "filter_decision_log.csv", index=False)
    bb = afs_board(bat, "player_name", "batting_rank", "batting_reliability_pct", master, "Batters")
    bw = afs_board(bowl, "player_name", "bowling_rank", "bowling_reliability_pct", master, "Bowlers")
    pd.concat([bb, bw]).to_csv(OUT / "Acquisition_Priority_Board.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
    for t, d in (("ELIGIBLE TOP-10 BATTERS", sb), ("ELIGIBLE TOP-10 BOWLERS", sw),
                 ("PRIORITY BOARD BATTERS", bb), ("PRIORITY BOARD BOWLERS", bw)):
        print("\n" + t)
        cols = [c for c in ("acq_rank", "shortlist_rank", "original_pri_rank", "player", "pri_pct", "team_2026",
                            "status", "overseas", "afs") if c in d.columns]
        print(d[cols].to_string(index=False))
    for lab, lg in (("Batters", lb), ("Bowlers", lw)):
        print(f"\nEXCLUSIONS ({lab})")
        print(lg[lg.decision == "EXCLUDED"][["original_pri_rank", "player", "status", "reason"]].to_string(index=False))
    pool = set(bat.player_name) | set(bowl.player_name)
    listed = {L.ALIAS.get(x, x) for t in L.TEAMS.values() for k in ("retained", "traded_in", "released") for x in t[k]}
    print(f"\nList names matched to PRI pool: {len(listed & pool)} of {len(listed)}")

if __name__ == "__main__":
    main()
