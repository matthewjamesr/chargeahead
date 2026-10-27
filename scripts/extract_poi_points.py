#!/usr/bin/env python3
"""Dump categorized OSM POI points for one region (same filter + category
logic as parse_osm_poi_region.py, but points instead of tract counts, so
buffer/density features can be computed nationally without border loss).
Usage: extract_poi_points.py <region>  ->  data/poi_pts_<region>.csv"""
import sys
import numpy as np, pandas as pd
from pyrosm import OSM

region = sys.argv[1]
FILTER = {"amenity": ["fuel", "parking", "charging_station"],
          "shop": True,
          "tourism": ["hotel", "motel", "hostel", "guest_house"]}
pois = OSM(f"data/osm/{region}.osm.pbf").get_pois(custom_filter=FILTER)
cat = np.where(pois.amenity == "fuel", "poi_fuel",
      np.where(pois.amenity == "parking", "poi_parking",
      np.where(pois.shop.notna(), "poi_retail",
      np.where(pois.tourism.notna(), "poi_hotel", "other"))))
pois = pois.assign(cat=cat)
pois = pois[pois.cat != "other"]
cent = pois.geometry.centroid.to_crs("EPSG:4326")
out = pd.DataFrame({"lon": cent.x.values, "lat": cent.y.values,
                    "cat": pois.cat.values})
out.to_csv(f"data/poi_pts_{region}.csv", index=False)
print(f"{region}: {len(out):,} points", out.cat.value_counts().to_dict(), flush=True)
