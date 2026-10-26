#!/usr/bin/env python3
"""Tract-level EV charger demand model v1.

Stations (NLR) -> spatial join to 2023 census tracts -> aggregate supply
per tract -> join ACS 2023 population + median income -> train
HistGradientBoostingRegressor (target: total charging ports per tract)
with GroupKFold spatial validation by county -> rank zero-station tracts
by predicted demand as placement candidates.
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error

D = "data/"

# --- 1. Tracts ------------------------------------------------------------
tracts = gpd.read_file(D + "cb_2023_us_tract_500k.zip")[
    ["GEOID", "STATEFP", "COUNTYFP", "NAME", "ALAND", "geometry"]]
tracts["land_sqmi"] = tracts["ALAND"] / 2.58999e6

# --- 2. Stations -> tracts ------------------------------------------------
st = pd.read_csv(D + "nlr_elec_public_stations.csv", low_memory=False)
for c in ["ev_level1_evse_num", "ev_level2_evse_num", "ev_dc_fast_num"]:
    st[c] = pd.to_numeric(st[c], errors="coerce").fillna(0)
st["ports"] = st[["ev_level1_evse_num", "ev_level2_evse_num",
                  "ev_dc_fast_num"]].sum(axis=1)
pts = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st.longitude,
                                                       st.latitude),
                       crs="EPSG:4326").to_crs(tracts.crs)
joined = gpd.sjoin(pts, tracts[["GEOID", "geometry"]], how="inner",
                   predicate="within")
supply = joined.groupby("GEOID").agg(
    stations=("id", "count"), ports=("ports", "sum"),
    l2_ports=("ev_level2_evse_num", "sum"),
    dcfc_ports=("ev_dc_fast_num", "sum")).reset_index()
print(f"stations matched to a tract: {len(joined):,} / {len(st):,}")

# --- 3. ACS features ------------------------------------------------------
def load_acs(fname, col, name):
    df = pd.read_csv(D + fname, sep="|", usecols=["GEO_ID", col],
                     dtype=str)
    df = df[df.GEO_ID.str.startswith("1400000US")]  # summary level 140 = tract
    df["GEOID"] = df.GEO_ID.str[-11:]
    df[name] = pd.to_numeric(df[col], errors="coerce")
    return df[["GEOID", name]]

pop = load_acs("acs_population_by_tract_2023.dat", "B01003_E001", "population")
inc = load_acs("acs_median_income_by_tract_2023.dat", "B19013_E001",
               "median_income")
inc.loc[inc.median_income < 0, "median_income"] = np.nan  # Census sentinels

feat = tracts.drop(columns="geometry").merge(pop, on="GEOID", how="left") \
                                       .merge(inc, on="GEOID", how="left") \
                                       .merge(supply, on="GEOID", how="left")
for c in ["stations", "ports", "l2_ports", "dcfc_ports"]:
    feat[c] = feat[c].fillna(0)
feat["pop_density"] = feat.population / feat.land_sqmi.replace(0, np.nan)
feat.to_csv("tract_features.csv", index=False)
print(f"tracts: {len(feat):,} | with >=1 station: {(feat.stations>0).sum():,}")

# --- 4. Model -------------------------------------------------------------
m = feat.dropna(subset=["population", "median_income", "pop_density"]).copy()
m["log_pop"] = np.log1p(m.population)
m["log_density"] = np.log1p(m.pop_density)
X = m[["log_pop", "log_density", "median_income"]]
y = m.ports
groups = m.GEOID.str[:5]  # county FIPS

model = HistGradientBoostingRegressor(random_state=42)
pred = cross_val_predict(model, X, y, groups=groups,
                         cv=GroupKFold(n_splits=5))
print(f"spatial-CV (by county): R2={r2_score(y, pred):.3f} "
      f"MAE={mean_absolute_error(y, pred):.2f} ports/tract")
model.fit(X, y)
m["predicted_ports"] = np.clip(model.predict(X), 0, None)
m["gap"] = m.predicted_ports - m.ports

# --- 5. Candidates: zero supply, highest predicted demand -----------------
cand = m[m.stations == 0].nlargest(500, "predicted_ports")[
    ["GEOID", "STATEFP", "COUNTYFP", "NAME", "population", "median_income",
     "pop_density", "predicted_ports", "gap"]]
cand.to_csv("candidate_tracts_top500.csv", index=False)
print("\nTop 10 candidate tracts (no station today, highest predicted ports):")
print(cand.head(10).to_string(index=False))
