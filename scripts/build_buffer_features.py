#!/usr/bin/env python3
"""Buffer + density POI features (draft6):
- National point set (all five regions pooled -> no border undercount).
- For each tract centroid (the feature table's own centroid_lat/lon):
  counts of fuel/parking/retail/hotel POIs within 1/3/5 km (BallTree
  haversine count_neighbors) + poi_all_3k total.
- Densities: in-tract counts (draft4 table) per km2 of tract land area
  (ALAND from the Census cartographic boundary file); NaN where the
  draft4 table has no row, matching draft4 semantics.
Writes data/poi_buffer_by_tract.csv."""
import glob
import numpy as np, pandas as pd, geopandas as gpd
from sklearn.neighbors import BallTree

pts = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("data/poi_pts_*.csv"))])
print("national POI points:", len(pts), pts.cat.value_counts().to_dict())
feat = pd.read_csv("tract_features_m3d2.csv", dtype={"GEOID": str})[
    ["GEOID", "centroid_lat", "centroid_lon"]]
cent = np.radians(np.c_[feat.centroid_lat.values, feat.centroid_lon.values])
out = pd.DataFrame({"GEOID": feat.GEOID.values})
EARTH = 6371.0088
for cat, short in [("poi_fuel", "fuel"), ("poi_parking", "parking"),
                   ("poi_retail", "retail"), ("poi_hotel", "hotel")]:
    sub = pts[pts.cat == cat]
    tree = BallTree(np.radians(np.c_[sub.lat.values, sub.lon.values]),
                    metric="haversine")
    for km in (1, 3, 5):
        out[f"buf_{short}_{km}k"] = tree.query_radius(
            cent, r=km / EARTH, count_only=True)
    print(cat, "done", flush=True)
out["poi_all_3k"] = (out.buf_fuel_3k + out.buf_parking_3k +
                     out.buf_retail_3k + out.buf_hotel_3k)

tracts = gpd.read_file("data/cb_2023_us_tract_500k.zip")[["GEOID", "ALAND"]]
tracts["GEOID"] = tracts.GEOID.astype(str)
tracts["aland_km2"] = tracts.ALAND / 1e6
intract = pd.read_csv("data/poi_by_tract_draft4.csv", dtype={"GEOID": str})
out = out.merge(tracts[["GEOID", "aland_km2"]], on="GEOID", how="left")
out = out.merge(intract[["GEOID", "poi_fuel", "poi_parking", "poi_retail",
                         "poi_hotel"]], on="GEOID", how="left")
for c in ["poi_fuel", "poi_parking", "poi_retail", "poi_hotel"]:
    short = c.replace("poi_", "")
    out[f"dens_{short}"] = out[c] / out.aland_km2.replace(0, np.nan)
out = out.drop(columns=["aland_km2", "poi_fuel", "poi_parking", "poi_retail",
                        "poi_hotel"])
out.to_csv("data/poi_buffer_by_tract.csv", index=False)
print(out.shape)
print(out.iloc[:, 1:].describe().loc[["mean", "max"]].round(2).to_string())
print("DONE")
