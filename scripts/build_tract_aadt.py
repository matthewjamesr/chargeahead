#!/usr/bin/env python3
"""Tract-level AADT from HPMS section midpoints (validated re-extract).
Per tract: max AADT + length-weighted mean AADT over sections whose
midpoint falls in the tract; county-fallback 'filled' variants coalesce
tract -> county values. Writes data/aadt_by_tract.csv."""
import numpy as np, pandas as pd, geopandas as gpd

mid = pd.read_csv("data/hpms_sections_mid.csv")
mid = mid.drop_duplicates().dropna(subset=["aadt", "mid_lon", "mid_lat"])
print("sections used:", len(mid))
pts = gpd.GeoDataFrame(mid, geometry=gpd.points_from_xy(mid.mid_lon, mid.mid_lat),
                       crs="EPSG:4326")
tracts = gpd.read_file("data/cb_2023_us_tract_500k.zip")[["GEOID", "geometry"]]
tracts["GEOID"] = tracts.GEOID.astype(str)
j = gpd.sjoin(pts, tracts, predicate="within")[["GEOID", "aadt", "sectionlength"]]
j["wl"] = j.aadt * j.sectionlength
g = j.groupby("GEOID")
t = pd.DataFrame({"tract_max_raw": g.aadt.max(),
                  "tract_wavg_raw": g.wl.sum() / g.sectionlength.sum(),
                  "tract_n_sections": g.size()})
print("tracts with >=1 arterial section:", len(t), "of", len(tracts))

feat = pd.read_csv("tract_features_m3d2.csv", dtype={"GEOID": str})[["GEOID"]]
out = feat.merge(t, left_on="GEOID", right_index=True, how="left")
ref = pd.read_csv("data/hpms_aadt_by_county.csv", dtype={"county_fips": str})
cmap_max = ref.set_index("county_fips").max_aadt_art
cmap_wavg = ref.set_index("county_fips").wavg_aadt_art
county = out.GEOID.str[:5]
out["county_max_raw"] = county.map(cmap_max)
out["county_wavg_raw"] = county.map(cmap_wavg)
out["has_tract_aadt"] = out.tract_max_raw.notna().astype(int)
out["log_tract_max_aadt"] = np.log1p(out.tract_max_raw)
out["log_tract_wavg_aadt"] = np.log1p(out.tract_wavg_raw)
out["fill_log_max_aadt"] = np.log1p(out.tract_max_raw.fillna(out.county_max_raw))
out["fill_log_wavg_aadt"] = np.log1p(out.tract_wavg_raw.fillna(out.county_wavg_raw))
out = out[["GEOID", "log_tract_max_aadt", "log_tract_wavg_aadt", "has_tract_aadt",
           "fill_log_max_aadt", "fill_log_wavg_aadt", "tract_n_sections"]]
out.to_csv("data/aadt_by_tract.csv", index=False)
print(out.shape, "| tract-AADT coverage: %.1f%%" % (100 * out.has_tract_aadt.mean()))
print("DONE")
