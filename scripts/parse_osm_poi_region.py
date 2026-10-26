#!/usr/bin/env python3
"""Per-region OSM POI parse (one process per region — pyrosm's memory
footprint on a 4 GB PBF is not survivable alongside another region's
results). Usage: parse_osm_poi_region.py us-west|us-south
Writes data/poi_counts_<region>.csv and data/fuel_pts_<region>.csv.
"""
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
from pyrosm import OSM

region = sys.argv[1]
tracts = gpd.read_file("data/cb_2023_us_tract_500k.zip")[["GEOID", "geometry"]]
tracts["GEOID"] = tracts.GEOID.astype(str)
tracts = tracts.to_crs("EPSG:5070")

FILTER = {"amenity": ["fuel", "parking", "charging_station"],
          "shop": True,
          "tourism": ["hotel", "motel", "hostel", "guest_house"]}
pois = OSM(f"data/osm/{region}.osm.pbf").get_pois(custom_filter=FILTER)
print(f"{region}: {len(pois):,} POIs", flush=True)
pois = pois.to_crs("EPSG:5070")
pois["pt"] = pois.geometry.centroid
joined = gpd.sjoin(gpd.GeoDataFrame(pois, geometry="pt", crs="EPSG:5070"),
                   tracts, predicate="within")
cat = np.where(joined.amenity == "fuel", "poi_fuel",
      np.where(joined.amenity == "parking", "poi_parking",
      np.where(joined.shop.notna(), "poi_retail",
      np.where(joined.tourism.notna(), "poi_hotel", "other"))))
joined = joined.assign(cat=cat)
tab = joined.groupby(["GEOID", "cat"]).size().unstack(fill_value=0)
for c in ["poi_fuel", "poi_parking", "poi_retail", "poi_hotel"]:
    if c not in tab:
        tab[c] = 0
tab[["poi_fuel", "poi_parking", "poi_retail", "poi_hotel"]] \
    .to_csv(f"data/poi_counts_{region}.csv")
fuel = pois[pois.amenity == "fuel"].geometry.centroid.to_crs("EPSG:4326")
pd.DataFrame({"lon": fuel.x, "lat": fuel.y}).to_csv(
    f"data/fuel_pts_{region}.csv", index=False)
print(f"{region}: joined {len(joined):,}, tracts {tab.shape[0]:,}, "
      f"fuel stations {len(fuel):,}")
print("DONE")
