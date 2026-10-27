# ChargeAhead

**Open, data-driven models for deciding where EV charging should go next** — tract-level demand prediction for DC fast charging, built entirely on public data.

🌐 **Live dashboard & results:** https://matthewjamesr.github.io/chargeahead/

## What this is

ChargeAhead is an open research project in applied geospatial machine learning. It censuses every public charging station in the United States, builds features for all ~85,000 census tracts from public datasets, trains demand models under **county-grouped spatial cross-validation** (the honest way to validate a map), and publishes ranked lists of underserved tracts — with limitations stated as prominently as results.

Current flagship: **Tract Demand Hurdle GBDT — M4** — a LightGBM two-stage hurdle ensemble (classifier for "any DCFC at all" × Tweedie regressor for "how many", 3 seeds) predicting DC fast-charge ports per census tract, with state target encoding computed inside training folds.

| Model | Change | Spatial-CV R² | MAE (ports/tract) |
|---|---|---|---|
| M0 | Population, density, income only | 0.007 | 1.61 |
| M2 | Single regressor, full v2 feature set | 0.209 | 1.33 |
| M3 | Hurdle architecture + derived features, LODES workplace flows, EV registrations (6 states, harmonized), AADT arterial traffic (HPMS), OpenStreetMap POIs (fuel/parking/retail/lodging) | 0.335 | 1.17 |
| **M4** | M3 + nationwide POI coverage with 1/3/5 km buffer & density features, Tweedie sizing, tract-level AADT, state target encoding, EV-corridor proximity (NTAD) | **0.365** | **0.99** |

Findings baked into M3: Poisson loss collapsed on this target (R² −2.2) and is not used; hyperparameter tuning did not beat defaults for the hurdle stages; expanding registration coverage from 2 to 6 states added no national R² on its own, while LODES employment and OpenStreetMap land use carried the gains. M4 findings: gains flattened across the final drafts (each under +0.005 R²); LODES job-growth trends and Microsoft building footprints (141.8M buildings aggregated per tract) were tested and not shipped — footprints produced the best MAE of any variant (0.983 single-seed) at a tied R², and footprint substitution for POI features was clearly worse (0.310). Development iterations are worked locally and are not published; this repo carries released models only. Trained artifacts live in `models/` (joblib dump + model card per release); the pipelines that built them live in `scripts/`.

## Repository layout

| Path | Contents |
|---|---|
| `docs/` | The GitHub Pages site (landing page + interactive results dashboard) |
| `scripts/fetch_nlr_stations.py` | Pull the station census from the NLR Alternative Fuel Stations API (free key) |
| `models/` | Released model artifacts only: joblib dump + model card per release (M3, M4) |
| `scripts/` | The build pipelines: fetch, parse, feature builders, and `build_model_m4.py` (current release) |
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
