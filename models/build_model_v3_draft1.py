#!/usr/bin/env python3
"""M3_draft1 — improvements from data already on disk only.

Adds derived features:
  * centroid lat/lon (regional regimes)
  * distance to nearest primary-road x primary-road intersection
    (interchange proxy)
  * Level 2 supply context: L2 ports within 5 km (excl. own tract),
    distance to nearest out-of-tract L2 station
  * DCFC vintage within 10 km (excl. own tract): ports opened in the last
    3 years, years since the first DCFC opened nearby
Model variants under identical county-grouped 5-fold CV:
  A0 M2 features + squared loss (continuity)   A1 M2 + Poisson
  A2 extended + squared                        A3 extended + Poisson
  A4 hurdle on extended (classifier x regressor-on-positives)
Then a randomized hyperparameter search (3-fold) on the best loss family,
final 5-fold OOF score for the tuned config, and a full-data refit that
produces the M3_draft1 candidate ranking.
"""
import json
import time
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sklearn.ensemble import HistGradientBoostingRegressor, \
    HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.neighbors import BallTree

D = "data/"
t0 = time.time()
feat = pd.read_csv("tract_features_v2.csv", dtype={"GEOID": str})
feat["log_pop"] = np.log1p(feat.population)
feat["log_density"] = np.log1p(feat.pop_density)
feat["log_jobs"] = np.log1p(feat.jobs)
feat["log_ev"] = np.log1p(feat.ev_regs)
feat = feat.set_index("GEOID")

# --- centroids ---------------------------------------------------------------
tg = gpd.read_file(D + "cb_2023_us_tract_500k.zip")[["GEOID", "geometry"]]
tg["GEOID"] = tg.GEOID.astype(str)
cent = tg.set_index("GEOID").geometry.to_crs("EPSG:4326").centroid
feat["centroid_lat"] = cent.y.reindex(feat.index)
feat["centroid_lon"] = cent.x.reindex(feat.index)
clat = feat.centroid_lat.values
clon = feat.centroid_lon.values

# --- interchange proxy: primary-road crossings -------------------------------
roads = gpd.read_file(D + "tl_2023_us_primaryroads.zip")[["geometry"]] \
    .to_crs("EPSG:5070")
geoms = roads.geometry.values
sidx = roads.sindex
pts = []
for i, gline in enumerate(geoms):
    for j in sidx.query(gline, predicate="intersects"):
        if j <= i:
            continue
        inter = gline.intersection(geoms[j])
        if inter.is_empty:
            continue
        stack = [inter] if inter.geom_type == "Point" else \
            list(inter.geoms) if hasattr(inter, "geoms") else []
        for p in stack:
            if p.geom_type == "Point":
                pts.append(p)
            elif p.geom_type == "MultiPoint":
                pts.extend(p.geoms)
print(f"road crossings found: {len(pts):,}", flush=True)
cross = gpd.GeoDataFrame(geometry=pts, crs="EPSG:5070").to_crs("EPSG:4326")
ctree = BallTree(np.radians(np.c_[cross.geometry.y, cross.geometry.x]),
                 metric="haversine")
d, _ = ctree.query(np.radians(np.c_[clat, clon]), k=1)
feat["dist_interchange_km"] = d[:, 0] * 6371.0

# --- station arrays -----------------------------------------------------------
st = pd.read_csv(D + "nlr_elec_public_stations.csv", low_memory=False)
for c in ["ev_level2_evse_num", "ev_dc_fast_num"]:
    st[c] = pd.to_numeric(st[c], errors="coerce").fillna(0)
st_pts = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.longitude,
                                                          st.latitude),
                          crs="EPSG:4326")
st_join = gpd.sjoin(st_pts, tg, how="left", predicate="within")
st["tract"] = st_join.GEOID.values
st["open_year"] = pd.to_datetime(st.open_date, errors="coerce").dt.year

# L2 context
l2 = st[st.ev_level2_evse_num > 0]
ltree = BallTree(np.radians(l2[["latitude", "longitude"]]), metric="haversine")
idx5 = ltree.query_radius(np.radians(np.c_[clat, clon]), r=5 / 6371.0)
feat["l2_5km"] = [l2.ev_level2_evse_num.values[i].sum() if len(i) else 0
                  for i in idx5]
feat["l2_5km"] = feat.l2_5km - feat.l2_ports  # exclude own tract
dist, ind = ltree.query(np.radians(np.c_[clat, clon]), k=5)
own = l2.tract.values
feat["dist_nearest_l2_km"] = [
    next((dd * 6371.0 for dd, ii in zip(rd, ri) if own[ii] != g), np.nan)
    for rd, ri, g in zip(dist, ind, feat.index)]

# DCFC vintage within 10 km
dc = st[st.ev_dc_fast_num > 0].copy()
dtree = BallTree(np.radians(dc[["latitude", "longitude"]]), metric="haversine")
idx10 = dtree.query_radius(np.radians(np.c_[clat, clon]), r=10 / 6371.0)
own_dc = dc.set_index("tract").ev_dc_fast_num
recent, since_first = [], []
for i, g in zip(idx10, feat.index):
    sub = dc.iloc[i]
    sub = sub[sub.tract != g]
    if not len(sub):
        recent.append(0)
        since_first.append(np.nan)
        continue
    recent.append(sub.loc[sub.open_year >= 2023, "ev_dc_fast_num"].sum())
    ymin = sub.open_year.min()
    since_first.append(2026 - ymin if pd.notna(ymin) else np.nan)
feat["dcfc_recent_10km"] = recent
feat["years_since_first_dcfc_10km"] = since_first

feat = feat.reset_index()
feat.to_csv("tract_features_m3d1.csv", index=False)
print(f"features ready {time.time()-t0:.0f}s", flush=True)

# --- model comparison ----------------------------------------------------------
M2 = ["log_pop", "log_density", "median_income", "log_jobs", "establishments",
      "log_ev", "ev_per_1000", "ev_data", "dist_road_km", "dcfc_5km",
      "dcfc_10km", "dist_nearest_dcfc_km"]
EXT = M2 + ["centroid_lat", "centroid_lon", "dist_interchange_km", "l2_5km",
            "dist_nearest_l2_km", "dcfc_recent_10km",
            "years_since_first_dcfc_10km"]
y = feat.dcfc_ports.values
groups = feat.GEOID.str[:5].values
gkf = GroupKFold(n_splits=5)


def oof(make, cols):
    pred = np.zeros(len(feat))
    for tr, te in gkf.split(feat, y, groups):
        m = make()
        m.fit(feat[cols].iloc[tr], y[tr])
        pred[te] = np.clip(m.predict(feat[cols].iloc[te]), 0, None)
    return pred


def oof_hurdle(cols):
    pred = np.zeros(len(feat))
    for tr, te in gkf.split(feat, y, groups):
        Xtr, ytr = feat[cols].iloc[tr], y[tr]
        clf = HistGradientBoostingClassifier(random_state=42)
        clf.fit(Xtr, (ytr > 0).astype(int))
        pos = ytr > 0
        reg = HistGradientBoostingRegressor(random_state=42)
        reg.fit(Xtr[pos], ytr[pos])
        pred[te] = clf.predict_proba(feat[cols].iloc[te])[:, 1] * \
            np.clip(reg.predict(feat[cols].iloc[te]), 0, None)
    return pred


results = {}
variants = [
    ("A0_m2_squared", lambda: HistGradientBoostingRegressor(random_state=42), M2),
    ("A1_m2_poisson", lambda: HistGradientBoostingRegressor(loss="poisson", random_state=42), M2),
    ("A2_ext_squared", lambda: HistGradientBoostingRegressor(random_state=42), EXT),
    ("A3_ext_poisson", lambda: HistGradientBoostingRegressor(loss="poisson", random_state=42), EXT),
]
for name, make, cols in variants:
    p = oof(make, cols)
    results[name] = {"r2": round(r2_score(y, p), 4),
                     "mae": round(mean_absolute_error(y, p), 4)}
    print(name, results[name], f"({time.time()-t0:.0f}s)", flush=True)
p = oof_hurdle(EXT)
results["A4_ext_hurdle"] = {"r2": round(r2_score(y, p), 4),
                            "mae": round(mean_absolute_error(y, p), 4)}
print("A4_ext_hurdle", results["A4_ext_hurdle"], flush=True)

# --- tuning on the best loss family ---------------------------------------------
best_plain = max((k for k in results if k != "A4_ext_hurdle"),
                 key=lambda k: results[k]["r2"])
use_poisson = "poisson" in best_plain
print("best plain variant:", best_plain, "-> tuning",
      "poisson" if use_poisson else "squared", flush=True)
rng = np.random.RandomState(42)
configs = []
for _ in range(18):
    configs.append({
        "max_iter": int(rng.choice([300, 500, 800])),
        "learning_rate": float(rng.choice([0.03, 0.05, 0.08])),
        "max_leaf_nodes": int(rng.choice([15, 31, 63, 127])),
        "min_samples_leaf": int(rng.choice([20, 40, 80])),
        "l2_regularization": float(rng.choice([0.0, 0.1, 1.0])),
    })
gkf3 = GroupKFold(n_splits=3)
best_cfg, best_r2 = None, -1
for cfg in configs:
    pred = np.zeros(len(feat))
    for tr, te in gkf3.split(feat, y, groups):
        m = HistGradientBoostingRegressor(
            loss="poisson" if use_poisson else "squared_error",
            random_state=42, **cfg)
        m.fit(feat[EXT].iloc[tr], y[tr])
        pred[te] = np.clip(m.predict(feat[EXT].iloc[te]), 0, None)
    r2 = r2_score(y, pred)
    print("cfg", cfg, "3fold R2", round(r2, 4), flush=True)
    if r2 > best_r2:
        best_r2, best_cfg = r2, cfg
pred = oof(lambda: HistGradientBoostingRegressor(
    loss="poisson" if use_poisson else "squared_error",
    random_state=42, **best_cfg), EXT)
results["M3_draft1_tuned"] = {"r2": round(r2_score(y, pred), 4),
                              "mae": round(mean_absolute_error(y, pred), 4),
                              "config": best_cfg,
                              "loss": "poisson" if use_poisson else "squared_error"}
print("M3_draft1_tuned", results["M3_draft1_tuned"], flush=True)

# --- full fit + candidates -------------------------------------------------------
final = HistGradientBoostingRegressor(
    loss="poisson" if use_poisson else "squared_error",
    random_state=42, **best_cfg)
final.fit(feat[EXT], y)
feat["predicted_dcfc_m3d1"] = np.clip(final.predict(feat[EXT]), 0, None)
cand = feat[feat.dcfc_ports == 0].nlargest(500, "predicted_dcfc_m3d1")[
    ["GEOID", "STATEFP", "COUNTYFP", "NAME", "population", "median_income",
     "ev_regs", "jobs", "dist_road_km", "dist_nearest_dcfc_km",
     "predicted_dcfc_m3d1"]]
cand.to_csv("candidate_tracts_dcfc_m3d1_top500.csv", index=False)
feat.to_csv("tract_features_m3d1_scored.csv", index=False)
json.dump(results, open("m3_draft1_results.json", "w"), indent=1)
print("DONE", json.dumps(results, indent=1))
