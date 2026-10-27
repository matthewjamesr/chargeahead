#!/usr/bin/env python3
"""LODES trend features: 2019 -> 2023 growth in workplace jobs (WAC C000)
and resident workers (RAC C000), aggregated block -> tract, as shrunk log
ratios log((x23 + 10) / (x19 + 10)). Tracts absent from either year's
extract get NaN. Also verifies 2019 tract coverage (2020-geography check)
and that the 2023 aggregation reproduces the existing LODES levels.
Writes data/lodes_trends_by_tract.csv."""
import glob
import numpy as np, pandas as pd

def agg(pattern, col):
    parts = []
    for f in sorted(glob.glob(pattern)):
        d = pd.read_csv(f, usecols=[col, "C000"], dtype={col: str})
        d["GEOID"] = d[col].str[:11]
        parts.append(d.groupby("GEOID")["C000"].sum())
    return pd.concat(parts).groupby(level=0).sum()

w19 = agg("data/lodes/*_wac_S000_JT00_2019.csv.gz", "w_geocode")
w23 = agg("data/lodes/*_wac_S000_JT00_2023.csv.gz", "w_geocode")
r19 = agg("data/lodes/*_rac_S000_JT00_2019.csv.gz", "h_geocode")
r23 = agg("data/lodes/*_rac_S000_JT00_2023.csv.gz", "h_geocode")
print("tracts: wac19", len(w19), "| wac23", len(w23), "| rac19", len(r19), "| rac23", len(r23))

feat = pd.read_csv("tract_features_m3d2.csv", dtype={"GEOID": str})
universe = set(feat.GEOID)
print("2019 WAC tract coverage of feature universe: %.1f%%" %
      (100 * len(universe & set(w19.index)) / len(universe)))
chk = pd.DataFrame({"jobs23": w23}).join(
    feat.set_index("GEOID")["log_lodes_work"], how="inner")
chk["implied"] = np.log1p(chk.jobs23)
print("2023 WAC vs log_lodes_work: max |diff| =",
      float((chk.implied - chk.log_lodes_work).abs().max()))

out = pd.DataFrame(index=sorted(universe))
out.index.name = "GEOID"
out["wac_growth"] = np.log((w23 + 10) / (w19 + 10))
out["rac_growth"] = np.log((r23 + 10) / (r19 + 10))
out = out.reset_index()
out.to_csv("data/lodes_trends_by_tract.csv", index=False)
print(out.shape)
print(out[["wac_growth", "rac_growth"]].describe().loc[["mean", "std", "min", "max"]].round(3).to_string())
print("DONE")
