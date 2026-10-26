#!/usr/bin/env python3
"""M3 (release build) — three targeted tests on top of draft2's hurdle model:

  C1  LODES-only employment: drop the ZBP jobs feature (log_jobs) that
      duplicates LODES workplace counts; establishments (business
      counts) stay — they measure a different thing.
  C2  Harmonized registrations: VA excluded (county grain + 2022
      vintage breaks comparability), NY flagged bev_only (its source
      counts battery-electric only) so the model can price the
      definition difference instead of absorbing it as signal.
  C3  + AADT: county-level arterial traffic from FHWA HPMS 2024
      (server-side targeted extract; log max + length-weighted mean
      AADT over f_system 1-3 sections).
  C4  + OSM POIs (only if data/poi_by_tract.csv exists): fuel stations,
      parking, retail, hotels per tract + distance to nearest fuel.

Same protocol as always: county-grouped 5-fold CV, hurdle GBDT.
"""
import json
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, \
    HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error

feat = pd.read_csv("tract_features_m3d2.csv", dtype={"GEOID": str})

# --- AADT county features -------------------------------------------------
aadt = pd.read_csv("data/hpms_aadt_by_county.csv",
                   dtype={"county_fips": str})
amap_max = aadt.set_index("county_fips").max_aadt_art
amap_wavg = aadt.set_index("county_fips").wavg_aadt_art
county = feat.GEOID.str[:5]
feat["log_max_aadt"] = np.log1p(county.map(amap_max))
feat["log_wavg_aadt"] = np.log1p(county.map(amap_wavg))
print(f"AADT coverage: {feat.log_max_aadt.notna().mean():.1%} of tracts")

# --- harmonized registrations ----------------------------------------------
state = feat.GEOID.str[:2]
ev_h = feat.ev_regs2.where(state != "51")          # drop VA (grain/vintage)
feat["ev_regs_h"] = ev_h
feat["log_ev_h"] = np.log1p(ev_h)
feat["ev_per_1000_h"] = 1000 * ev_h / feat.population.replace(0, np.nan)
feat["ev_data_h"] = ev_h.notna().astype(int)
feat["ev_bev_only"] = (state == "36").astype(int)   # NY = BEV-only source

feat.to_csv("tract_features_m3d3.csv", index=False)

EXT = ["log_pop", "log_density", "median_income", "log_jobs", "establishments",
       "log_ev", "ev_per_1000", "ev_data", "dist_road_km", "dcfc_5km",
       "dcfc_10km", "dist_nearest_dcfc_km", "centroid_lat", "centroid_lon",
       "dist_interchange_km", "l2_5km", "dist_nearest_l2_km",
       "dcfc_recent_10km", "years_since_first_dcfc_10km"]
REG = ["log_ev2", "ev_per_1000_v2", "ev_data2"]
LOD = ["log_lodes_work", "lodes_workers_home", "lodes_net_jobs"]
REGH = ["log_ev_h", "ev_per_1000_h", "ev_data_h", "ev_bev_only"]
AADT = ["log_max_aadt", "log_wavg_aadt"]

y = feat.dcfc_ports.values
groups = county.values


def hurdle_oof(cols):
    pred = np.zeros(len(feat))
    for tr, te in GroupKFold(5).split(feat, y, groups):
        Xtr, ytr = feat[cols].iloc[tr], y[tr]
        clf = HistGradientBoostingClassifier(random_state=42)
        clf.fit(Xtr, (ytr > 0).astype(int))
        pos = ytr > 0
        reg = HistGradientBoostingRegressor(random_state=42)
        reg.fit(Xtr[pos], ytr[pos])
        pred[te] = clf.predict_proba(feat[cols].iloc[te])[:, 1] * \
            np.clip(reg.predict(feat[cols].iloc[te]), 0, None)
    return pred


variants = {
    "C0_draft2_full": EXT + REG + LOD,
    "C1_lodes_only_emp": [c for c in EXT if c != "log_jobs"] + REG + LOD,
    "C2_harmonized_regs": [c for c in EXT if c != "log_jobs"] + REGH + LOD,
    "C3_plus_aadt": [c for c in EXT if c != "log_jobs"] + REGH + LOD + AADT,
}
try:
    poi = pd.read_csv("data/poi_by_tract.csv", dtype={"GEOID": str})
    feat = feat.merge(poi, on="GEOID", how="left")
    POI = [c for c in poi.columns if c != "GEOID"]
    variants["C4_plus_osm_poi"] = variants["C3_plus_aadt"] + POI
    print("POI features:", POI)
except FileNotFoundError:
    POI = []
    print("no POI file yet — C4 skipped")

results = {}
for name, cols in variants.items():
    p = hurdle_oof(cols)
    results[name] = {"r2": round(r2_score(y, p), 4),
                     "mae": round(mean_absolute_error(y, p), 4),
                     "n_features": len(cols)}
    print(name, results[name], flush=True)

best_name = max(results, key=lambda k: results[k]["r2"])
best_cols = variants[best_name]
X = feat[best_cols]
clf = HistGradientBoostingClassifier(random_state=42).fit(X, (y > 0).astype(int))
pos = y > 0
reg = HistGradientBoostingRegressor(random_state=42).fit(X[pos], y[pos])
feat["predicted_dcfc_m3d3"] = clf.predict_proba(X)[:, 1] * \
    np.clip(reg.predict(X), 0, None)
cand = feat[feat.dcfc_ports == 0].nlargest(500, "predicted_dcfc_m3d3")[
    ["GEOID", "STATEFP", "COUNTYFP", "NAME", "population", "median_income",
     "ev_regs2", "jobs", "dist_road_km", "dist_nearest_dcfc_km",
     "predicted_dcfc_m3d3"]]
cand.to_csv("candidate_tracts_dcfc_m3d3_top500.csv", index=False)
feat.to_csv("tract_features_m3d3_scored.csv", index=False)
results["best_variant"] = best_name
json.dump(results, open("m3_draft3_results.json", "w"), indent=1)
print("BEST:", best_name)
print(cand.head(10).to_string(index=False))
