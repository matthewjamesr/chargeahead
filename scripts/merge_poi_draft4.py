#!/usr/bin/env python3
"""DRAFT4: merge all five parsed regions + distance to nearest fuel.
Writes data/poi_by_tract_draft4.csv — the released M3 table is untouched."""
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.neighbors import BallTree

parts = [pd.read_csv(f"data/poi_counts_{r}.csv", dtype={"GEOID": str})
         for r in ["us-west", "us-south", "us-midwest", "us-northeast", "puerto-rico"]]
out = pd.concat(parts).groupby("GEOID").sum(numeric_only=True).reset_index()
fuel = pd.concat([pd.read_csv(f"data/fuel_pts_{r}.csv")
                  for r in ["us-west", "us-south", "us-midwest", "us-northeast", "puerto-rico"]])
tree = BallTree(np.radians(np.c_[fuel.lat.values, fuel.lon.values]),
                metric="haversine")
tracts = gpd.read_file("data/cb_2023_us_tract_500k.zip")[["GEOID", "geometry"]]
tracts["GEOID"] = tracts.GEOID.astype(str)
cent = tracts.geometry.to_crs("EPSG:4326").centroid
cent = cent[tracts.GEOID.isin(out.GEOID)]
d, _ = tree.query(np.radians(np.c_[cent.y, cent.x]), k=1)
dist = pd.Series(d[:, 0] * 6371.0088, index=cent.index)
out = out.set_index("GEOID")
out["dist_nearest_fuel_km"] = dist.groupby(tracts.GEOID).first().reindex(out.index)
out["poi_data"] = 1
out = out.reset_index()
out.to_csv("data/poi_by_tract_draft4.csv", index=False)
print(out.shape)
print(out[["poi_fuel", "poi_parking", "poi_retail", "poi_hotel"]].sum())
print("DONE")
