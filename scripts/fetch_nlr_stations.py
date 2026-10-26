#!/usr/bin/env python3
"""Fetch the NLR (National Laboratory of the Rockies, formerly NREL)
Alternative Fuel Stations dataset — electric, public, currently available.

Requires a free API key from https://developer.nlr.gov/signup/
Set it in the environment:  export NLR_API_KEY=...

Usage:
    python fetch_nlr_stations.py [--state TX] --out stations.jsonl
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

BASE = "https://developer.nlr.gov/api/alt-fuel-stations/v1.json"


def fetch(params, key):
    url = BASE + "?" + urllib.parse.urlencode({**params, "api_key": key})
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    key = os.environ.get("NLR_API_KEY")
    if not key:
        sys.exit("NLR_API_KEY is not set (get a free key at "
                 "https://developer.nlr.gov/signup/)")
    base = {"fuel_type": "ELEC", "status": "E", "access": "public", "limit": 1}
    if args.state:
        base["state"] = args.state
    total = fetch(base, key)["total_results"]
    print(f"total_results: {total}", file=sys.stderr)
    written = 0
    with open(args.out, "w", encoding="utf-8") as f:
        offset = 0
        while offset < total:
            d = fetch({**base, "limit": 200, "offset": offset}, key)
            rows = d.get("fuel_stations", [])
            if not rows:
                break
            for s in rows:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
            written += len(rows)
            offset += len(rows)
            print(f"pulled {written}/{total}", file=sys.stderr)
    print(json.dumps({"written": written, "expected": total}))


if __name__ == "__main__":
    main()
