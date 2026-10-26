#!/usr/bin/env python3
"""DCFC placement model v2 — target: DC fast-charge ports per census tract.

New features vs v1:
  * EV registrations per tract (WA DOL + CA DMV, ZIP-level distributed to
    tracts by population-density-weighted areal interpolation; CA/WA only,
    NaN elsewhere + indicator)
  * Employment + establishments per tract (Census ZIP Business Patterns
    2022, same ZIP->tract distribution, national)
  * Distance from tract centroid to nearest TIGER primary road (km)
  * Supply context excluding the tract itself: DCFC ports within 5/10 km
    of the centroid, distance to nearest out-of-tract DCFC station
Validation: GroupKFold by county, same as v1. Models compared:
  M0 = v1 demographic features only, M2 = all features.
"""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.neighbors import BallTree

D = "data/"
CRS = "EPSG:5070"  # CONUS Albers (meters); AK/HI/PR distances approximate

# --- geography -------------------------------------------------------------
tracts = gpd.read_file(D + "cb_2023_us_tract_500k.zip")[
    ["GEOID", "ALAND", "geometry"]]
feat = pd.read_csv("tract_features.csv", dtype={"GEOID": str})
feat = feat.set_index("GEOID")
tracts["GEOID"] = tracts.GEOID.astype(str)
g = tracts.set_index("GEOID").loc[feat.index]
g["pop_density"] = feat.population / (g.ALAND / 2.58999e6).replace(0, np.nan)

# --- ZIP-level source tables ----------------------------------------------
# EV registrations (plug-ins, light duty where the source distinguishes)
wa = pd.Series(json.load(open(D + "wa_ev_by_zip.json")), name="ev_regs")
ca_raw = pd.read_csv(D + "ca_vehicle_counts_2025.csv",
                     usecols=["ZIP Code", "Fuel", "Duty", "Vehicles"])
ca = ca_raw[(ca_raw.Fuel.isin(["Battery Electric", "Plug-in Hybrid"]))
            & (ca_raw.Duty == "Light")].groupby(
                ca_raw["ZIP Code"].astype(str).str.zfill(5)).Vehicles.sum()
ca.index.name = "zip"
ev_zip = wa.add(ca.rename("ev_regs"), fill_value=0)
print(f"EV ZIPs: WA {len(wa):,} + CA {ca.notna().sum():,} "
      f"-> plug-ins CA {int(ca.sum()):,} / WA {int(wa.sum()):,}")

zbp = pd.read_csv(D + "zbp22totals.zip", dtype={"zip": str})
zbp["zip"] = zbp.zip.str.zfill(5)
zbp = zbp.set_index("zip")
all_zips = zbp.index.union(ev_zip.index)
zip_tbl = pd.DataFrame(index=all_zips)
zip_tbl["ev_regs"] = ev_zip
zip_tbl["zbp_emp"] = zbp.emp
zip_tbl["zbp_est"] = zbp.est
zip_tbl = zip_tbl.reset_index(names="zip")

# --- distribute ZIP values to tracts (pop-density-weighted areal) ---------
zcta = gpd.read_file(D + "tl_2023_us_zcta520.zip")[["ZCTA5CE20", "geometry"]]
zcta = zcta.rename(columns={"ZCTA5CE20": "zip"}).merge(zip_tbl, on="zip",
                                                       how="inner")
print(f"ZCTAs with source data: {len(zcta):,}")
z = zcta.to_crs(CRS)
t = g.reset_index()[["GEOID", "pop_density", "geometry"]].to_crs(CRS)
alloc_parts = []
zips = z.zip.values
for i in range(0, len(z), 1500):  # chunked: national overlay OOMs otherwise
    chunk = z.iloc[i:i + 1500]
    inter = gpd.overlay(chunk, t, how="intersection")
    inter["w"] = inter.geometry.area * inter.pop_density.fillna(0)
    wsum = inter.groupby("zip").w.transform("sum")
    for col in ["ev_regs", "zbp_emp", "zbp_est"]:
        inter[col + "_t"] = inter[col] * inter.w / wsum.replace(0, np.nan)
    alloc_parts.append(inter.groupby("GEOID")[["ev_regs_t", "zbp_emp_t",
                                               "zbp_est_t"]].sum())
    print(f"overlay chunk {i}-{i + len(chunk)} done", flush=True)
alloc = pd.concat(alloc_parts).groupby(level=0).sum()
feat = feat.join(alloc.rename(columns={"ev_regs_t": "ev_regs",
                                       "zbp_emp_t": "jobs",
                                       "zbp_est_t": "establishments"}))
feat["ev_data"] = feat.ev_regs.notna().astype(int)
feat["ev_per_1000"] = 1000 * feat.ev_regs / feat.population.replace(0, np.nan)

# --- distance to nearest primary road --------------------------------------
roads = gpd.read_file(D + "tl_2023_us_primaryroads.zip")[["geometry"]]
cent = g.copy()
cent["geometry"] = cent.geometry.to_crs(CRS).centroid
near = gpd.sjoin_nearest(cent[["geometry"]], roads.to_crs(CRS),
                         distance_col="d_road_m")
feat["dist_road_km"] = (near.groupby(level=0).d_road_m.min() / 1000).reindex(
    feat.index)

# --- supply context (out-of-tract) -----------------------------------------
st = pd.read_csv(D + "nlr_elec_public_stations.csv", low_memory=False)
st["dcfc"] = pd.to_numeric(st.ev_dc_fast_num, errors="coerce").fillna(0)
pts = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.longitude,
                                                       st.latitude),
                       crs="EPSG:4326")
tg = gpd.read_file(D + "cb_2023_us_tract_500k.zip")[["GEOID", "geometry"]]
tg["GEOID"] = tg.GEOID.astype(str)
pts = gpd.sjoin(pts, tg, how="left", predicate="within")
dc = pts[pts.dcfc > 0].copy()
tree = BallTree(np.radians(dc[["latitude", "longitude"]]), metric="haversine")
clat = g.geometry.to_crs("EPSG:4326").centroid.y
clon = g.geometry.to_crs("EPSG:4326").centroid.x
for r_km, col in [(5, "dcfc_5km"), (10, "dcfc_10km")]:
    idx = tree.query_radius(np.radians(np.c_[clat, clon]), r=r_km / 6371.0)
    feat[col] = [dc.dcfc.values[i].sum() if len(i) else 0 for i in idx]
    feat[col] = feat[col] - feat.dcfc_ports  # exclude own tract's ports
dist, ind = tree.query(np.radians(np.c_[clat, clon]), k=5)
own = dc.GEOID.values
nearest_out = []
for row_d, row_i, geoid in zip(dist, ind, feat.index):
    d = next((dd * 6371.0 for dd, ii in zip(row_d, row_i)
              if own[ii] != geoid), np.nan)
    nearest_out.append(d)
feat["dist_nearest_dcfc_km"] = nearest_out

feat = feat.reset_index()
feat.to_csv("tract_features_v2.csv", index=False)
print(f"v2 feature table: {len(feat):,} tracts")

# --- models -----------------------------------------------------------------
feat["log_pop"] = np.log1p(feat.population)
feat["log_density"] = np.log1p(feat.pop_density)
feat["log_jobs"] = np.log1p(feat.jobs)
feat["log_ev"] = np.log1p(feat.ev_regs)
y = feat.dcfc_ports
groups = feat.GEOID.str[:5]
cv = GroupKFold(n_splits=5)

def evaluate(cols, name):
    X = feat[cols]
    model = HistGradientBoostingRegressor(random_state=42)
    p = cross_val_predict(model, X, y, groups=groups, cv=cv)
    print(f"{name}: R2={r2_score(y, p):.3f} MAE={mean_absolute_error(y, p):.3f}")
    return model.fit(X, y), np.clip(p, 0, None)

m0, _ = evaluate(["log_pop", "log_density", "median_income"], "M0 demographics")
cols2 = ["log_pop", "log_density", "median_income", "log_jobs",
         "establishments", "log_ev", "ev_per_1000", "ev_data",
         "dist_road_km", "dcfc_5km", "dcfc_10km", "dist_nearest_dcfc_km"]
m2, p2 = evaluate(cols2, "M2 full feature set        ")

from sklearn.inspection import permutation_importance
sample = feat.sample(20000, random_state=42)
pi = permutation_importance(m2, sample[cols2], sample.dcfc_ports,
                            n_repeats=3, random_state=42)
print("\nPermutation importance (held-out sample):")
for c, v in sorted(zip(cols2, pi.importances_mean), key=lambda t: -t[1]):
    print(f"  {c:26s} {v:+.3f}")

feat["predicted_dcfc"] = np.clip(m2.predict(feat[cols2]), 0, None)
cand = feat[feat.dcfc_ports == 0].nlargest(500, "predicted_dcfc")[
    ["GEOID", "STATEFP", "COUNTYFP", "NAME", "population", "median_income",
     "ev_regs", "jobs", "dist_road_km", "dist_nearest_dcfc_km",
     "predicted_dcfc"]]
cand.to_csv("candidate_tracts_dcfc_top500.csv", index=False)
print("\nTop 10 zero-DCF tracts by predicted DCFC ports:")
print(cand.head(10).to_string(index=False))
