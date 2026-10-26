#!/usr/bin/env python3
"""M3_draft2 — draft1's hurdle model + the data-hunt haul.

New features:
  * EV registrations, 6 states: WA/CA/NY/MD/PA by ZIP -> tracts via the
    pop-density-weighted ZCTA allocation (5-state subset); VA by county
    (FIPS) -> tracts pro-rata by population. NY is BEV-only by source
    definition; VA is 2022 vintage at county grain — both flagged in the
    model card, neither silently harmonized.
  * LODES8 2023 (LEHD): workplace jobs (WAC C000) and resident workers
    (RAC C000) aggregated block->tract; net importer balance. AK/MI WAC
    are 404 in LODES8 2023 -> NaN there, by design.
Attribution runs: hurdle on EXT (draft1 set), EXT+regs, EXT+LODES,
EXT+all — same county-grouped 5-fold CV throughout.
"""
import glob
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.ensemble import HistGradientBoostingRegressor, \
    HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.inspection import permutation_importance

D = "data/"
feat = pd.read_csv("tract_features_m3d1.csv", dtype={"GEOID": str})
feat = feat.set_index("GEOID")

# --- EV registrations v2 -----------------------------------------------------
zip_frames = []
wa = pd.Series(json.load(open(D + "wa_ev_by_zip.json")), name="ev")
ca_raw = pd.read_csv(D + "ca_vehicle_counts_2025.csv",
                     usecols=["ZIP Code", "Fuel", "Duty", "Vehicles"])
ca = ca_raw[(ca_raw.Fuel.isin(["Battery Electric", "Plug-in Hybrid"]))
            & (ca_raw.Duty == "Light")].groupby(
                ca_raw["ZIP Code"].astype(str).str.zfill(5)).Vehicles.sum()
zip_frames.append(wa)
zip_frames.append(ca.rename("ev"))
for f in ["ny_ev_by_zip.csv", "md_ev_by_zip.csv", "pa_ev_by_zip.csv"]:
    d = pd.read_csv(D + f, dtype={"zip": str})
    zip_frames.append(d.set_index(d.zip.str.zfill(5)).ev_regs.rename("ev"))
ev_zip = pd.concat(zip_frames).groupby(level=0).sum()
print(f"ZIP-level EV states: {len(ev_zip):,} ZIPs, {int(ev_zip.sum()):,} EVs")

tracts = gpd.read_file(D + "cb_2023_us_tract_500k.zip")[
    ["GEOID", "ALAND", "geometry"]]
tracts["GEOID"] = tracts.GEOID.astype(str)
pop = feat.population
tracts = tracts.set_index("GEOID").loc[feat.index]
tracts["pop_density"] = pop / (tracts.ALAND / 2.58999e6).replace(0, np.nan)

zcta = gpd.read_file(D + "tl_2023_us_zcta520.zip")[["ZCTA5CE20", "geometry"]]
zcta = zcta.rename(columns={"ZCTA5CE20": "zip"})
zcta = zcta[zcta.zip.isin(ev_zip.index)]
zcta["ev"] = zcta.zip.map(ev_zip)
z = zcta.to_crs("EPSG:5070")
t = tracts.reset_index()[["GEOID", "pop_density", "geometry"]] \
    .to_crs("EPSG:5070")
alloc_parts = []
zips = z.zip.values
for i in range(0, len(z), 1500):
    inter = gpd.overlay(z.iloc[i:i + 1500], t, how="intersection")
    inter["w"] = inter.geometry.area * inter.pop_density.fillna(0)
    wsum = inter.groupby("zip").w.transform("sum")
    inter["ev_t"] = inter.ev * inter.w / wsum.replace(0, np.nan)
    alloc_parts.append(inter.groupby("GEOID").ev_t.sum())
ev_tract = pd.concat(alloc_parts).groupby(level=0).sum()
feat["ev_regs2"] = ev_tract.reindex(feat.index)

# VA: county totals -> tracts pro-rata by population
va = pd.read_csv(D + "va_ev_by_county.csv", dtype={"fips": str})
va_col = [c for c in va.columns if c.startswith("20")][-1]  # latest year col
va_map = va.set_index(va.fips.str.zfill(5))[va_col]
county = feat.index.str[:5]
county_pop = pop.groupby(county.values).transform("sum")
va_share = va_map.reindex(county).values * (pop / county_pop).values
feat.loc[county.str.startswith("51"), "ev_regs2"] = \
    pd.Series(va_share, index=feat.index)[county.str.startswith("51")]
feat["ev_data2"] = feat.ev_regs2.notna().astype(int)
feat["ev_per_1000_v2"] = 1000 * feat.ev_regs2 / pop.replace(0, np.nan)
feat["log_ev2"] = np.log1p(feat.ev_regs2)
print(f"tracts with EV data: {feat.ev_data2.sum():,} / {len(feat):,}")

# --- LODES ---------------------------------------------------------------------
def lodes_agg(kind):
    parts = []
    for f in sorted(glob.glob(D + f"lodes/*_{kind}_S000_JT00_2023.csv.gz")):
        d = pd.read_csv(f, usecols=[f"{'w' if kind=='wac' else 'h'}_geocode",
                                    "C000"],
                        dtype={"C000": "int32"})
        d.columns = ["geo", "jobs"]
        d["tract"] = d.geo.astype(str).str[:11]
        parts.append(d.groupby("tract").jobs.sum())
    return pd.concat(parts).groupby(level=0).sum()

wac = lodes_agg("wac")
rac = lodes_agg("rac")
feat["lodes_jobs_work"] = wac.reindex(feat.index)
feat["lodes_workers_home"] = rac.reindex(feat.index)
feat["lodes_net_jobs"] = feat.lodes_jobs_work - feat.lodes_workers_home
feat["log_lodes_work"] = np.log1p(feat.lodes_jobs_work)
print(f"LODES work coverage: {feat.lodes_jobs_work.notna().mean():.1%} of tracts")

feat = feat.reset_index()
feat.to_csv("tract_features_m3d2.csv", index=False)

# --- models ----------------------------------------------------------------------
EXT = ["log_pop", "log_density", "median_income", "log_jobs", "establishments",
       "log_ev", "ev_per_1000", "ev_data", "dist_road_km", "dcfc_5km",
       "dcfc_10km", "dist_nearest_dcfc_km", "centroid_lat", "centroid_lon",
       "dist_interchange_km", "l2_5km", "dist_nearest_l2_km",
       "dcfc_recent_10km", "years_since_first_dcfc_10km"]
REG = ["log_ev2", "ev_per_1000_v2", "ev_data2"]
LOD = ["log_lodes_work", "lodes_workers_home", "lodes_net_jobs"]
y = feat.dcfc_ports.values
groups = feat.GEOID.str[:5].values


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


results = {}
for name, cols in [("D2_ext_only", EXT), ("D2_ext_plus_regs", EXT + REG),
                   ("D2_ext_plus_lodes", EXT + LOD),
                   ("M3_draft2_full", EXT + REG + LOD)]:
    p = hurdle_oof(cols)
    results[name] = {"r2": round(r2_score(y, p), 4),
                     "mae": round(mean_absolute_error(y, p), 4)}
    print(name, results[name], flush=True)

ALL = EXT + REG + LOD
X = feat[ALL]
clf = HistGradientBoostingClassifier(random_state=42).fit(X, (y > 0).astype(int))
pos = y > 0
reg = HistGradientBoostingRegressor(random_state=42).fit(X[pos], y[pos])
feat["predicted_dcfc_m3d2"] = clf.predict_proba(X)[:, 1] * \
    np.clip(reg.predict(X), 0, None)

sample = feat.sample(20000, random_state=42)
# permutation importance needs a single estimator; use the regressor stage
# evaluated on positive tracts as the interpretable proxy, plus the
# classifier stage on all tracts.
pi_r = permutation_importance(reg, sample[sample.dcfc_ports > 0][ALL],
                              sample[sample.dcfc_ports > 0].dcfc_ports,
                              n_repeats=3, random_state=42)
print("\nPermutation importance (regressor stage, positive tracts):")
imp = sorted(zip(ALL, pi_r.importances_mean), key=lambda t: -t[1])
for c, v in imp:
    print(f"  {c:28s} {v:+.3f}")
results["importance_regressor_stage"] = {c: round(float(v), 3) for c, v in imp}

cand = feat[feat.dcfc_ports == 0].nlargest(500, "predicted_dcfc_m3d2")[
    ["GEOID", "STATEFP", "COUNTYFP", "NAME", "population", "median_income",
     "ev_regs2", "jobs", "dist_road_km", "dist_nearest_dcfc_km",
     "predicted_dcfc_m3d2"]]
cand.to_csv("candidate_tracts_dcfc_m3d2_top500.csv", index=False)
feat.to_csv("tract_features_m3d2_scored.csv", index=False)
json.dump(results, open("m3_draft2_results.json", "w"), indent=1)
print("\nTop 10 M3_draft2 candidates:")
print(cand.head(10).to_string(index=False))
print("DONE", json.dumps(results, indent=1)[:600])
