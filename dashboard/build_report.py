"""Builds the submission PDF from dashboard_data.json (same source as the dashboard)."""
import json, re, io
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether)

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
OUT = ROOT / "SupeRR_Selector_RR_2027_Final" / "RR_IPL2027_Round1_Final_Submission.pdf"
D = json.loads((HERE / "dashboard_data.json").read_text(encoding="utf-8"))

BLUE, NAVY, PINK = colors.HexColor("#254AA5"), colors.HexColor("#16295c"), colors.HexColor("#EA1A85")
TINT = colors.HexColor("#eef2fb")
ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=13.5, textColor=colors.HexColor("#1b2437"))
small = ParagraphStyle("s", parent=body, fontSize=8, leading=10.5, textColor=colors.HexColor("#5d6881"))
h1 = ParagraphStyle("h1", parent=body, fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=NAVY)
h2 = ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=NAVY, spaceBefore=10, spaceAfter=4)
h3 = ParagraphStyle("h3", parent=body, fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=BLUE, spaceBefore=6)
bul = ParagraphStyle("bul", parent=body, leftIndent=12, bulletIndent=2, spaceAfter=2)
cell = ParagraphStyle("c", parent=body, fontSize=8.2, leading=10.2)

f1 = lambda x: "-" if x is None else f"{x:.1f}"
f2 = lambda x: "-" if x is None else f"{x:.2f}"
fi = lambda x: f"{int(round(x)):,}"
M = D["meta"]

def tbl(rows, widths, head=True):
    t = Table(rows, colWidths=widths, repeatRows=1 if head else 0)
    st = [("FONT", (0, 0), (-1, -1), "Helvetica", 8.2), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#d5dcec")), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if head:
        st += [("BACKGROUND", (0, 0), (-1, 0), TINT), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.2), ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
               ("LINEBELOW", (0, 0), (-1, 0), 1.2, BLUE)]
    t.setStyle(TableStyle(st))
    return t

def footer(c, d):
    c.saveState(); c.setFont("Helvetica", 7.5); c.setFillColor(colors.HexColor("#5d6881"))
    c.drawString(18 * mm, 10 * mm, "Rajasthan Royals | SupeRR Selector Season 2 | Round 1"); c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {d.page}")
    c.setStrokeColor(PINK); c.setLineWidth(1.5); c.line(18 * mm, A4[1] - 12 * mm, A4[0] - 18 * mm, A4[1] - 12 * mm); c.restoreState()

# ---------- picks (same rule as the dashboard) ----------
gapre = re.compile(r"GAP-\d+")
gid = lambda s: (gapre.search(s or "") or [None])[0]
gaps = {g["gap_id"]: g for g in D["gaps"]}
F = D["feas"]
STAT = {"A": "Available (in the official auction pool)", "B": "Released / reported registered; auction pool not yet official", "C": "Retained or traded: contracted by another franchise",
        "D": "Ineligible", "E": "Already with RR", "F": "Withdrawn / retired / opted out", "G": "Status unverified (no reliable information)"}
CON = F["constraint"]
_by = {t["uid"]: t for t in D["targets"]}
picks = [{**_by[p["uid"]], "gap": p["gap"], "price_cr": p["price_cr"]} for p in D["picks"]]

def pool_row(t):
    bat = t["primary_role"] == "Batter"
    pl = next((p for p in (D["batPool"] if bat else D["bowlPool"]) if p["player_id"] == t["player_id"]), None)
    return bat, pl, len(D["batPool"] if bat else D["bowlPool"])


mono = ParagraphStyle("mono", parent=body, fontName="Courier", fontSize=7.2, leading=9.4)
import textwrap
def fm(lines):
    wrapped = []
    for l in lines:
        wrapped += textwrap.wrap(l, width=104, subsequent_indent="      ", break_long_words=False, replace_whitespace=False) or [""]
    txt = "<br/>".join(l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;") for l in wrapped)
    t = Table([[Paragraph(txt, mono)]], colWidths=[174 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TINT), ("LINEBEFORE", (0, 0), (0, -1), 2, BLUE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t
_bw = [t for t in D["targets"] if t["primary_role"] == "Bowler"]
pick_bw = sum(1 for t in picks if t['primary_role'] == 'Bowler')
pick_sat = sum(1 for t in picks if t['primary_role'] == 'Bowler' and (t['sgf_score'] or 0) >= 99.99)
sat_share = sum(1 for t in _bw if (t["sgf_score"] or 0) >= 99.99) / max(len(_bw), 1) * 100

# ---------- charts ----------
def chart():
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.0))
    for a, rows, key, name, col in [(ax[0], D["topBat"], "player", "Top 10 batters", "#254AA5"), (ax[1], D["topBowl"], "player", "Top 10 bowlers", "#EA1A85")]:
        names = [r[key] for r in rows][::-1]; vals = [r["reliability_pct"] for r in rows][::-1]
        a.barh(names, vals, color=col); a.set_xlim(60, 90); a.set_title(name, fontsize=9, loc="left", color="#16295c", fontweight="bold")
        a.tick_params(labelsize=7); a.spines[["top", "right"]].set_visible(False)
        for i, v in enumerate(vals): a.text(v + .3, i, f"{v:.1f}", va="center", fontsize=7)
        a.set_xlabel("Pressure Reliability Index", fontsize=7)
    fig.tight_layout(); b = io.BytesIO(); fig.savefig(b, format="png", dpi=200); plt.close(fig); b.seek(0)
    return Image(b, width=174 * mm, height=70 * mm)

S = []
S += [Paragraph("SupeRR Selector Season 2: Help Shape Rajasthan Royals' IPL 2027 Auction Strategy", h1), Spacer(1, 3),
      Paragraph("Round 1: Identify the Most Reliable Players Under Pressure", ParagraphStyle("x", parent=body, textColor=BLUE, fontSize=12, fontName="Helvetica-Bold")), Spacer(1, 8)]
tb, tw = D["topBat"][0], D["topBowl"][0]
rb = lambda k, rows: sum(1 for r in rows if D["robust"][k][str(r["player_id"])] >= 90)
S += [Paragraph("Summary", h2),
      Paragraph(f"We scored {M['bat_pool']} batters and {M['bowl_pool']} bowlers on {fi(M['deliveries'])} ball-by-ball deliveries from {fi(M['matches'])} IPL and T20I matches (2022 onwards). "
                f"<b>The Final Top 10 (below) keeps only players who are both available to RR and able to handle pressure; the pressure-only ranking is in section 3.</b> "
                f"The most reliable under pressure are <b>{tb['player']}</b> (batters, index {f1(tb['reliability_pct'])}) and <b>{tw['player']}</b> (bowlers, index {f1(tw['reliability_pct'])}). "
                f"We then screened {M['auction_pool']} players against Rajasthan Royals' squad gaps, the IPL 2027 retention and release lists as reported on {F['asOf']}, and RR's purse and overseas-slot limits to produce {len(picks)} recommended targets. "
                f"The auction pool is not official until the register is published (due {F['auction']['final_register']}; auction {F['auction']['date']}, {F['auction']['venue']}), so released players are 'potentially available' rather than confirmed.", body),
      Spacer(1, 4),
      Paragraph(f"Rankings are not equally firm: {rb('bat', D['topBat'])} of the 10 batters and {rb('bowl', D['topBowl'])} of the 10 bowlers stay in the Top 10 in at least 90% of 2,000 random re-weightings of the score, so the lower places are weight-sensitive.", body),
      Spacer(1, 6), chart()]

ecol0 = [8 * mm, 40 * mm, 22 * mm, 14 * mm, 22 * mm, 16 * mm, 14 * mm]
def frow(r): return [r["shortlist_rank"], r["player"] + (" (OS)" if r["overseas"] == 1 else ""), r["team_2026"] or "reg.", f1(r["pri_pct"]), f1(r["pri_percentile"]) + "%", "#" + str(r["original_pri_rank"]), r["status"]]
S += [Paragraph("Final Top 10: available AND able to handle pressure", h2),
      Paragraph(f"A player is on this list only if he passes <b>both</b> tests: (1) he is available to Rajasthan Royals (released by his franchise on the {F['asOf']} lists, so not retained, traded, already at RR, retired, ineligible or unverified), and (2) he can handle pressure (Pressure Reliability Index in the top {100 - F['gate']}% of all scored players, and not a low sample). "
                "Available players who fail the pressure test, and pressure-proof players who are not available (for example Bumrah, retained by MI), are never selected. OS = overseas; RR can add at most 3 overseas players. Status B = released but not yet in an official auction pool.", body),
      Paragraph("Batters", h3), tbl([["#", "Batter", "Released by", "PRI", "Pressure pctile", "PRI rank", "Status"]] + [frow(r) for r in F["eligBat"]], ecol0),
      Paragraph("Bowlers", h3), tbl([["#", "Bowler", "Released by", "PRI", "Pressure pctile", "PRI rank", "Status"]] + [frow(r) for r in F["eligBowl"]], ecol0),
      Spacer(1, 3), Paragraph("Sections 3 and 4 show the pressure-only ranking and how availability was applied. Availability comes from press-reported lists (an official list could not be reached); the Bangladeshi players are only reported as registered.", small)]

S += [PageBreak(), Paragraph("1. Methodology", h2),
      Paragraph("<b>Defining pressure.</b> Every delivery gets a pressure index from 0 to 1, built from the factors in the brief:", body)]
for t in ["<b>Required run rate (40%)</b>: 14 or more scores 1.0, 10 or more 0.7, 7 or more 0.4, otherwise 0.1 (chases).",
          "<b>Wickets remaining (25%)</b>: 2 or fewer scores 1.0, 4 or fewer 0.7, 6 or fewer 0.4, otherwise 0.1.",
          "<b>Innings stage (20%)</b>: death overs 0.6, middle overs 0.3, powerplay 0.2.",
          "<b>Par deficit, first innings (15%)</b>: run rate well under 8 an over raises pressure (0.5, 0.3 or 0.1)."]:
    S.append(Paragraph(t, bul, bulletText="•"))
hp = D["pressure"]["batClass"][3] + D["pressure"]["batClass"][4]
S += [Paragraph(f"Balls with an index of 0.50 or more (High or Extreme) are treated as pressure balls. They are {hp:.1f}% of all deliveries and sit mostly in the death overs "
                f"({D['pressure']['phaseHigh']['Death']}% of death-over balls versus {D['pressure']['phaseHigh']['Middle']}% in the middle overs), so pressure statistics rest on far less data than overall statistics.", body),
      Paragraph("<b>Scoring players.</b> The Pressure Reliability Index (PRI) combines seven components, each scaled 0 to 1 and then weighted:", body)]
W = D["weights"]
bn = ["Quality (overall)", "Consistency", "Pressure performance", "Pressure consistency", "Boundary conversion / Wicket quality", "Strike rotation / Dot-ball generation", "Acceleration / Economy control"]
rows = [["Component (batter / bowler variant)", "Weight"]] + [[bn[i], f"{list(W['bat'].values())[i] * 100:.0f}%"] for i in range(7)]
S += [Spacer(1, 3), tbl(rows, [120 * mm, 22 * mm]), Spacer(1, 4),
      Paragraph("Quality and consistency are shrunk toward the population mean with an empirical-Bayes weight n / (n + 15), where n is innings (batters) or matches (bowlers), so small samples cannot rank highly on a few lucky games. "
                "Each player carries a sample-size label (High from 30 innings or matches). Bowlers are also credited for the quality of the batters they dismiss.", body),
      Paragraph("<b>Checking the rankings.</b> We re-ranked every player under 2,000 random perturbations of the weights, and report how often each Top 10 name stays in the Top 10. "
                "Confidence intervals quoted for batters and bowlers are bootstrap intervals on mean runs per innings and mean economy per match, not on the index itself.", body)]


S += [PageBreak(), Paragraph("2. Formulas and calculation details", h2),
      Paragraph("All formulas below are taken from the project's scoring code. Notation: <b>n(x)</b> = clip((x - P5) / (P95 - P5), 0, 1), where P5 and P95 are the 5th and 95th percentiles of x across all scored players "
                "(a robust min-max that stops outliers compressing everyone else); <b>inv(x) = 1 - n(x)</b> is used where lower is better.", body),
      Paragraph("2.1 Pressure index (per delivery)", h3),
      fm(["R = 1.0 if required run rate >= 14 | 0.7 if >= 10 | 0.4 if >= 7 | else 0.1   (second innings; 0 in first)",
          "W = 1.0 if wickets remaining <= 2 | 0.7 if <= 4 | 0.4 if <= 6 | else 0.1",
          "S = 0.6 death (overs 16-20) | 0.3 middle | 0.2 powerplay",
          "G = first-innings par deficit (after 2 overs, par 8 an over): 0.5 if run rate < 6 | 0.3 if < 7 | else 0.1",
          "",
          "Batting pressure index   BPI  = clip(0.40 R + 0.25 W + 0.20 S + 0.15 G, 0, 1)",
          "Pressure ball (batting)  BPI >= 0.50     classes: <0.10 Negligible, <0.30 Low, <0.50 Moderate, <0.70 High, else Extreme",
          "",
          "R' = R in the second innings, 0.3 in the first      W' = 0.5 if wickets remaining >= 8 | 0.4 if >= 5 | else 0.3",
          "S' = 0.8 death | 0.5 powerplay | 0.3 middle",
          "Bowling pressure index   BwPI = clip(0.35 R' + 0.25 W' + 0.40 S', 0, 1)      Pressure ball (bowling): BwPI >= 0.50"]),
      Paragraph("Required run rate already combines runs required, balls remaining and the closeness of the chase, which is how those factors enter the index.", small),
      Paragraph("2.2 Batter components (all players, IPL + T20I combined)", h3),
      fm(["Quality          Q   = 0.45 n(average) + 0.35 n(strike rate) + 0.20 n(share of innings with 30+)",
          "Consistency      C   = 0.30 inv(CV of runs) + 0.30 inv(share of innings under 10) + 0.25 n(median runs) + 0.15 n(share 20+)",
          "Pressure perf.   P   = 0.45 n(pressure strike rate) + 0.35 n(pressure runs per innings) + 0.20 inv(pressure dot %)",
          "Pressure consist. PC = 0.60 inv(CV of pressure strike rate) + 0.40 n(number of pressure innings)",
          "Boundary         B   = n(boundary %)",
          "Strike rotation  Rot = inv(dot ball %)",
          "Acceleration     A   = n(death-over strike rate / overall strike rate)"]),
      Paragraph("2.3 Bowler components", h3),
      fm(["Quality          Q   = 0.40 inv(economy) + 0.35 n(wickets per match) + 0.25 inv(bowling average)",
          "Consistency      C   = 0.40 inv(CV of match economy) + 0.35 n(share of matches with 1+ wicket) + 0.25 inv(share with 0 wickets)",
          "Pressure perf.   P   = 0.45 inv(pressure economy) + 0.35 n(pressure wickets) + 0.20 n(pressure dot %)",
          "Pressure consist. PC = 0.60 inv(CV of pressure economy) + 0.40 n(number of pressure matches)",
          "Wicket quality   WQ  = 0.60 n(mean wicket quality) + 0.40 n(high-threat dismissals)",
          "Dot balls        Dot = n(dot ball %)            Economy control   EC = inv(economy)"]),
      Paragraph("Wicket quality of one dismissal, and the threat score of the batter dismissed:", body),
      fm(["wicket quality = clip(0.40 T + 0.25 BwPI at the wicket + 0.20 phase weight + 0.15 critical, 0, 1)",
          "   phase weight: powerplay 0.9, middle 0.8, death 1.0      critical: 1.0 if wickets remaining <= 4, 0.6 if <= 7, else 0.3",
          "T (batter threat) = clip(0.45 n(avg*) + 0.35 n(strike rate) + 0.20 n(share of innings 30+), 0, 1)",
          "   avg* = (innings x average + 15 x population average) / (innings + 15)"]),
      Paragraph("2.4 Shrinkage, final index and sample labels", h3),
      fm(["w = n / (n + K),   K = 15,   n = innings (batters) or matches (bowlers)",
          "Q_shrunk = w Q + (1 - w) mean(Q)            C_shrunk = w C + (1 - w) mean(C)",
          "",
          "PRI (batter) = 100 x clip(0.20 Q_shrunk + 0.20 C_shrunk + 0.25 P + 0.15 PC + 0.10 B + 0.05 Rot + 0.05 A, 0, 1)",
          "PRI (bowler) = 100 x clip(0.20 Q_shrunk + 0.20 C_shrunk + 0.25 P + 0.15 PC + 0.10 WQ + 0.05 Dot + 0.05 EC, 0, 1)",
          "",
          "Sample label: batters High if innings >= 30, Medium >= 20, Moderate >= 10, else Low (bowlers use matches, same style of cut-offs)",
          "95% interval: 500 bootstrap resamples of per-innings runs (batters) or per-match economy (bowlers); 2.5th and 97.5th percentiles"]),
      Paragraph("The 40% weight on pressure components (P and PC are 25% + 15%) is what makes this a pressure ranking rather than a general quality ranking; the remaining weight keeps the score honest about overall ability and consistency.", small),
      Paragraph("2.5 Stress test of the ranking", h3),
      fm(["For each of 2,000 trials:  w ~ Dirichlet(40 x w0)  (a random re-weighting centred on the official weights w0)",
          "score_i = sum_k w_k x component_ik for every player;   record which players land in the Top 10",
          "Top-10 survival (%) = share of trials in which the player is in the Top 10"]),
      Paragraph("2.6 Coach alignment, squad-gap fit, and the combined score", h3),
      Paragraph("Coach-alignment indices use a plain min-max over all scored players (called m(x) here, and mi(x) = 1 - m(x)):", body),
      fm(["Batters:  DCI = 0.35 mi(CV runs) + 0.35 m(pressure perf.) + 0.30 mi(dot %)",
          "          SMI = 0.35 m(boundary %) + 0.35 m(strike rate) + 0.30 m(death strike rate)",
          "          RDI = 0.35 m(consistency) + 0.35 m(1 - share under 10) + 0.30 m(average)",
          "          TFI = 0.5 min(powerplay balls, 30)/30 + 0.5 min(death balls, 30)/30",
          "          CPAS(bat) = 100 (0.35 DCI + 0.35 SMI + 0.20 RDI + 0.10 TFI)",
          "Bowlers:  BDI = 0.35 m(dot %) + 0.35 m(wicket quality) + 0.30 mi(death economy)",
          "          DCI = 0.40 mi(CV economy) + 0.35 mi(pressure economy) + 0.25 m(pressure wickets)",
          "          SMI = 0.40 m(wickets per match) + 0.30 m(powerplay wicket rate) + 0.30 m(dot-ball score)",
          "          TFI as for batters (powerplay and death overs, 30-ball cap)",
          "          CPAS(bowl) = 100 (0.40 BDI + 0.35 DCI + 0.15 SMI + 0.10 TFI)"]),
      fm(["Gap fit (batters), each capped to 0-100:",
          "  gap1 (opener)   = 100 (0.45 min(PP SR,180)/180 + 0.35 min(boundary %,28)/28 + 0.20 max(0,50 - dot %)/50)",
          "  gap2 (finisher) = 100 (0.40 min(death SR,200)/200 + 0.35 min(pressure SR,180)/180 + 0.25 max(0,1.2 - CV runs)/1.2)",
          "Gap fit (bowlers):",
          "  gap3 (pace/death) = 100 (0.45 max(0,13 - death econ)/5 + 0.35 min(dot %,55)/55 + 0.20 max(0,12 - pressure econ)/4)",
          "  gap4 (spin)       = 100 (0.40 max(0,10 - economy)/3 + 0.40 min(wickets,30)/30 + 0.20 min(dot %,50)/50)",
          "SGF = max of the player's gap fits.",
          "Versatility VF (bat)  = 100 (0.40 min(PP balls,30)/30 + 0.40 min(death balls,30)/30 + 0.20 min(runs,500)/500)",
          "Versatility VF (bowl) = 100 (0.40 min(PP balls,36)/36 + 0.40 min(death balls,36)/36 + 0.20 min(wickets,20)/20)",
          "",
          "CAFS = 0.40 PRI + 0.30 CPAS + 0.20 SGF + 0.10 VF"]),
      Paragraph("A 'realistic target' is a player with status A or B (released by a franchise, so not retained, traded, already at RR, withdrawn or unverified) who also passes RR's purse and overseas-slot check.", small)]

S += [PageBreak(), Paragraph("3. Top 10 most reliable under pressure (pressure-only ranking)", h2),
      Paragraph("<b>This is the pressure-only ranking, before availability.</b> It comes only from the supplied ball-by-ball data, so retained or traded players such as Bumrah appear here but cannot be bought. The Final Top 10 at the start of this report applies availability on top of this ranking; section 4 shows how.", body), Paragraph("Batters", h3)]
rows = [["#", "Batter", "Inn", "Runs", "SR", "Press. SR", "Press. inn", "Sample", "PRI", "Top-10 %"]]
for r in D["topBat"]:
    rows.append([r["rank"], r["player"], r["innings"], fi(r["total_runs"]), f1(r["strike_rate"]), f1(r["pressure_sr"]), r["pressure_innings"], r["sample_reliability"], f1(r["reliability_pct"]), f"{D['robust']['bat'][str(r['player_id'])]:.0f}%"])
S.append(tbl(rows, [8 * mm, 38 * mm, 12 * mm, 16 * mm, 14 * mm, 20 * mm, 20 * mm, 17 * mm, 14 * mm, 15 * mm]))
S.append(Paragraph("Bowlers", h3))
rows = [["#", "Bowler", "Mat", "Wkts", "Econ", "Press. econ", "Press. wkts", "Sample", "PRI", "Top-10 %"]]
for r in D["topBowl"]:
    rows.append([r["rank"], r["player"], r["matches"], r["wickets"], f2(r["economy"]), f2(r["pressure_economy"]), r["pressure_wickets"], r["sample_reliability"], f1(r["reliability_pct"]), f"{D['robust']['bowl'][str(r['player_id'])]:.0f}%"])
S.append(tbl(rows, [8 * mm, 38 * mm, 12 * mm, 14 * mm, 14 * mm, 22 * mm, 22 * mm, 17 * mm, 14 * mm, 15 * mm]))
S.append(Spacer(1, 4))
S.append(Paragraph("Read the pressure columns with care: several batters have fewer than 10 pressure innings, so their pressure strike rates are indicative, not conclusive. "
                   "The index uses the whole profile (quality, consistency and pressure) rather than pressure alone.", small))


S += [PageBreak(), Paragraph("4. Acquisition feasibility (status as of " + F["asOf"] + ")", h2),
      Paragraph("The Top 10 above is the pure pressure ranking. To judge whether Rajasthan Royals can realistically acquire these players, every ranked player was walked in PRI order and given one status. "
                "A player stays on the acquisition shortlist only if status is A or B, his pressure percentile clears the threshold, and RR's purse / overseas-slot check passes. Statuses C to G are skipped and the next-ranked player is considered, until 10 qualify.", body)]
S.append(tbl([["Status", "Meaning"]] + [[k, v] for k, v in STAT.items()], [16 * mm, 158 * mm]))
S += [Spacer(1, 4), Paragraph("Evidence base: the IPL 2027 retention and release lists as reported on " + F["asOf"] + " (the deadline day), cross-checked between two press compilations. An official iplt20.com or BCCI page could not be reached, so these are press-reported lists, not an official download. "
      "No official auction pool exists yet, so no player is status A; released players are B. The old Low / Medium / High release tiers are gone because retention is now known. Pakistani players are marked D because none has been selected in the IPL since 2008 (a long-standing practice; no written rule was found).", small)]
ecol = [8 * mm, 14 * mm, 38 * mm, 18 * mm, 24 * mm, 16 * mm]
def erow(r): return [r["shortlist_rank"], r["original_pri_rank"], r["player"], r["team_2026"] or "-", r["status"] + (" (overseas)" if r["overseas"] == 1 else ""), f1(r["pri_pct"])]
S.append(Paragraph("Eligible Top 10 batters", h3))
S.append(tbl([["#", "PRI rank", "Player", "2026 team", "Status", "PRI"]] + [erow(r) for r in F["eligBat"]], ecol))
S.append(Paragraph("Eligible Top 10 bowlers", h3))
S.append(tbl([["#", "PRI rank", "Player", "2026 team", "Status", "PRI"]] + [erow(r) for r in F["eligBowl"]], ecol))
S.append(Paragraph("Players excluded while walking the ranking", h3))
exrows = [["List", "PRI rank", "Player", "St.", "Reason / evidence"]] + [[r["list"], r["original_pri_rank"], r["player"], r["status"], Paragraph(r["reason"] + ": " + (r["evidence"] or ""), cell)] for r in F["excluded"]]
S.append(tbl(exrows, [16 * mm, 14 * mm, 34 * mm, 8 * mm, 102 * mm]))
S.append(Spacer(1, 4))
_nb = sum(1 for r in F["excluded"] if r["list"] == "Batters"); _nw = sum(1 for r in F["excluded"] if r["list"] == "Bowlers")
S.append(Paragraph(f"Result: the official lists remove {_nb} batters and {_nw} bowlers from the ranking (almost every high-ranked batter was retained, which is why the eligible batter list starts at PRI rank {F['eligBat'][0]['original_pri_rank']}). "
                   f"Both eligible lists have 10 names, all status B. RR can add at most {CON['free_overseas_slots']} overseas players, yet {F['eligOverseas']['bat']} of the 10 eligible batters and {F['eligOverseas']['bowl']} of the 10 eligible bowlers are overseas, so these lists are a ranking, not a buy list.", body))
S.append(Paragraph("Acquisition priority board", h3))
S.append(Paragraph("Score = PRI x availability weight (status A 1.0, status B 0.8) x 0.85 for overseas players (RR can add at most 3 overseas players). These weights are judgement values.", small))
bb = [["#", "Player", "PRI rank", "Team", "Status", "Score"]]
for lst, title in (("Batters", "Batters"), ("Bowlers", "Bowlers")):
    S.append(Paragraph(title, h3))
    S.append(tbl(bb + [[r["acq_rank"], r["player"], r["original_pri_rank"], r["team_2026"], r["status"], f1(r["afs"])] for r in F["board"] if r["list"] == lst], [8 * mm, 44 * mm, 18 * mm, 20 * mm, 24 * mm, 16 * mm]))

S += [PageBreak(), Paragraph("5. Rajasthan Royals context", h2)]
ev = D["tenure"]
S.append(Paragraph(f"RR won {M['rr_wins']} of {M['rr_matches']} matches in the pack ({M['rr_wins'] / M['rr_matches'] * 100:.1f}%). "
                   f"Under the {ev[0]['era_name']} ({ev[0]['seasons']}) they won {ev[0]['win_rate_pct']:.1f}% with a batting strike rate of {f1(ev[0]['batting_sr'])} and economy {f2(ev[0]['bowling_economy'])}; "
                   f"in the {ev[1]['era_name']} ({ev[1]['seasons']}) they won {ev[1]['win_rate_pct']:.1f}% with a strike rate of {f1(ev[1]['batting_sr'])} but economy of {f2(ev[1]['bowling_economy'])}. "
                   "The team scores faster but concedes more, which is why the squad gaps below lean on bowling as well as batting.", body))
core = ", ".join(f"{s['player_name']}" for s in D["squad"])
S.append(Paragraph(f"<b>RR squad for IPL 2027 ({len(D['squad'])} players, retention lists of {F['asOf']}; Shami and M Siddharth traded in from LSG, Curran traded to LSG):</b> {core}. RR hold {sum(1 for s in D['squad'] if s['nationality']=='Overseas')} overseas players (cap 8, so {CON['free_overseas_slots']} free), have Rs {CON['purse_cr']} crore of purse and {CON['open_slots']} open slots. Released: {', '.join(r['player_name'] for r in F['rrReleased'] if r['action']=='Released')}.", body))
rows = [["Gap", "What RR needs"]] + [[Paragraph("<b>" + g["gap_id"] + "</b> " + g["gap_name"], cell), Paragraph(g["tactical_need"], cell)] for g in D["gaps"]]
S += [Spacer(1, 3), tbl(rows, [62 * mm, 112 * mm])]

S += [PageBreak(), Paragraph("6. Recommended targets and squad fit", h2),
      Paragraph("Targets are the best candidates for each gap with a Combined Auction Fit Score (CAFS) of 70 or more and status A or B, who then pass RR's purse and overseas-slot check (below). CAFS = 0.40 PRI + 0.30 CPAS + 0.20 SGF + 0.10 VF (section 2.6). "
                "Gaps with no candidate above 70 are left open rather than filled with a weak name.", body), Spacer(1, 4)]
for t in picks:
    bat, pl, n = pool_row(t); g = gaps[t["gap"]]
    if pl:
        pc = pl["pressure_innings_count"] if bat else pl["pressure_match_count"]
        if bat:
            ev_txt = f"Ranked #{pl['official_rank']} of {n} batters under pressure; strike rate {f1(pl['strike_rate'])} overall, {f1(pl['pressure_sr'])} under pressure ({pc} pressure innings)."
        else:
            ev_txt = f"Ranked #{pl['official_rank']} of {n} bowlers under pressure; economy {f2(pl['economy'])} overall, {f2(pl['pressure_econ'])} under pressure; {pl['total_wickets']} wickets."
        risks = []
        if pl["sample_reliability"] != "High": risks.append(f"{pl['sample_reliability']} sample size")
        if pc < 10: risks.append(f"only {pc} pressure {'innings' if bat else 'matches'}")
        rbv = D["robust"]["bat" if bat else "bowl"].get(str(t["player_id"]))
        if rbv is not None and rbv < 70: risks.append(f"rank is weight-sensitive (Top 10 in {rbv:.0f}% of re-weightings)")
    else:
        ev_txt, risks = "No pressure statistics in the scored pool.", []
    if t["nationality"] == "Overseas": risks.append(f"uses 1 of RR's {CON['free_overseas_slots']} free overseas slots")
    risks.append(("released by " + t["team_2026"] if t["team_2026"] else "reported registered") + f"; not yet in an official auction pool (status {t['status']}); price not modelled" + (f"; last price Rs {t['price_cr']} cr" if t.get("price_cr") else ""))
    block = [Paragraph(f"<b>{t['player_name']}</b> | {t['primary_role']}, {t['nationality']} | CAFS {f1(t['cafs_score'])} | fills {t['gap']} ({g['gap_name']})", h3),
             Paragraph(f"<b>Evidence.</b> {ev_txt} PRI {f1(t['pri_score'])}, coach fit {f1(t['cpas_score'])}, gap fit {f1(t['sgf_score'])}.", body),
             Paragraph(f"<b>How he strengthens RR.</b> {g['tactical_need']}", body),
             Paragraph(f"<b>Risks.</b> {'; '.join(risks) if risks else 'None flagged by the data'}.", body), Spacer(1, 3)]
    S.append(KeepTogether(block))
open_gaps = [g for g in gaps if not any(p["gap"] == g for p in picks)]
if open_gaps:
    S.append(Paragraph("<b>Gaps with no candidate above CAFS 70:</b> " + ", ".join(f"{g} ({gaps[g]['gap_name']})" for g in open_gaps) +
                       ". These need a wider search or a trade rather than a name from this list.", body))

S.append(Paragraph("RR feasibility check (mandatory)", h3))
S.append(Paragraph(f"RR have Rs {CON['purse_cr']} crore, {CON['open_slots']} open squad slots and {CON['free_overseas_slots']} free overseas slots ({8 - CON['free_overseas_slots']} of 8 used). "
                   f"A target fails if it needs an overseas slot RR cannot free, or if last disclosed prices clearly exceed the purse (more than {round((CON['purse_tolerance'] - 1) * 100)}% over). "
                   f"Last prices are not 2027 forecasts and most released players have none disclosed here, so the purse test is weak and the overseas test binds. The {len(picks)} picks use {CON['picks_overseas']} of {CON['free_overseas_slots']} overseas slots.", body))
if CON["fails"]:
    S.append(tbl([["Player", "Gap", "CAFS", "Why it fails RR feasibility"]] + [[f["player"], f["gap"], f1(f["cafs"]), Paragraph(f["reason"], cell)] for f in CON["fails"]], [38 * mm, 18 * mm, 14 * mm, 104 * mm]))
    S.append(Spacer(1, 4))

S += [Paragraph("7. Limitations", h2)]
c = [v for v in D["validation"] if "Correlation" in v["test_category"]]
for t in [f"The coach-alignment score overlaps heavily with the pressure index (correlation {c[0]['measured_value']} for batters, {c[1]['measured_value']} for bowlers; our own test required below 0.85). "
          "The shortlist is therefore mainly a pressure-reliability ranking filtered by squad need, not an independent second opinion.",
          "Pressure situations are rare (about 8% of balls), so individual pressure samples are small. Players with few pressure innings are flagged.",
          "The source scoring file tags every bowler to the pace gap, and its spin flag compares against lowercase 'spin' while the data says 'Spin', so the spin adjustments never apply. "
          "This understates gap-fit scores for spinners against the spin gap and overstates them against the pace gap. "
          "We assigned bowlers to the pace or spin gap by bowling type; CAFS values are unchanged.",
                    "Nationality and overseas status come from the verified status list where a player is listed, otherwise from the national team in the pack's T20I series; unlisted players are status G (unverified) and are never recommended.",
          "Availability comes from the IPL 2027 retention and release lists as reported on " + F["asOf"] + ", not the data pack. An official iplt20.com or BCCI list could not be reached, and the official auction pool is not out until " + F["auction"]["final_register"] + "; re-check then (B becomes A). Auction prices are not modelled; the purse check uses last disclosed prices only.",
          "Coaching-staff philosophies (Dravid, Sangakkara, Bond, Rathour) were translated into measurable proxies; these are judgement calls, not facts from the data."]:
    S.append(Paragraph(t, bul, bulletText="•"))
SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=16 * mm,
                  title="SupeRR Selector Season 2 - Round 1: Most Reliable Players Under Pressure", author="SupeRR Selector S2").build(S, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT, OUT.stat().st_size)
