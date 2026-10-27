#!/usr/bin/env python3
"""Download all US building-footprint partitions (checkpointed by size)."""
import json, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor
parts = json.load(open("us_part_urls.json"))
os.makedirs("data/buildings/parts", exist_ok=True)

def local_path(url):
    m = re.search(r"quadkey=([0-9]+)/(part-[^/]+)$", url)
    return f"data/buildings/parts/{m.group(1)}__{m.group(2)}"

def fetch(p):
    lp = local_path(p["url"])
    want = int(p["mb"] * 1e6)
    if os.path.exists(lp) and abs(os.path.getsize(lp) - want) < want * 0.02 + 2048:
        return ("skip", lp)
    r = subprocess.run(["curl", "-sL", "--fail", "--retry", "2", "-o", lp + ".tmp", p["url"]],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return ("fail", lp)
    os.rename(lp + ".tmp", lp)
    return ("ok", lp)

done = fail = 0
with ThreadPoolExecutor(4) as ex:
    for i, (st, lp) in enumerate(ex.map(fetch, parts)):
        if st == "fail":
            fail += 1; print("FAIL", lp, flush=True)
        done += 1
        if done % 200 == 0:
            print(f"{done}/{len(parts)} (fails {fail})", flush=True)
print("DONE_PARTS", done, "fails", fail)
