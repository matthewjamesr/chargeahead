# Data sources

All inputs are public datasets. Raw downloads are **not** committed to this
repository (several are hundreds of MB); this file is the exact recipe the
maintainers used, so the pipeline is fully reproducible.

| Dataset | Publisher | File / endpoint | Used for |
|---|---|---|---|
| Alternative Fuel Stations | NLR (National Laboratory of the Rockies, formerly NREL), U.S. DOE | `GET https://developer.nlr.gov/api/alt-fuel-stations/v1.json` — free API key from https://developer.nlr.gov/signup/; helper: `scripts/fetch_nlr_stations.py` | Station census (83,546 public, available, electric stations at Oct 2026 pull); port counts = model target |
| ACS 2023 5-year, table-based summary files | U.S. Census Bureau | `https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/acsdt5y2023-b01003.dat` (population) and `...-b19013.dat` (median household income) | Tract demographics (summary level 140 rows) |
| Cartographic boundary tracts 2023 (500k) | U.S. Census Bureau | `https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_tract_500k.zip` | Tract geometries for the spatial join |
| TIGER ZCTA 2023 | U.S. Census Bureau | `https://www2.census.gov/geo/tiger/TIGER2023/ZCTA520/tl_2023_us_zcta520.zip` | ZIP→tract areal interpolation |
| TIGER primary roads 2023 | U.S. Census Bureau | `https://www2.census.gov/geo/tiger/TIGER2023/PRIMARYROADS/tl_2023_us_primaryroads.zip` | Distance to nearest Interstate / U.S. highway |
| ZIP Business Patterns 2022 | U.S. Census Bureau | `https://www2.census.gov/programs-surveys/cbp/datasets/2022/zbp22totals.zip` | Employment + establishments by ZIP |
| Electric Vehicle Population Data | Washington State Dept. of Licensing | Socrata `https://data.wa.gov/resource/f6w7-q2d2.json` (300k records) | WA EV registrations by ZIP. Note: the ZIP field is `zip_code`; the tract field is `_2020_census_tract` |
| Vehicle Fuel Type Count by ZIP (1/1/2026 snapshot) | California DMV via CA Open Data | `https://publish.data.ca.gov/dataset/15179472-adeb-4df6-920a-20640d02b08c/resource/b459d957-5d94-4b10-999d-770419870364/download/vehicle-fuel-type-counts-2025.csv` | CA plug-in registrations by ZIP (Fuel ∈ {Battery Electric, Plug-in Hybrid}, Duty = Light; ≈2.22M vehicles) |

## Joins and derived features

- Stations → tracts: point-in-polygon spatial join (`geopandas.sjoin`, predicate `within`).
- ZIP-level values (EV registrations, ZBP employment/establishments) → tracts:
  population-density-weighted areal interpolation over ZCTA∩tract intersections
  (weight = intersection area × tract population density). The overlay runs in
  chunks — a single national overlay will exhaust memory on modest hardware.
- Supply context: haversine BallTree over DCFC station coordinates; ring sums
  exclude the tract's own ports.
- Validation everywhere: `GroupKFold` grouped by county FIPS (GEOID[:5]).
