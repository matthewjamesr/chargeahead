# ChargeAhead Data Hunt — Manifest

Pulled 2026-10-26 (America/Chicago). All URLs below were found via the portals'
own APIs/search or were returned by those APIs — none were guessed. Failures are
recorded as honestly as successes.

## 1. EV registrations by state (new states; WA + CA already in hand)

| State | Status | Source / URL used | File | Size | Rows | Key columns | Granularity | Vintage |
|---|---|---|---|---|---|---|---|---|
| NY | ✅ downloaded | data.ny.gov Socrata `w4pv-hbkt` (Vehicle, Snowmobile, and Boat Registrations), SODA aggregate `fuel_type='ELECTRIC' AND record_type='VEH'` grouped by ZIP. Statewide ELECTRIC total cross-checks: 221,726 | `ny_ev_by_zip.csv` | ~55 KB | 2,265 ZIPs (+header) | zip, ev_regs | ZIP | Current registrations snapshot, pulled Oct 2026. Note: NY records plug-in hybrids under other fuel codes — this is the file's `ELECTRIC` class only |
| MD | ✅ downloaded (bonus state) | opendata.maryland.gov Socrata `tugr-unu9` (MDOT MVA Electric and Plug-in Hybrid Vehicle Registrations), full paginated pull (114,745 rows), latest month snapshot, fuel_category ∈ {Electric, Plug-In Hybrid, Plug-in Hybrid}. Requires a browser User-Agent — bare clients get 403 | `md_ev_by_zip.csv` | ~35 KB | 1,389 ZIPs (+header) | zip, ev_regs, vintage | ZIP | Latest month in file: 2026/08; total 160,773 plug-ins. ZIP count exceeds MD's own ZIP count — the MVA file includes out-of-state garaging ZIPs as published |
| PA | ✅ downloaded (bonus state) | PennDOT ArcGIS MapServer `gis.penndot.pa.gov/gis/rest/services/opendata/evregistrationszip/MapServer/0`, all 7,328 features; per ZIP, latest year's most recent non-null quarterly `TOTAL_EV_Q*` | `pa_ev_by_zip.csv` | ~40 KB | 1,562 ZIPs (+header) | zip, ev_regs, year | ZIP | Year 2026 (latest in service; years 2023–2026 present); total 173,757 EVs. Underlying service carries quarterly BEV/PHEV/HEV/fuel-cell splits |
| VA | ✅ downloaded | data.virginia.gov (CKAN) dataset `virginia-electric-vehicle-ev` — "Virginia Electric Vehicle (EV) Registrations by Jurisdiction (2008–2022)", DOE-sourced XLSX; converted and cleaned (footer/projection rows stripped) | `va_ev_by_jurisdiction.xlsx` + `va_ev_by_county.csv` | 62,882 B / ~25 KB | 133 jurisdictions (of 179 sheet rows) | fips, jurisdiction, 2008…2022 annual counts | County / independent city (FIPS-keyed) | 2008–2022; workbook's own 2022 total = 47,892 EVs across the 133 jurisdictions (workbook definitions; a separate 'hybrids' sheet exists). Note: a handful of mid-2010s cells in the source look anomalous as published |
| TX | ❌ not found (sub-state) | data.texas.gov Socrata `cbmj-zeje` = statewide fiscal-year totals only (no geography, no fuel). TxDOT ArcGIS "Texas Electric Vehicle Registrations" (services.arcgis.com/KTcxiTD9dsQw4r7Z) = 154-row statewide weekly time series (Nov 2023–), not geographic | — | — | — | — | — | No public ZIP/county-level TX registration file found |
| CO | ❌ not found | data.colorado.gov Socrata catalog searched (EV / vehicle registrations): only sales aggregates and incentive lists; no registration-by-ZIP/county dataset | — | — | — | — | — | — |
| OR | ❌ not found | data.oregon.gov Socrata catalog + ArcGIS Hub search: no ODOT/DMV registration-by-geography dataset surfaced | — | — | — | — | — | — |
| NJ | ❌ not found | data.nj.gov Socrata catalog: inspection data only, no registration counts by fuel/geography | — | — | — | — | — | — |
| MA | ⚠️ exists, dashboard-gated | Massachusetts Vehicle Census (MassDOT/MAPC): town- and ZIP-sortable ZEV/hybrid/fossil counts + VMT, downloadable per the MassDOT announcement — but distribution is through the MVC dashboard UI, no direct file/API endpoint found in the time box | — | — | — | — | Municipality / ZIP | Annual (statutory, Ch. 6C §78) |
| IL | ❌ not found | data.illinois.gov Socrata catalog: no registration-by-geography dataset (IL SOS registration data is not openly published at ZIP/county level) | — | — | — | — | — | — |
| FL | ❌ not found | ArcGIS Hub + portal searches: only charging-station layers; FLHSMV publishes registration statistics as reports, no clean tabular ZIP/county EV file found | — | — | — | — | — | — |
| AZ | ❌ not found | ArcGIS Hub search surfaced only an academic "EV Sales by Zip Code" layer (ASU), not an ADOT/MVD authoritative series — not taken | — | — | — | — | — | — |
| NC | ❌ not found | opendata.nc.gov CKAN API did not return usable results; NCDOT data is dashboard-oriented; no registration-by-geography file found | — | — | — | — | — | — |
| GA | ❌ not found | ArcGIS Hub / portal searches: no DOR registration-by-geography dataset found | — | — | — | — | — | — |
| MN | ❌ not found | data.mn.gov CKAN `package_search` errored; MnDOT EV figures are dashboard-published, no file found in the time box | — | — | — | — | — | — |
| MI | ❌ not found | ArcGIS Hub search: only charger-needs planning layers (SEMCOG/evenergi), no SOS registration-by-geography dataset | — | — | — | — | — | — |

**Net gain: 4 new states** (NY, VA + bonus MD, PA) → registration features now
cover WA, CA, NY, MD, PA, VA.

## 2. LODES employment (LEHD) — ✅ downloaded

- **Version/year:** LODES8, year **2023** (latest in the tree), files
  `<st>_<wac|rac>_S000_JT00_2023.csv.gz` from
  `https://lehd.ces.census.gov/data/lodes/LODES8/<st>/<wac|rac>/`
- **Coverage:** 100 of 102 state files (50 states + DC × WAC + RAC), all
  gzip-verified; total **191,268,947 bytes (~183 MiB)** in `data/lodes/`
- **Granularity:** census block (w_geocode / h_geocode, 15-digit)
- **Columns (53):** geocode, C000 (total jobs), CA01–CA03 (age), CE01–CE03
  (earnings), CNS01–CNS20 (NAICS sector), CR01–CR07 / CT01–CT02 (race/ethnicity),
  CD01–CD04 (education), CS01–CS02 (sex), CFA01–CFA05 / CFS01–CFS05 (firm
  age/size). Spot checks: TX WAC 168,581 blocks; CA RAC 370,514 blocks; DC RAC
  4,484 blocks
- **Documented gaps:** `ak_wac` 2023 and `mi_wac` 2023 return **404 in LODES8**
  (AK WAC latest published = 2016; MI WAC latest = 2021; both states' RAC 2023
  downloaded fine). Not back-filled with older vintages, to keep the feature
  vintage uniform — substitute deliberately if wanted.
- Note: only the S000/JT00 (all jobs) segment was pulled, per spec; OD flow
  files were not requested and not downloaded.

## 3. AADT traffic counts — 📋 documented, not downloaded (per stop rule)

- **Best national source found:** FHWA **HPMS Spatial All Sections — 2024**,
  datahub.transportation.gov Socrata dataset `42um-tgh5`:
  `https://datahub.transportation.gov/resource/42um-tgh5.json`
- **Content:** 19,573,739 road-section rows; columns include `aadt`,
  `aadt_single_unit`, `aadt_combination`, `aadt_d` (count date; 2023 AADT
  vintage in the 2024 file), `county_id`, `f_system`, `nhs`, route/begin/end
  points, plus full HPMS pavement/condition fields (~120 columns)
- **Why not downloaded:** the full export is far beyond the ~2 GB cap
  (19.6M rows × ~120 cols). A compliant future extract: SODA `$select` on
  state/county/route/begin/end/aadt columns only, or the per-state HPMS
  shapefiles FHWA distributes — either is a deliberate follow-up job, not a
  scrape of 50 DOT sites (which was not attempted, per instructions).

## 4. OpenStreetMap POI extract — ⚠️ host reachable; on-disk copy NOT verified

- `download.geofabrik.de` is reachable from this environment. A clean
  single-pass download of `us-south-latest.osm.pbf` completed once at
  **1,717,161,488 bytes**, and its MD5 (a5ca1305cdcc755181ca8d89e3a784a0)
  matched the checksum Geofabrik published for that build at first check;
  the publisher has since rolled a newer daily build (checksum no longer
  comparable — the "-latest" file is a moving target).
- **However:** the copy currently on disk at `data/us-south-latest.osm.pbf`
  measures only 96,362,496 bytes despite starting with a valid OSMHeader
  block — i.e., it was truncated/replaced after the verified download
  (another writer may be active in this shared workspace). **Treat the PBF
  as not-acquired** and re-download in an exclusive window before parsing.
  The first (resumed) attempt also stitched across a daily rebuild and was
  discarded for the same reason — resume (`curl -C -`) is unsafe against
  Geofabrik's regenerating "-latest" files; use the dated extract or a
  single uninterrupted pass.

## Budget

Verified new data on disk: ~191 MB (LODES) + ~0.15 MB (state EV files) —
far under the ~6 GB cap. The 1.72 GB PBF was downloaded and checksum-verified
in flight but is not counted as acquired (see §4).
