# ChargeAhead

**Open, data-driven models for deciding where EV charging should go next** — tract-level demand prediction for DC fast charging, built entirely on public data.

🌐 **Live dashboard & results:** https://matthewjamesr.github.io/chargeahead/

## What this is

ChargeAhead is an open research project in applied geospatial machine learning. It censuses every public charging station in the United States, builds features for all ~85,000 census tracts from public datasets, trains demand models under **county-grouped spatial cross-validation** (the honest way to validate a map), and publishes ranked lists of underserved tracts — with limitations stated as prominently as results.

Current flagship: **Tract Demand Hurdle GBDT, v3 draft 3** — a two-stage model (classifier for "any DCFC at all" × regressor for "how many") predicting DC fast-charge ports per census tract.

| Model | Change | Spatial-CV R² | MAE (ports/tract) |
|---|---|---|---|
| M0 | Population, density, income only | 0.007 | 1.61 |
| M2 | Single regressor, full v2 feature set | 0.209 | 1.33 |
| M3 draft 1 | Hurdle architecture + derived features (interchanges, L2 context, vintage, coordinates) | 0.281 | 1.26 |
| M3 draft 2 | + LODES workplace flows + EV registrations expanded 2 → 6 states | 0.288 | 1.24 |
| **M3 draft 3** | + AADT arterial traffic (HPMS) + OpenStreetMap POIs (fuel/parking/retail/lodging), ZBP-jobs dedup, harmonized registration definitions | **0.335** | **1.17** |

Notes from the v3 experiments: Poisson loss collapsed on this target (R² −2.2) and is not used; hyperparameter tuning did not beat defaults for the hurdle stages; the registration expansion added no national R² (LODES carried draft 2's gain) — all reported as found in `results/m3_draft2_results.json`.

## Repository layout

| Path | Contents |
|---|---|
| `docs/` | The GitHub Pages site (landing page + interactive results dashboard) |
| `scripts/fetch_nlr_stations.py` | Pull the station census from the NLR Alternative Fuel Stations API (free key) |
| `models/build_model_v1.py` | v1: tract features from demographics; all-ports target |
| `models/build_model_v2.py` | v2: full feature set; DC fast-charge target; spatial CV; candidate ranking |
| `results/` | Feature tables and ranked candidate tract lists (CSV) |
| `data/DATA_SOURCES.md` | Every dataset used, where to get it, and how it is joined |

## Quick start

```bash
export NLR_API_KEY=...            # free key: https://developer.nlr.gov/signup/
python scripts/fetch_nlr_stations.py --out stations.jsonl
# download the Census/ACS/TIGER/ZBP and state registration files per data/DATA_SOURCES.md
pip install geopandas scikit-learn pandas
python models/build_model_v2.py
```

## Data sources (all public)

NLR Alternative Fuel Stations API · U.S. Census ACS 2023 5-year · TIGER/Line 2023 · ZIP Business Patterns 2022 · Washington DOL EV Population Data · California DMV Vehicle Fuel Type Counts. Details and links in `data/DATA_SOURCES.md`.

## Model families (roadmap)

- **Tract Demand GBDT** — live (v2, this repo)
- **Greenfield Discovery** — in development: demand isolated from network clustering
- **Corridor Model** — planned: highway-segment framing for corridor charging
- **Utilization Model** — blocked on open station-level utilization data

## License

MIT — see `LICENSE`. Data remains under its publishers' respective terms (all are public/open datasets).
