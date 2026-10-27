#!/usr/bin/env python3
"""Re-extract HPMS arterial sections (f_system 1-3) WITH geometry from the
FHWA SODA dataset, reduced on the fly to section midpoints.
Checkpointed per page in data/hpms_pages/ — safe to re-run after a crash.
Output: data/hpms_sections_mid.csv (stateid, county_id, aadt,
sectionlength, mid_lon, mid_lat)."""
import json, os, time, urllib.request, urllib.parse
import pandas as pd

BASE = "https://datahub.transportation.gov/resource/42um-tgh5.json"
PAGE = 50000
os.makedirs("data/hpms_pages", exist_ok=True)

def fetch_page(off):
    q = {"$select": "stateid,county_id,aadt,sectionlength,line",
         "$where": "f_system in('1','2','3')",
         "$order": "shapeid", "$limit": PAGE, "$offset": off}
    url = BASE + "?" + urllib.parse.urlencode(q)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return json.load(r)
        except Exception as e:
            print(f"offset {off} attempt {attempt}: {e}", flush=True)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"page at offset {off} failed")

off = 0
total = 0
while True:
    f = f"data/hpms_pages/p{off:07d}.csv"
    if not os.path.exists(f):
        rows = fetch_page(off)
        if not rows:
            print("no more rows at", off, flush=True); break
        recs = []
        for r in rows:
            line = r.get("line") or {}
            coords = line.get("coordinates") or []
            if len(coords) < 2:
                continue
            mx = sum(c[0] for c in coords) / len(coords)
            my = sum(c[1] for c in coords) / len(coords)
            recs.append((r.get("stateid"), r.get("county_id"),
                         r.get("aadt"), r.get("sectionlength"), mx, my))
        pd.DataFrame(recs, columns=["stateid", "county_id", "aadt",
                     "sectionlength", "mid_lon", "mid_lat"]).to_csv(f, index=False)
        print(f"page {off}: {len(recs)} rows kept", flush=True)
        if len(rows) < PAGE:
            total += len(recs); print("last page", flush=True); break
    off += PAGE
    if off > 4200000: break

parts = [pd.read_csv(f"data/hpms_pages/{x}") for x in sorted(os.listdir("data/hpms_pages"))]
out = pd.concat(parts, ignore_index=True)
out.to_csv("data/hpms_sections_mid.csv", index=False)
print("TOTAL sections with midpoints:", len(out))
print(out.head(3).to_string())
