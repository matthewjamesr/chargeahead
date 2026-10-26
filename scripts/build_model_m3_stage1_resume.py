#!/usr/bin/env python3
"""Resume M3_draft1 after a runtime restart killed the tuning phase.
Verified results from the first run's log are carried in; this script
tunes the hurdle model (the best variant), scores it 5-fold OOF, refits
on all data, and writes the candidate list + results JSON.
"""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, \
    HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error

feat = pd.read_csv("tract_features_m3d1.csv", dtype={"GEOID": str})
EXT = ["log_pop", "log_density", "median_income", "log_jobs", "establishments",
       "log_ev", "ev_per_1000", "ev_data", "dist_road_km", "dcfc_5km",
       "dcfc_10km", "dist_nearest_dcfc_km", "centroid_lat", "centroid_lon",
       "dist_interchange_km", "l2_5km", "dist_nearest_l2_km",
       "dcfc_recent_10km", "years_since_first_dcfc_10km"]
y = feat.dcfc_ports.values
groups = feat.GEOID.str[:5].values


def hurdle_oof(cols, clf_kw, reg_kw, n_splits=5):
    pred = np.zeros(len(feat))
    for tr, te in GroupKFold(n_splits).split(feat, y, groups):
        Xtr, ytr = feat[cols].iloc[tr], y[tr]
        clf = HistGradientBoostingClassifier(random_state=42, **clf_kw)
        clf.fit(Xtr, (ytr > 0).astype(int))
        pos = ytr > 0
        reg = HistGradientBoostingRegressor(random_state=42, **reg_kw)
        reg.fit(Xtr[pos], ytr[pos])
        pred[te] = clf.predict_proba(feat[cols].iloc[te])[:, 1] * \
            np.clip(reg.predict(feat[cols].iloc[te]), 0, None)
    return pred


results = {
    "A0_m2_squared": {"r2": 0.2094, "mae": 1.3262},
    "A1_m2_poisson": {"r2": -2.2487, "mae": 1.3762},
    "A2_ext_squared": {"r2": 0.2350, "mae": 1.3095},
    "A3_ext_poisson": {"r2": -0.5081, "mae": 1.3332},
    "A4_ext_hurdle_default": {"r2": 0.2811, "mae": 1.2606},
}

grids = [
    ({}, {}),
    ({"max_iter": 300, "max_leaf_nodes": 31, "learning_rate": 0.06},
     {"max_iter": 500, "max_leaf_nodes": 31, "learning_rate": 0.05,
      "min_samples_leaf": 40}),
    ({"max_iter": 500, "max_leaf_nodes": 63, "learning_rate": 0.05},
     {"max_iter": 800, "max_leaf_nodes": 63, "learning_rate": 0.03,
      "min_samples_leaf": 40}),
    ({"max_iter": 300, "max_leaf_nodes": 127, "learning_rate": 0.06},
     {"max_iter": 500, "max_leaf_nodes": 127, "learning_rate": 0.05,
      "min_samples_leaf": 20}),
]
best = None
for i, (ck, rk) in enumerate(grids):
    p = hurdle_oof(EXT, ck, rk, n_splits=3)
    r2 = r2_score(y, p)
    print(f"hurdle grid {i}: 3fold R2={r2:.4f} MAE={mean_absolute_error(y, p):.4f}",
          flush=True)
    if best is None or r2 > best[0]:
        best = (r2, ck, rk)
_, ck, rk = best
p = hurdle_oof(EXT, ck, rk, n_splits=5)
results["M3_draft1_hurdle_tuned"] = {
    "r2": round(r2_score(y, p), 4), "mae": round(mean_absolute_error(y, p), 4),
    "clf": ck, "reg": rk}
print("M3_draft1_hurdle_tuned", results["M3_draft1_hurdle_tuned"], flush=True)

X = feat[EXT]
clf = HistGradientBoostingClassifier(random_state=42, **ck).fit(X, (y > 0).astype(int))
pos = y > 0
reg = HistGradientBoostingRegressor(random_state=42, **rk).fit(X[pos], y[pos])
feat["predicted_dcfc_m3d1"] = clf.predict_proba(X)[:, 1] * \
    np.clip(reg.predict(X), 0, None)
cand = feat[feat.dcfc_ports == 0].nlargest(500, "predicted_dcfc_m3d1")[
    ["GEOID", "STATEFP", "COUNTYFP", "NAME", "population", "median_income",
     "ev_regs", "jobs", "dist_road_km", "dist_nearest_dcfc_km",
     "predicted_dcfc_m3d1"]]
cand.to_csv("candidate_tracts_dcfc_m3d1_top500.csv", index=False)
feat.to_csv("tract_features_m3d1_scored.csv", index=False)
json.dump(results, open("m3_draft1_results.json", "w"), indent=1)
print("DONE", json.dumps(results, indent=1))
print(cand.head(10).to_string(index=False))
