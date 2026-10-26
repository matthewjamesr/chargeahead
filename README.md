# ChargeAhead

**Open, data-driven models for deciding where EV charging should go next** — tract-level demand prediction for DC fast charging, built entirely on public data.

🌐 **Live dashboard & results:** https://matthewjamesr.github.io/chargeahead/

## What this is

ChargeAhead is an open research project in applied geospatial machine learning. It censuses every public charging station in the United States, builds features for all ~85,000 census tracts from public datasets, trains demand models under **county-grouped spatial cross-validation** (the honest way to validate a map), and publishes ranked lists of underserved tracts — with limitations stated as prominently as results.

Current flagship: **Tract Demand GBDT v2** — gradient-boosted trees predicting DC fast-charge ports per census tract.

| Model | Features | Spatial-CV R² | MAE (ports/tract) |
|---|---|---|---|
| M0 | Population, density, income | 0.007 | 1.61 |
| **M2** | + EV registrations, jobs, establishments, highway distance, supply context | **0.209** | **1.33** |

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
