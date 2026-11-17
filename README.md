# Who Delivers Under Pressure? Rajasthan Royals, IPL 2027

**SupeRR Selector Season 2: Help Shape Rajasthan Royals' IPL 2027 Auction Strategy**
Round 1: Identify the Most Reliable Players Under Pressure

**[Open the interactive dashboard](https://lakshmikanthan07.github.io/rr-selector-dashboard/)** | **[Read the report (PDF)](RR_IPL2027_Pressure_Reliability_Report.pdf)**

---

## Summary

We scored **311 batters and 249 bowlers** on **194,014 ball-by-ball deliveries** from 883 IPL and T20I matches (2022 onwards) and ranked them by a **Pressure Reliability Index (PRI)**: a 0-100 score that rewards players who stay effective, and consistent, in high-pressure match situations. We then screened 560 player profiles against Rajasthan Royals' squad gaps and the IPL 2027 retention/release lists of 17 Nov 2026 to produce **4 recommended auction targets**. The Top 10 tables below are the pure Round 1 data ranking: retention and availability are applied separately.

### Top 10 most reliable batters under pressure

| # | Batter | PRI | | # | Bowler | PRI |
|---|---|---|---|---|---|---|
| 1 | Phil Salt | 85.4 | | 1 | Jasprit Bumrah | 76.6 |
| 2 | Jos Buttler | 84.8 | | 2 | Matheesha Pathirana | 74.9 |
| 3 | Heinrich Klaasen | 82.8 | | 3 | Arshdeep Singh | 73.4 |
| 4 | Rinku Singh | 82.2 | | 4 | Josh Hazlewood | 73.1 |
| 5 | Naman Dhir | 80.8 | | 5 | Mustafizur Rahman | 71.9 |
| 6 | Suryakumar Yadav | 79.8 | | 6 | Bhuvneshwar Kumar | 71.8 |
| 7 | Tim David | 78.3 | | 7 | Varun Chakravarthy | 70.5 |
| 8 | Namboori Tilak Varma | 78.3 | | 8 | Jofra Archer | 69.8 |
| 9 | Tristan Stubbs | 78.0 | | 9 | Nathan Ellis | 69.8 |
| 10 | Rajat Patidar | 77.0 | | 10 | Haris Rauf | 69.5 |

### Recommended auction targets (status as of 17 Nov 2026)
Picks are released players (status B, the official auction pool is not published until 3 Dec 2026) with CAFS of 70 or more that pass RR's purse (Rs 27.05 cr) and overseas-slot check (3 free of 8).

| Gap in the RR squad | Targets |
|---|---|
| Explosive opening partner | no realistic candidate above CAFS 70 |
| Middle-order spin counter and chase finisher | Pathum Nissanka, Nitish Rana (Bethell and Towhid Hridoy fail the overseas-slot check) |
| High-pace death-overs bowler | Matheesha Pathirana, Mustafizur Rahman (Boult, Taskin Ahmed, Hasan Mahmud fail the overseas-slot check) |
| Attacking spinner | none (Hasaranga fails the overseas-slot check) |
| Lower-order all-rounder | no candidate cleared the quality bar |

The dashboard and report also show an **eligible Top 10** (original PRI order, released players only): batters Nissanka, Towhid Hridoy, Bethell, Linde, Nitish Rana, Hetmyer, Lomror, Tripathi, Short, Wadhera; bowlers Pathirana, Mustafizur, Hasaranga, Boult, Taskin Ahmed, Avesh Khan, Starc, Muzarabani, Deshpande, Hasan Mahmud.

Each pick has its evidence, squad fit and risks in the report and on the dashboard.

**Availability caveats:** the lists are press-reported (an official IPL/BCCI list could not be reached); nobody is yet in an official auction pool, so no player is status A; Bangladesh players are only reported as registered; most released players have no disclosed price, so the purse test is weak.

## How it works

1. **Pressure, per delivery.** A 0-1 index combines required run rate (40%), wickets remaining (25%), innings stage (20%) and, in the first innings, the deficit against a par run rate (15%). Balls scoring 0.50 or more count as pressure balls (about 8% of all deliveries, mostly in the death overs). Bowlers have a matching bowling-pressure index.
2. **Player score.** Seven components: overall quality, consistency, performance under pressure, consistency under pressure, plus boundary, strike-rotation and acceleration for batters, or wicket quality, dot balls and economy control for bowlers. Pressure performance and consistency carry 40% of the weight.
3. **Small samples are shrunk.** Quality and consistency are pulled toward the population mean with weight n / (n + 15), so a few good games cannot top the list.
4. **Stress test.** Every player is re-ranked under 2,000 random re-weightings. The dashboard shows how often each Top 10 name stays in the Top 10 (for example, 6 of 10 batters and 6 of 10 bowlers do so in at least 90% of trials).
5. **Auction fit.** `CAFS = 0.40 PRI + 0.30 coach-alignment + 0.20 squad-gap fit + 0.10 versatility`.

All formulas, with their weights and cut-offs, are in section 2 of the report.

## Limitations

- Pressure situations are rare, so individual pressure samples are small. Players with few pressure innings are flagged.
- The coach-alignment score overlaps heavily with PRI (r = 0.93 for batters, 0.90 for bowlers), so the shortlist is mainly a pressure ranking filtered by squad need.
- "Realistic target" means released by a franchise on the 17 Nov 2026 lists (press-reported) and within RR's purse and overseas-slot limits. Prices are not modelled; availability is not in the data pack.
- Nationality is inferred from T20I team appearances, with a name-list fallback for players with no T20I record in the pack.
- The source pipeline tagged every bowler to the pace gap; the dashboard and report assign bowlers by bowling type instead.

## Repository

```
index.html                                   interactive dashboard (single file, no backend)
RR_IPL2027_Pressure_Reliability_Report.pdf   methodology, formulas, rankings, picks, limitations
src/                                         scoring pipeline: pressure, reliability model, coach alignment, auction fit
dashboard/build_data.py                      builds the dashboard data from pipeline outputs
dashboard/template.html                      dashboard template
dashboard/build_report.py                    builds the PDF report
```

## Data and reproducibility

The dataset and all processed data files are deliberately **not published** in this repository. The scripts are included so the method can be inspected; they expect the private data pack under `data/raw/` and pipeline outputs under `SupeRR_Selector_Research/outputs/`, so they will not run from this repository alone. `run_pipeline.py` is the original runner and also expects a `tests/` folder that is not published.

The dashboard embeds aggregated per-player statistics only, not the raw ball-by-ball records.

With the data in place: `pip install -r requirements.txt`, run the pipeline, then `python dashboard/build_data.py` and `python dashboard/build_report.py`.

_Dashboard and report last refreshed 17 Nov 2026._
