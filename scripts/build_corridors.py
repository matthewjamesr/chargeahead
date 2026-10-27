#!/usr/bin/env python3
"""EV corridor features from the BTS NTAD Alternative Fuel Corridors
service: pull all segments, keep EV-designated (EV in 1=Ready, 2=Pending),
then per tract centroid (EPSG:5070 for true distances): distance to the
nearest EV corridor + within-1mi / within-5mi flags.
Writes data/corridor_by_tract.csv and data/ev_corridors.geojson."""
import json, urllib.request, urllib.parse
import numpy as np, pandas as pd, geopandas as gpd

BASE = ("https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/"
        "NTAD_Alternative_Fuel_Corridors/FeatureServer/0/query")
feats, off = [], 0
while True:
    q = {"where": "EV IN (1,2)", "outFields": "EV,EV_ROUND,Len_miles",
         "returnGeometry": "true", "f": "geojson",
         "resultRecordCount": 1000, "resultOffset": off}
    url = BASE + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=120) as r:
        d = json.load(r)
    got = d.get("features", [])
    feats.extend(got)
    print(f"offset {off}: +{len(got)} (total {len(feats)})", flush=True)
    if len(got) < 1000:
        break
    off += 1000

cor = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
cor.to_file("data/ev_corridors.geojson", driver="GeoJSON")
print("EV corridor segments:", len(cor), "| total miles:",
      round(cor.Len_miles.sum()))

feat = pd.read_csv("tract_features_m3d2.csv", dtype={"GEOID": str})[
    ["GEOID", "centroid_lat", "centroid_lon"]]
pts = gpd.GeoDataFrame(feat, geometry=gpd.points_from_xy(
    feat.centroid_lon, feat.centroid_lat), crs="EPSG:4326").to_crs("EPSG:5070")
lines = cor.to_crs("EPSG:5070")[["geometry"]]
near = gpd.sjoin_nearest(pts, lines, how="left", distance_col="d_m")
near = near.groupby("GEOID")["d_m"].min().reset_index()
out = feat[["GEOID"]].merge(near, on="GEOID", how="left")
out["dist_corridor_km"] = out.d_m / 1000.0
out["log_dist_corridor_km"] = np.log1p(out.dist_corridor_km)
out["corr_1mi"] = (out.dist_corridor_km <= 1.609).astype(int)
out["corr_5mi"] = (out.dist_corridor_km <= 8.047).astype(int)
out = out[["GEOID", "log_dist_corridor_km", "corr_1mi", "corr_5mi"]]
out.to_csv("data/corridor_by_tract.csv", index=False)
print(out.shape, "| within 1mi: %.1f%% | within 5mi: %.1f%%" % (
    100 * out.corr_1mi.mean(), 100 * out.corr_5mi.mean()))
print("DONE")
