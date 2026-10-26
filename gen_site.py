#!/usr/bin/env python3
"""Generate docs/index.html (GitHub Pages landing + results dashboard)."""
import json

cands = json.load(open("data/dashboard_candidates.json"))
DATA = json.dumps(cands)

HEAD = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChargeAhead — Open models for EV charging placement</title>
<meta name="description" content="Open, data-driven models for deciding where EV charging should go next. Tract-level DC fast-charging demand prediction built entirely on public data.">
<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script>
tailwind.config = { theme: { extend: {
  colors: { volt: '#a3e635', ink: '#09090b' },
  fontFamily: { sans: ['Inter','ui-sans-serif','system-ui'], disp: ['Space Grotesk','Inter','sans-serif'], mono: ['JetBrains Mono','monospace'] }
}}}
</script>
<style>
  html{scroll-behavior:smooth}
  body{background:#09090b;color:#e4e4e7;font-family:Inter,ui-sans-serif,system-ui}
  ::selection{background:#a3e635;color:#09090b}
  .card{background:rgba(24,24,27,.72);border:1px solid #27272a;border-radius:.9rem;backdrop-filter:blur(8px)}
  .card:hover{border-color:#3f3f46}
  .badge{display:inline-flex;align-items:center;gap:.35rem;border:1px solid #3f3f46;border-radius:999px;padding:.15rem .6rem;font-size:.72rem;font-weight:600;letter-spacing:.02em;color:#d4d4d8;background:rgba(39,39,42,.6)}
  .badge-volt{border-color:#a3e635;color:#a3e635;background:rgba(163,230,53,.08)}
  .btn{display:inline-flex;align-items:center;gap:.5rem;border-radius:.6rem;font-weight:600;font-size:.9rem;padding:.65rem 1.15rem;transition:all .15s}
  .btn-primary{background:#a3e635;color:#09090b}.btn-primary:hover{background:#bef264}
  .btn-outline{border:1px solid #3f3f46;color:#e4e4e7;background:rgba(24,24,27,.5)}.btn-outline:hover{border-color:#a3e635;color:#a3e635}
  .tab-btn{border:1px solid #3f3f46;border-radius:.55rem;padding:.45rem .95rem;font-size:.85rem;font-weight:600;color:#a1a1aa;background:rgba(24,24,27,.5)}
  .tab-btn.active{background:#a3e635;color:#09090b;border-color:#a3e635}
  .bar-track{background:#27272a;border-radius:999px;height:.65rem;overflow:hidden}
  .bar-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#65a30d,#a3e635);width:0;transition:width 1.1s cubic-bezier(.22,1,.36,1)}
  .bar-fill.dim{background:linear-gradient(90deg,#3f3f46,#52525b)}
  table.explorer th{font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:#a1a1aa;text-align:left;padding:.55rem .7rem;border-bottom:1px solid #27272a;cursor:pointer;white-space:nowrap}
  table.explorer td{padding:.55rem .7rem;border-bottom:1px solid #1c1c1f;font-size:.85rem;white-space:nowrap}
  table.explorer tr.row:hover td{background:rgba(163,230,53,.05)}
  table.explorer tr.sel td{background:rgba(163,230,53,.12)}
  input[type=range]{accent-color:#a3e635}
  select,input[type=text]{background:#18181b;border:1px solid #3f3f46;border-radius:.55rem;padding:.5rem .7rem;font-size:.85rem;color:#e4e4e7}
  select:focus,input[type=text]:focus{outline:none;border-color:#a3e635}
  .leaflet-container{background:#0c0c0e;font-family:Inter}
  .glow{position:fixed;border-radius:50%;filter:blur(120px);pointer-events:none;z-index:-1}
  .fade-up{opacity:0;transform:translateY(14px);transition:opacity .7s ease,transform .7s ease}
  .fade-up.in{opacity:1;transform:none}
  .num{font-family:'Space Grotesk';font-variant-numeric:tabular-nums}
  .sep{height:1px;background:linear-gradient(90deg,transparent,#27272a,transparent)}
  #tooltip{position:fixed;pointer-events:none;z-index:60;max-width:300px}
</style>
</head>
<body class="antialiased">
<canvas id="bg-canvas" class="fixed inset-0 -z-10 w-full h-full"></canvas>
<div class="glow" style="width:560px;height:560px;top:-160px;right:-120px;background:rgba(163,230,53,.07)"></div>
<div class="glow" style="width:640px;height:640px;bottom:-260px;left:-200px;background:rgba(34,211,238,.05)"></div>

<header class="sticky top-0 z-40 border-b border-zinc-800/80 bg-zinc-950/75 backdrop-blur-md">
  <div class="max-w-7xl mx-auto px-5 h-16 flex items-center gap-6">
    <a href="#top" class="flex items-center gap-2.5 font-disp font-700 text-lg tracking-tight">
      <span class="inline-flex w-8 h-8 rounded-lg bg-volt text-zinc-950 items-center justify-center">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2 4.5 13.5H11L9.5 22 19 9.5h-6.5L13 2z"/></svg>
      </span>ChargeAhead
    </a>
    <nav class="hidden md:flex items-center gap-5 text-sm text-zinc-400">
      <a class="hover:text-volt" href="#results">Results</a>
      <a class="hover:text-volt" href="#explorer">Candidate explorer</a>
      <a class="hover:text-volt" href="#methods">Methods</a>
      <a class="hover:text-volt" href="#families">Model families</a>
      <a class="hover:text-volt" href="#data">Data</a>
    </nav>
    <div class="ml-auto flex items-center gap-3">
      <span class="badge badge-volt hidden sm:inline-flex">Open source · MIT</span>
      <a class="btn btn-outline !py-2 !px-3.5" href="https://github.com/matthewjamesr/chargeahead" target="_blank" rel="noopener">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
        GitHub</a>
    </div>
  </div>
</header>

<main id="top" class="max-w-7xl mx-auto px-5">
  <!-- HERO -->
  <section class="pt-20 pb-14 text-center">
    <span class="badge badge-volt fade-up">An open research project · public data only</span>
    <h1 class="fade-up font-disp font-bold tracking-tight text-5xl md:text-7xl mt-6 leading-[1.04]">Where should the next<br><span class="text-volt">fast chargers</span> go?</h1>
    <p class="fade-up text-zinc-400 text-lg md:text-xl max-w-3xl mx-auto mt-6">ChargeAhead builds open, reproducible machine-learning models that predict DC fast-charging demand for every census tract in the United States — so placement decisions rest on evidence, not guesswork. Every dataset is public, every number on this page is computed by code in the repository, and every limitation is stated out loud.</p>
    <div class="fade-up flex flex-wrap justify-center gap-3 mt-8">
      <a href="#explorer" class="btn btn-primary">Explore candidate tracts
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      <a href="https://github.com/matthewjamesr/chargeahead" target="_blank" rel="noopener" class="btn btn-outline">Read the code &amp; data</a>
    </div>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-14 text-left">
      <div class="card p-5 fade-up"><div class="num text-3xl md:text-4xl font-bold text-white"><span data-count="83546">0</span></div><div class="text-zinc-400 text-sm mt-1">public charging stations censused (NLR)</div></div>
      <div class="card p-5 fade-up"><div class="num text-3xl md:text-4xl font-bold text-white"><span data-count="79187">0</span></div><div class="text-zinc-400 text-sm mt-1">DC fast-charge ports in the census</div></div>
      <div class="card p-5 fade-up"><div class="num text-3xl md:text-4xl font-bold text-white"><span data-count="85186">0</span></div><div class="text-zinc-400 text-sm mt-1">census tracts scored by the model</div></div>
      <div class="card p-5 fade-up"><div class="num text-3xl md:text-4xl font-bold text-volt">0.209</div><div class="text-zinc-400 text-sm mt-1">spatial-CV R² — vs 0.007 for demographics alone</div></div>
    </div>
  </section>

  <div class="sep"></div>

  <!-- RESEARCH QUESTIONS -->
  <section class="py-14">
    <h2 class="font-disp text-3xl font-bold fade-up">The academic questions</h2>
    <p class="text-zinc-400 mt-2 max-w-3xl fade-up">This project is equal parts infrastructure planning and applied machine-learning methodology — in particular, how honestly a geospatial model can be evaluated.</p>
    <div class="grid md:grid-cols-3 gap-4 mt-8">
      <div class="card p-6 fade-up"><div class="badge mb-3">RQ1 · Demand</div><h3 class="font-semibold text-lg">What predicts fast-charging demand?</h3><p class="text-zinc-400 text-sm mt-2 leading-relaxed">Which observable features of a place — its people, jobs, vehicles, roads, and existing supply — actually explain where DC fast charging exists and thrives? Demographics alone, it turns out, explain almost nothing.</p></div>
      <div class="card p-6 fade-up"><div class="badge mb-3">RQ2 · Validation</div><h3 class="font-semibold text-lg">How do you validate a map?</h3><p class="text-zinc-400 text-sm mt-2 leading-relaxed">Random train/test splits leak badly on geographic data — a site and its near-twin across the street land on both sides. We use county-grouped spatial cross-validation throughout, and report the unflattering numbers it produces.</p></div>
      <div class="card p-6 fade-up"><div class="badge mb-3">RQ3 · Gaps</div><h3 class="font-semibold text-lg">Where is the underserved demand?</h3><p class="text-zinc-400 text-sm mt-2 leading-relaxed">Ranking tracts with high predicted demand and zero fast chargers produces a defensible shortlist for planners — with the model's own confidence limits attached, not hidden.</p></div>
    </div>
  </section>
"""

RESULTS = r"""
  <div class="sep"></div>

  <!-- RESULTS -->
  <section id="results" class="py-14">
    <div class="flex flex-wrap items-end gap-4">
      <div>
        <h2 class="font-disp text-3xl font-bold fade-up">Results — model v2, DC fast charging</h2>
        <p class="text-zinc-400 mt-2 max-w-3xl fade-up">Target: DC fast-charge ports per census tract. Algorithm: gradient-boosted trees (scikit-learn <span class="font-mono text-zinc-300">HistGradientBoostingRegressor</span>). Validation: 5-fold cross-validation grouped by county, so the model is always scored on counties it has never seen.</p>
      </div>
      <span class="badge badge-volt ml-auto fade-up">v2 · Oct 2026</span>
    </div>

    <div class="grid lg:grid-cols-2 gap-4 mt-8">
      <div class="card p-6 fade-up">
        <h3 class="font-semibold">Explained variance (R²), held-out counties</h3>
        <div class="mt-5 space-y-5">
          <div>
            <div class="flex justify-between text-sm mb-1.5"><span class="text-zinc-300">M2 — full feature set</span><span class="num font-semibold text-volt">0.209</span></div>
            <div class="bar-track"><div class="bar-fill" data-w="83.6"></div></div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1.5"><span class="text-zinc-400">M0 — demographics only (v1 features)</span><span class="num font-semibold text-zinc-400">0.007</span></div>
            <div class="bar-track"><div class="bar-fill dim" data-w="2.8"></div></div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1.5"><span class="text-zinc-400">v1 — all charging ports, demographics only</span><span class="num font-semibold text-zinc-400">0.004</span></div>
            <div class="bar-track"><div class="bar-fill dim" data-w="1.6"></div></div>
          </div>
        </div>
        <p class="text-zinc-500 text-sm mt-5 leading-relaxed">Adding EV registrations, employment, highway proximity and supply context improved explained variance roughly <strong class="text-zinc-300">thirty-fold</strong>. Mean absolute error fell from 1.61 to <strong class="text-zinc-300">1.33 ports per tract</strong>. The honest reading: placement is still mostly driven by land-use detail and network history no tract dataset captures — which is itself a publishable finding.</p>
      </div>

      <div class="card p-6 fade-up">
        <h3 class="font-semibold">What drives placement? <span class="text-zinc-500 font-normal text-sm">— permutation importance, hover for plain English</span></h3>
        <div id="importance" class="mt-5 space-y-3.5"></div>
        <p class="text-zinc-500 text-sm mt-5 leading-relaxed">Charging clusters near charging: existing supply context is the single strongest signal, which makes the model excellent at predicting <em>infill</em> — and is exactly why greenfield discovery needs its own model family (below).</p>
      </div>
    </div>
  </section>

  <div class="sep"></div>

  <!-- EXPLORER -->
  <section id="explorer" class="py-14">
    <h2 class="font-disp text-3xl font-bold fade-up">Candidate explorer</h2>
    <p class="text-zinc-400 mt-2 max-w-3xl fade-up">The top 250 census tracts that have <strong class="text-zinc-200">zero DC fast chargers today</strong>, ranked by predicted ports. Filter, search, sort — click a row or a marker and the map and table stay in sync.</p>
    <div class="card p-4 mt-8 fade-up">
      <div class="flex flex-wrap gap-3 items-center">
        <select id="f-state"><option value="">All states</option></select>
        <input type="text" id="f-search" placeholder="Search county or tract…" class="w-52">
        <label class="text-sm text-zinc-400 flex items-center gap-2">Min predicted ports
          <input type="range" id="f-min" min="0" max="15" step="0.5" value="0" class="w-36">
          <span id="f-min-val" class="num text-zinc-200 w-8">0</span></label>
        <select id="f-sort">
          <option value="predicted_dcfc">Sort: predicted ports</option>
          <option value="population">Sort: population</option>
          <option value="ev_regs">Sort: EV registrations</option>
          <option value="jobs">Sort: jobs</option>
          <option value="dist_nearest_dcfc_km">Sort: distance to nearest DCFC</option>
        </select>
        <span class="badge ml-auto" id="f-count"></span>
      </div>
      <div id="map" class="w-full h-[430px] rounded-lg mt-4 border border-zinc-800 z-0"></div>
      <div class="overflow-x-auto mt-4 max-h-[430px] overflow-y-auto">
        <table class="explorer w-full" id="cand-table">
          <thead class="sticky top-0 bg-zinc-900"><tr>
            <th>#</th><th>Tract</th><th>County</th><th>State</th><th>Predicted ports</th>
            <th>Population</th><th>Median income</th><th>EV regs*</th><th>Jobs</th>
            <th>km to highway</th><th>km to nearest DCFC</th>
          </tr></thead>
          <tbody id="cand-body"></tbody>
        </table>
      </div>
      <p class="text-zinc-500 text-xs mt-3">* EV registrations are currently available only for California and Washington (state open-data portals); blank elsewhere — the model handles the missing values natively rather than inventing them.</p>
    </div>
  </section>

  <div class="sep"></div>

  <!-- METHODS -->
  <section id="methods" class="py-14">
    <h2 class="font-disp text-3xl font-bold fade-up">Methods, in the open</h2>
    <div class="flex flex-wrap gap-2 mt-6 fade-up" id="method-tabs">
      <button class="tab-btn active" data-tab="pipeline">Pipeline</button>
      <button class="tab-btn" data-tab="features">Features</button>
      <button class="tab-btn" data-tab="validation">Validation</button>
      <button class="tab-btn" data-tab="limitations">Limitations</button>
    </div>
    <div class="card p-6 mt-4 fade-up">
      <div class="tab-panel" data-panel="pipeline">
        <ol class="list-decimal ml-5 space-y-2 text-zinc-300 text-[15px] leading-relaxed">
          <li><strong>Census the present.</strong> Pull every public, available U.S. charging station from the NLR Alternative Fuel Stations API (83,546 stations) via <span class="font-mono text-sm">scripts/fetch_nlr_stations.py</span>.</li>
          <li><strong>Geocode to tracts.</strong> Spatially join stations to 2023 census tracts; aggregate Level 2 and DC fast ports per tract (83,528 of 83,546 matched).</li>
          <li><strong>Build features.</strong> Join ACS demographics, distribute ZIP-level data (EV registrations, business patterns) to tracts with population-density-weighted areal interpolation, measure highway distance and out-of-tract supply context.</li>
          <li><strong>Train &amp; honestly validate.</strong> Gradient-boosted trees with county-grouped cross-validation; report R²/MAE on unseen counties only.</li>
          <li><strong>Rank the gaps.</strong> Score every tract; the candidate list is zero-DCF tracts ordered by predicted ports. Full code: <span class="font-mono text-sm">models/build_model_v2.py</span>.</li>
        </ol>
      </div>
      <div class="tab-panel hidden" data-panel="features">
        <div class="grid md:grid-cols-2 gap-x-8 gap-y-2 text-[15px] text-zinc-300 leading-relaxed">
          <p><strong class="text-white">Demographics</strong> — population, population density, median household income (ACS 2023 5-year, tract level).</p>
          <p><strong class="text-white">EV registrations</strong> — plug-in vehicles by ZIP (WA Dept. of Licensing; CA DMV), allocated to tracts. CA + WA only for now.</p>
          <p><strong class="text-white">Employment</strong> — jobs and establishments by ZIP (Census ZIP Business Patterns 2022), allocated to tracts.</p>
          <p><strong class="text-white">Corridor access</strong> — distance from tract centroid to the nearest TIGER primary road (Interstates &amp; U.S. highways).</p>
          <p><strong class="text-white">Supply context</strong> — DC fast ports within 5 km and 10 km of the tract centroid (excluding the tract itself), and distance to the nearest out-of-tract DCFC station.</p>
          <p><strong class="text-white">Target</strong> — DC fast-charge ports physically located in the tract (NLR census, Oct 2026).</p>
        </div>
      </div>
      <div class="tab-panel hidden" data-panel="validation">
        <p class="text-zinc-300 text-[15px] leading-relaxed">Geospatial models fail quietly when validated naively: nearby tracts are near-duplicates, so random splits let the model "memorize the neighborhood" and report fantasy scores. Every ChargeAhead model is therefore validated with <strong class="text-white">GroupKFold cross-validation grouped by county</strong> — all tracts of a county sit entirely in train or entirely in test. Feature importance is permutation importance measured on a held-out sample, not training data. When a number on this page changes between versions, the change was earned under the same protocol.</p>
      </div>
      <div class="tab-panel hidden" data-panel="limitations">
        <ul class="list-disc ml-5 space-y-2 text-zinc-300 text-[15px] leading-relaxed">
          <li><strong class="text-white">Utilization is unobserved.</strong> No public dataset reports sessions/day per station; the model predicts where ports <em>are</em>, a proxy for where demand is — placement history and network strategy are baked into the target.</li>
          <li><strong class="text-white">Supply features cut both ways.</strong> "Ports within 5 km" is the strongest predictor, so v2 is best read as an infill model. Greenfield discovery is a separate family, in development.</li>
          <li><strong class="text-white">EV registration coverage is two states.</strong> CA/WA publish granular registration data; most states do not. Features are missing — honestly, as NaN — elsewhere.</li>
          <li><strong class="text-white">ZIP→tract allocation is approximate.</strong> Areal interpolation assumes demand follows population density within a ZIP.</li>
          <li><strong class="text-white">A ranking is not a site.</strong> Grid capacity, land cost, permitting and equity constraints decide real placements; the model produces a shortlist for humans.</li>
        </ul>
      </div>
    </div>
  </section>

  <div class="sep"></div>

  <!-- MODEL FAMILIES -->
  <section id="families" class="py-14">
    <h2 class="font-disp text-3xl font-bold fade-up">One project, many model families</h2>
    <p class="text-zinc-400 mt-2 max-w-3xl fade-up">ChargeAhead is a home for a family of placement models, each framed as its own research question with its own validation. New families land here as they mature.</p>
    <div class="grid md:grid-cols-2 gap-4 mt-8">
      <div class="card p-6 fade-up"><div class="flex items-center gap-3"><h3 class="font-semibold text-lg">Tract Demand — GBDT</h3><span class="badge badge-volt">Live · v2</span></div>
        <p class="text-zinc-400 text-sm mt-2 leading-relaxed">The flagship on this page: gradient-boosted trees predicting DC fast-charge ports for all 85,186 U.S. census tracts. Spatial-CV R² 0.209.</p></div>
      <div class="card p-6 fade-up"><div class="flex items-center gap-3"><h3 class="font-semibold text-lg">Greenfield Discovery</h3><span class="badge">In development</span></div>
        <p class="text-zinc-400 text-sm mt-2 leading-relaxed">The same target with supply-context features removed, isolating genuinely underserved demand from network clustering — the honest "where is nobody looking?" model.</p></div>
      <div class="card p-6 fade-up"><div class="flex items-center gap-3"><h3 class="font-semibold text-lg">Corridor Model</h3><span class="badge">Planned</span></div>
        <p class="text-zinc-400 text-sm mt-2 leading-relaxed">Highway-segment framing for corridor fast charging (NEVI-style): traffic volumes, stop spacing, and gap analysis along Interstates rather than residential tracts.</p></div>
      <div class="card p-6 fade-up"><div class="flex items-center gap-3"><h3 class="font-semibold text-lg">Utilization Model</h3><span class="badge">Blocked on data</span></div>
        <p class="text-zinc-400 text-sm mt-2 leading-relaxed">Predicting sessions per day — the target that actually matters commercially — the moment a network or city publishes station-level utilization openly. The pipeline is ready for it.</p></div>
    </div>
  </section>

  <div class="sep"></div>

  <!-- DATA -->
  <section id="data" class="py-14">
    <h2 class="font-disp text-3xl font-bold fade-up">Data sources — all public</h2>
    <div class="card mt-8 overflow-x-auto fade-up">
      <table class="explorer w-full">
        <thead><tr><th>Dataset</th><th>Publisher</th><th>Used for</th><th>Access</th></tr></thead>
        <tbody class="text-zinc-300">
          <tr><td>Alternative Fuel Stations</td><td>NLR (formerly NREL), U.S. DOE</td><td>Station census, port counts, target</td><td><a class="text-volt hover:underline" href="https://developer.nlr.gov/docs/transportation/alt-fuel-stations-v1/" target="_blank" rel="noopener">Free API key</a></td></tr>
          <tr><td>ACS 2023 5-year estimates</td><td>U.S. Census Bureau</td><td>Population, median income by tract</td><td><a class="text-volt hover:underline" href="https://www.census.gov/programs-surveys/acs" target="_blank" rel="noopener">Open</a></td></tr>
          <tr><td>TIGER/Line shapefiles 2023</td><td>U.S. Census Bureau</td><td>Tract &amp; ZCTA boundaries, primary roads</td><td><a class="text-volt hover:underline" href="https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html" target="_blank" rel="noopener">Open</a></td></tr>
          <tr><td>ZIP Business Patterns 2022</td><td>U.S. Census Bureau</td><td>Employment &amp; establishments by ZIP</td><td><a class="text-volt hover:underline" href="https://www.census.gov/programs-surveys/cbp.html" target="_blank" rel="noopener">Open</a></td></tr>
          <tr><td>Electric Vehicle Population Data</td><td>Washington State DOL</td><td>EV registrations by ZIP (WA)</td><td><a class="text-volt hover:underline" href="https://data.wa.gov/Transportation/Electric-Vehicle-Population-Data/f6w7-q2d2" target="_blank" rel="noopener">Open</a></td></tr>
          <tr><td>Vehicle Fuel Type Count by ZIP</td><td>California DMV</td><td>EV registrations by ZIP (CA)</td><td><a class="text-volt hover:underline" href="https://data.ca.gov/dataset/vehicle-fuel-type-count-by-zip-code" target="_blank" rel="noopener">Open</a></td></tr>
        </tbody>
      </table>
    </div>
    <div class="card p-6 mt-4 fade-up flex flex-wrap items-center gap-4">
      <div>
        <h3 class="font-semibold text-lg">Reproduce it, fork it, beat it</h3>
        <p class="text-zinc-400 text-sm mt-1 max-w-2xl">The full pipeline — fetch, features, training, validation, candidate ranking — is in the repository under an MIT license. Improvements, new model families, and new state registration sources are welcome contributions.</p>
      </div>
      <a class="btn btn-primary ml-auto" href="https://github.com/matthewjamesr/chargeahead" target="_blank" rel="noopener">github.com/matthewjamesr/chargeahead</a>
    </div>
  </section>
</main>

<footer class="border-t border-zinc-800/80 mt-4">
  <div class="max-w-7xl mx-auto px-5 py-8 flex flex-wrap gap-4 items-center text-sm text-zinc-500">
    <span class="flex items-center gap-2"><span class="inline-flex w-6 h-6 rounded bg-volt text-zinc-950 items-center justify-center"><svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M13 2 4.5 13.5H11L9.5 22 19 9.5h-6.5L13 2z"/></svg></span><span class="text-zinc-300 font-semibold">ChargeAhead</span></span>
    <span>Open research on EV charging placement · MIT licensed · Built entirely on public data</span>
    <span class="ml-auto font-mono text-xs">Model v2 · data as of Oct 2026</span>
  </div>
</footer>
<div id="tooltip" class="hidden card !rounded-lg px-3 py-2 text-sm text-zinc-200"></div>
"""

JS = r"""
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
/* ---------- animated background: drifting charge-field particles ---------- */
(function(){
  const cv=document.getElementById('bg-canvas'),ctx=cv.getContext('2d');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  let W,H,parts=[];
  function size(){W=cv.width=innerWidth;H=cv.height=innerHeight;}
  size();addEventListener('resize',size);
  const N=innerWidth<768?55:110;
  for(let i=0;i<N;i++)parts.push({x:Math.random()*innerWidth,y:Math.random()*innerHeight,s:.4+Math.random()*1.3,p:Math.random()*Math.PI*2,l:0});
  function tick(t){
    ctx.clearRect(0,0,W,H);
    for(const q of parts){
      const a=Math.sin(q.x*0.0016+t*0.00016+q.p)*1.2+Math.cos(q.y*0.0013-t*0.00011)*0.8;
      q.x+=Math.cos(a)*q.s;q.y+=Math.sin(a)*q.s;q.l++;
      if(q.x<-20)q.x=W+20;if(q.x>W+20)q.x=-20;if(q.y<-20)q.y=H+20;if(q.y>H+20)q.y=-20;
      ctx.beginPath();ctx.arc(q.x,q.y,1.6,0,7);
      ctx.fillStyle=q.p>4?'rgba(34,211,238,.5)':'rgba(163,230,53,.55)';ctx.fill();
    }
    for(let i=0;i<parts.length;i++)for(let j=i+1;j<parts.length;j++){
      const a=parts[i],b=parts[j],dx=a.x-b.x,dy=a.y-b.y,d=dx*dx+dy*dy;
      if(d<11500){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);
        ctx.strokeStyle='rgba(163,230,53,'+(0.10*(1-d/11500))+')';ctx.lineWidth=1;ctx.stroke();}
    }
    if(!reduced)requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
})();

/* ---------- reveal, counters, bars ---------- */
const io=new IntersectionObserver(es=>es.forEach(e=>{
  if(!e.isIntersecting)return;e.target.classList.add('in');
  e.target.querySelectorAll('[data-count]').forEach(el=>{
    const target=+el.dataset.count,t0=performance.now();
    (function step(t){const p=Math.min(1,(t-t0)/1300);el.textContent=Math.round(target*(1-Math.pow(1-p,3))).toLocaleString();if(p<1)requestAnimationFrame(step);})(t0);
  });
  e.target.querySelectorAll('.bar-fill').forEach(b=>b.style.width=b.dataset.w+'%');
  io.unobserve(e.target);
}),{threshold:.18});
document.querySelectorAll('.fade-up, .card').forEach(el=>io.observe(el));

/* ---------- feature importance ---------- */
const IMP=[
 ['DC fast ports within 5 km',0.313,'Charging already near this tract (its own ports excluded). Networks expand where they already are — the strongest single signal.'],
 ['Population density',0.255,'People per square mile. Dense places support more fast charging than sprawling ones at the same population.'],
 ['Distance to nearest DCFC',0.180,'How far the closest existing fast charger is. Proximity predicts more build-out — clustering again.'],
 ['Distance to primary road',0.098,'Kilometres from the tract centre to the nearest Interstate or U.S. highway. Corridor access matters for fast charging.'],
 ['DC fast ports within 10 km',0.055,'The wider supply ring — regional build-out momentum around the tract.'],
 ['EV registrations (log)',0.055,'Registered plug-in vehicles allocated from ZIP data (CA/WA only so far). Where the cars are.'],
 ['Establishments',0.044,'Count of businesses in the tract (ZIP Business Patterns) — retail and services host chargers.'],
 ['Jobs (log)',0.038,'Employment allocated from ZIP data — workplaces are charging destinations.'],
 ['EVs per 1,000 residents',0.033,'Registration intensity rather than raw count — adoption culture, not just size.'],
 ['Median household income',0.017,'ACS median income. Real but weak once the other features are known.'],
 ['Population (log)',0.013,'Raw tract population. Density carries most of its signal.'],
];
const imp=document.getElementById('importance'),tip=document.getElementById('tooltip');
IMP.forEach(([name,val,gloss])=>{
  const row=document.createElement('div');
  row.innerHTML='<div class="flex justify-between text-sm mb-1"><span class="text-zinc-300">'+name+'</span><span class="num text-zinc-400">+'+val.toFixed(2)+'</span></div><div class="bar-track"><div class="bar-fill" data-w="'+(val/0.313*100).toFixed(1)+'"></div></div>';
  row.addEventListener('mousemove',e=>{tip.textContent=gloss;tip.classList.remove('hidden');tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+12)+'px';});
  row.addEventListener('mouseleave',()=>tip.classList.add('hidden'));
  imp.appendChild(row);
  io.observe(row);
});

/* ---------- methods tabs ---------- */
document.querySelectorAll('#method-tabs .tab-btn').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('#method-tabs .tab-btn').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.toggle('hidden',p.dataset.panel!==b.dataset.tab));
}));

/* ---------- candidate explorer ---------- */
const CANDS=__DATA__;
const fmt=n=>n==null?'—':Math.round(n).toLocaleString();
const money=n=>n==null?'—':'$'+Math.round(n).toLocaleString();
const map=L.map('map',{scrollWheelZoom:false}).setView([37.5,-96],4);
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'© OpenStreetMap contributors © CARTO',maxZoom:18}).addTo(map);
map.on('focus',()=>map.scrollWheelZoom.enable());map.on('blur',()=>map.scrollWheelZoom.disable());
let markers={},filtered=CANDS.slice();

const stateSel=document.getElementById('f-state');
[...new Set(CANDS.map(c=>c.state_name))].sort().forEach(s=>{const o=document.createElement('option');o.value=s;o.textContent=s;stateSel.appendChild(o);});

function render(){
  const st=stateSel.value,q=document.getElementById('f-search').value.trim().toLowerCase(),
        min=+document.getElementById('f-min').value,sort=document.getElementById('f-sort').value;
  document.getElementById('f-min-val').textContent=min;
  filtered=CANDS.filter(c=>(!st||c.state_name===st)&&c.predicted_dcfc>=min&&
    (!q||(c.county_name+' '+c.tract+' '+c.GEOID).toLowerCase().includes(q)));
  filtered.sort((a,b)=>(b[sort]??-1)-(a[sort]??-1));
  document.getElementById('f-count').textContent=filtered.length+' tracts shown';
  const tb=document.getElementById('cand-body');tb.innerHTML='';
  Object.values(markers).forEach(m=>map.removeLayer(m));markers={};
  filtered.forEach((c,i)=>{
    const tr=document.createElement('tr');tr.className='row';tr.dataset.geoid=c.GEOID;
    tr.innerHTML='<td class="text-zinc-500">'+(i+1)+'</td><td class="font-mono text-xs">'+c.GEOID+'<br><span class="text-zinc-500">Tract '+c.tract+'</span></td><td>'+c.county_name+'</td><td>'+c.state_name+'</td><td class="num font-semibold text-volt">'+c.predicted_dcfc+'</td><td>'+fmt(c.population)+'</td><td>'+money(c.median_income)+'</td><td>'+fmt(c.ev_regs)+'</td><td>'+fmt(c.jobs)+'</td><td>'+(c.dist_road_km??'—')+'</td><td>'+(c.dist_nearest_dcfc_km??'—')+'</td>';
    tr.addEventListener('click',()=>select(c,true));
    tb.appendChild(tr);
    const m=L.circleMarker([c.lat,c.lon],{radius:4+c.predicted_dcfc*0.55,color:'#a3e635',weight:1,fillColor:'#a3e635',fillOpacity:.45})
      .bindPopup('<strong>Tract '+c.tract+'</strong><br>'+c.county_name+', '+c.state_name+'<br>Predicted DCFC ports: <strong>'+c.predicted_dcfc+'</strong><br>Nearest DCFC today: '+c.dist_nearest_dcfc_km+' km');
    m.on('click',()=>select(c,false));m.addTo(map);markers[c.GEOID]=m;
  });
}
function select(c,fly){
  document.querySelectorAll('#cand-body tr').forEach(r=>r.classList.toggle('sel',r.dataset.geoid===c.GEOID));
  const row=document.querySelector('#cand-body tr[data-geoid="'+c.GEOID+'"]');
  if(row)row.scrollIntoView({block:'nearest'});
  if(fly&&markers[c.GEOID]){map.flyTo([c.lat,c.lon],10,{duration:.8});markers[c.GEOID].openPopup();}
}
['f-state','f-search','f-min','f-sort'].forEach(id=>document.getElementById(id).addEventListener('input',render));
render();
</script>
</body>
</html>
"""

html = (HEAD + RESULTS + JS).replace("__DATA__", DATA)
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("docs/index.html:", len(html), "bytes")

