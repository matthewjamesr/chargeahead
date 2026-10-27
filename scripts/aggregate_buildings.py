#!/usr/bin/env python3
"""Aggregate Microsoft building footprints per census tract.
Per part file: vectorized GeoJSON parse (shapely.from_geojson), areas via
a per-part equirectangular scale (building-sized polygons: error <0.1%),
centroid -> tract via STRtree over cb_2023 tract polygons. Partial sums
per part -> data/buildings/partial_<part>.csv, then merged.
Writes data/buildings_by_tract.csv."""
import glob, json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
import shapely
from shapely import STRtree
from multiprocessing import Pool

TRACTS = gpd.read_file("data/cb_2023_us_tract_500k.zip")[["GEOID", "ALAND", "geometry"]]
TREE = STRtree(TRACTS.geometry.values)
GEOIDS = TRACTS.GEOID.values

def _agg_chunk(lines):
    geoms = shapely.from_geojson(lines)
    ok = shapely.is_valid(geoms) & (shapely.get_type_id(geoms) == 3)
    geoms = geoms[ok]
    if len(geoms) == 0:
        return None, 0
    cents = shapely.centroid(geoms)
    lat0 = float(np.mean(shapely.get_y(cents)))
    kx = 111320.0 * np.cos(np.radians(lat0))
    ky = 110574.0
    coords = shapely.get_coordinates(geoms)
    coords = coords * np.array([kx, ky])
    areas = shapely.area(shapely.set_coordinates(geoms, coords))
    q = TREE.query(cents, predicate="within")
    if len(q[0]) == 0:
        return None, len(geoms)
    df = pd.DataFrame({
        "GEOID": GEOIDS[q[1]],
        "n": 1,
        "area": areas[q[0]],
        "large500": (areas[q[0]] >= 500).astype(float),
        "large2000": (areas[q[0]] >= 2000).astype(float),
    })
    return df.groupby("GEOID").sum(numeric_only=True).reset_index(), len(geoms)


def process(path):
    name = os.path.basename(path)
    outp = f"data/buildings/partial_{name}.csv"
    if os.path.exists(outp):
        return (name, -1)
    import gzip
    aggs, total, buf = [], 0, []
    with gzip.open(path, "rb") as f:
        for line in f:
            buf.append(line)
            if len(buf) >= 100000:
                a, n = _agg_chunk(buf); total += n
                if a is not None: aggs.append(a)
                buf = []
    if buf:
        a, n = _agg_chunk(buf); total += n
        if a is not None: aggs.append(a)
    if aggs:
        agg = pd.concat(aggs).groupby("GEOID").sum(numeric_only=True).reset_index()
    else:
        agg = pd.DataFrame(columns=["GEOID", "n", "area", "large500", "large2000"])
    agg.to_csv(outp, index=False)
    return (name, total)


if __name__ == "__main__":
    parts = sorted(glob.glob("data/buildings/parts/*.csv.gz"))
    print("parts to process:", len(parts), flush=True)
    total = 0
    with Pool(2) as pool:
        for i, (name, n) in enumerate(pool.imap_unordered(process, parts, chunksize=4)):
            if n > 0:
                total += n
            if (i + 1) % 200 == 0:
                print(f"{i+1}/{len(parts)} parts, buildings so far {total:,}", flush=True)
    partials = [pd.read_csv(p, dtype={"GEOID": str})
                for p in glob.glob("data/buildings/partial_*.csv")]
    allp = pd.concat([p for p in partials if "n" in p.columns])
    g = allp.groupby("GEOID").sum(numeric_only=True).reset_index()
    aland = TRACTS.set_index("GEOID")["ALAND"] / 1e6  # km^2
    out = pd.DataFrame({"GEOID": g.GEOID})
    out["bldg_count"] = g.n.values
    out["bldg_area_km2"] = g.area.values / 1e6
    out["bldg_mean_area"] = g.area.values / g.n.values
    out["bldg_large500_share"] = g.large500.values / g.n.values
    out["bldg_large2000_share"] = g.large2000.values / g.n.values
    out["land_km2"] = out.GEOID.map(aland)
    out["bldg_per_km2"] = out.bldg_count / out.land_km2
    out["bldg_cover"] = out.bldg_area_km2 / out.land_km2
    out["log_bldg_count"] = np.log1p(out.bldg_count)
    out["log_bldg_area"] = np.log1p(g.area.values)
    out["log_bldg_mean_area"] = np.log(out.bldg_mean_area)
    out = out.drop(columns=["land_km2"])
    out.to_csv("data/buildings_by_tract.csv", index=False)
    print("tracts with buildings:", len(out), "| total buildings:", int(g.n.sum()))
    print("DONE")
