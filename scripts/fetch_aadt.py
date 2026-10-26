#!/usr/bin/env python3
"""Targeted AADT extract: arterial sections only (f_system 1-3) from the
FHWA HPMS Spatial All Sections 2024 dataset on datahub.transportation.gov.
Compact column subset via SODA CSV pages; aggregates to county level.
"""
import io
import urllib.parse
import urllib.request
import pandas as pd

BASE = "https://datahub.transportation.gov/resource/42um-tgh5.csv"
params = {"$select": "stateid,county_id,f_system,aadt,sectionlength",
          "$where": "aadt is not null AND f_system in('1','2','3')",
          "$order": ":id", "$limit": 50000}
frames, offset = [], 0
while True:
    params["$offset"] = offset
    u = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    txt = urllib.request.urlopen(req, timeout=300).read().decode()
    d = pd.read_csv(io.StringIO(txt))
    if len(d) == 0:
        break
    frames.append(d)
    offset += len(d)
    print(f"rows so far: {offset:,}", flush=True)
    if len(d) < 50000:
        break

raw = pd.concat(frames)
raw.to_csv("data/hpms_arterial_sections.csv", index=False)
raw["aadt"] = pd.to_numeric(raw.aadt, errors="coerce")
raw["sectionlength"] = pd.to_numeric(raw.sectionlength, errors="coerce")
raw = raw.dropna(subset=["aadt"])
raw = raw.dropna(subset=["stateid", "county_id"])
raw["county_fips"] = [f"{int(s):02d}{int(c):03d}"
                      for s, c in zip(raw.stateid, raw.county_id)]
raw["w"] = raw.aadt * raw.sectionlength
g = raw.groupby("county_fips").agg(
    max_aadt_art=("aadt", "max"),
    wsum=("w", "sum"), miles=("sectionlength", "sum"),
    n_sections=("aadt", "size")).reset_index()
g["wavg_aadt_art"] = g.wsum / g.miles
g.to_csv("data/hpms_aadt_by_county.csv", index=False)
print(g.shape)
print("LA 06037:", g.set_index("county_fips").loc["06037"].to_dict())
print("Cook 17031:", g.set_index("county_fips").loc["17031"].to_dict())
print("DONE")
