#!/usr/bin/env python3
"""Fetch LODES8 2019 WAC + RAC for the same jurisdictions as the local
2023 intake (data/lodes/*_2023.csv.gz), into data/lodes/ with 2019 names."""
import os, subprocess, sys
states = sorted({f.split("_")[0] for f in os.listdir("data/lodes") if f.endswith("_2023.csv.gz")})
print("jurisdictions:", len(states), states, flush=True)
fails = []
for st in states:
    for kind in ("wac", "rac"):
        fn = f"{st}_{kind}_S000_JT00_2019.csv.gz"
        path = f"data/lodes/{fn}"
        if os.path.exists(path):
            continue
        url = f"https://lehd.ces.census.gov/data/lodes/LODES8/{st}/{kind}/{fn}"
        r = subprocess.run(["curl", "-sL", "--fail", "-o", path, url],
                           capture_output=True, text=True)
        if r.returncode != 0:
            fails.append(fn); print("FAIL", fn, flush=True)
        else:
            print("ok", fn, os.path.getsize(path), flush=True)
print("fails:", fails)
