#!/usr/bin/env python3
"""Generate docs/index.html (GitHub Pages landing + results dashboard)."""
import json

cands = json.load(open("data/dashboard_candidates.json"))
DATA = json.dumps(cands)
POLYS = json.dumps(json.load(open("data/candidate_polygons.json")))

HEAD = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ChargeAhead — Open models for EV charging placement</title>
<meta name="description" content="Open, data-driven models for deciding where EV charging should go next. Tract-level DC fast-charging demand prediction for all 85,186 U.S. census tracts, built entirely on public data.">
<meta name="keywords" content="EV charging placement, DC fast charging, DCFC siting, electric vehicle infrastructure, census tract model, gradient boosting, hurdle model, open data, OpenStreetMap, LODES, AADT, ChargeAhead">
<meta name="author" content="Matthew Reichardt">
<meta name="robots" content="index, follow">
<meta name="theme-color" content="#09090b">
<link rel="canonical" href="https://www.matthewreichardt.com/chargeahead/">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ChargeAhead">
<meta property="og:title" content="ChargeAhead — Open models for EV charging placement">
<meta property="og:description" content="Tract-level DC fast-charging demand prediction for all 85,186 U.S. census tracts, built entirely on public data. Current model M4: spatial-CV R² 0.365.">
<meta property="og:url" content="https://www.matthewreichardt.com/chargeahead/">
<meta property="og:image" content="https://www.matthewreichardt.com/chargeahead/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="ChargeAhead — Open models for EV charging placement">
<meta name="twitter:description" content="Tract-level DC fast-charging demand prediction for all 85,186 U.S. census tracts, built entirely on public data. Current model M4: spatial-CV R² 0.365.">
<meta name="twitter:image" content="https://www.matthewreichardt.com/chargeahead/og-image.png">
<script type="application/ld+json">
{"@context":"https://schema.org","@graph":[
 {"@type":"WebSite","name":"ChargeAhead","url":"https://www.matthewreichardt.com/chargeahead/","description":"Open, data-driven models for deciding where EV charging should go next."},
 {"@type":"Dataset","name":"ChargeAhead tract-level DC fast-charging candidate rankings (model M4)","description":"Predicted DC fast-charge ports for U.S. census tracts with no existing DC fast charging, from a two-stage hurdle gradient-boosting model trained on public data (NLR station census, Census ACS/LODES, state EV registrations, FHWA HPMS traffic counts, OpenStreetMap).","url":"https://www.matthewreichardt.com/chargeahead/","license":"https://opensource.org/licenses/MIT","creator":{"@type":"Person","name":"Matthew Reichardt"},"distribution":[{"@type":"DataDownload","encodingFormat":"text/csv","contentUrl":"https://github.com/matthewjamesr/chargeahead/blob/main/results/candidate_tracts_dcfc_m4_top500.csv"},{"@type":"DataDownload","encodingFormat":"application/octet-stream","contentUrl":"https://github.com/matthewjamesr/chargeahead/blob/main/models/m4_hurdle.joblib"}]}
]}
</script>
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
  .card{background:rgba(24,24,27,.72);border:1px solid #27272a;border-radius:.75rem;box-shadow:0 1px 2px rgba(0,0,0,.4);backdrop-filter:blur(8px)}
  .card:hover{border-color:#3f3f46}
  /* shadcn Badge */
  .badge{display:inline-flex;align-items:center;gap:.35rem;border:1px solid #3f3f46;border-radius:.375rem;padding:.125rem .625rem;font-size:.75rem;font-weight:600;letter-spacing:.02em;color:#d4d4d8;background:rgba(39,39,42,.6)}
  .dt-badge{display:inline-flex;align-items:center;border:1px solid #3f3f46;border-radius:.375rem;padding:.125rem .55rem;font-size:.7rem;font-weight:500;color:#d4d4d8;background:rgba(39,39,42,.5);white-space:nowrap}
  .badge-volt{border-color:#a3e635;color:#a3e635;background:rgba(163,230,53,.08)}
  /* shadcn Button */
  .btn{display:inline-flex;align-items:center;justify-content:center;gap:.5rem;border-radius:.375rem;font-weight:500;font-size:.875rem;line-height:1.25rem;padding:.5rem 1rem;transition:background-color .15s,color .15s,border-color .15s;white-space:nowrap}
  .btn:focus-visible{outline:none;box-shadow:0 0 0 2px #09090b,0 0 0 4px #a3e635}
  .btn-primary{background:#a3e635;color:#09090b}.btn-primary:hover{background:#b7ec55}
  .btn-outline{border:1px solid #27272a;color:#e4e4e7;background:transparent}.btn-outline:hover{background:#27272a;color:#fafafa}
  /* shadcn Tabs */
  #method-tabs{display:inline-flex;align-items:center;gap:.25rem;background:#18181b;border-radius:.5rem;padding:.25rem}
  .tab-btn{border:0;border-radius:.375rem;padding:.375rem .75rem;font-size:.875rem;font-weight:500;color:#a1a1aa;background:transparent;transition:all .15s;cursor:pointer}
  .tab-btn.active{background:#09090b;color:#fafafa;box-shadow:0 1px 2px rgba(0,0,0,.4)}
  /* shadcn Select */
  .sc-native{display:none!important}
  .sc-wrap{position:relative;display:inline-block}
  .sc-trigger{display:flex;height:2.25rem;align-items:center;justify-content:space-between;gap:.5rem;border-radius:.375rem;border:1px solid #27272a;background:#09090b;padding:.5rem .75rem;font-size:.875rem;color:#e4e4e7;box-shadow:0 1px 2px rgba(0,0,0,.3);cursor:pointer;min-width:9rem}
  .sc-trigger:focus-visible{outline:none;box-shadow:0 0 0 2px #09090b,0 0 0 4px #a3e635}
  .sc-trigger svg{opacity:.5;flex:none;transition:transform .15s}
  .sc-trigger[aria-expanded="true"] svg{transform:rotate(180deg)}
  .sc-content{position:absolute;top:calc(100% + .25rem);left:0;z-index:50;min-width:100%;max-height:18rem;overflow-y:auto;border-radius:.375rem;border:1px solid #27272a;background:#18181b;color:#e4e4e7;box-shadow:0 10px 24px rgba(0,0,0,.5);padding:.25rem;animation:sc-in .14s ease}
  @keyframes sc-in{from{opacity:0;transform:scale(.97) translateY(-2px)}to{opacity:1;transform:scale(1) translateY(0)}}
  .sc-item{position:relative;display:flex;width:100%;align-items:center;border-radius:.25rem;padding:.375rem 2rem .375rem .5rem;font-size:.875rem;cursor:pointer;user-select:none;white-space:nowrap}
  .sc-item[data-hl="1"]{background:#27272a}
  .sc-item .sc-check{position:absolute;right:.5rem;display:none}
  .sc-item[aria-selected="true"] .sc-check{display:block}
  /* shadcn icon Button (ghost) + explorer reset visibility */
  .sc-icon-btn{display:inline-flex;width:2.25rem;height:2.25rem;flex:none;align-items:center;justify-content:center;border-radius:.375rem;color:#a1a1aa;background:transparent;transition:background-color .15s,color .15s,opacity .18s,transform .18s;cursor:pointer}
  .sc-icon-btn:hover{background:#27272a;color:#fafafa}
  .sc-icon-btn:focus-visible{outline:none;box-shadow:0 0 0 2px #09090b,0 0 0 4px #a3e635}
  .f-reset{opacity:0;pointer-events:none;transform:scale(.85)}
  .f-reset.show{opacity:1;pointer-events:auto;transform:scale(1)}
  /* shadcn Checkbox */
  .sc-checkbox{display:inline-flex;width:1rem;height:1rem;flex:none;align-items:center;justify-content:center;border-radius:.25rem;border:1px solid #52525b;background:transparent;cursor:pointer;vertical-align:-0.15rem}
  .sc-checkbox[data-state="checked"]{background:#a3e635;border-color:#a3e635;color:#09090b}
  .sc-checkbox:focus-visible{outline:none;box-shadow:0 0 0 2px #09090b,0 0 0 4px #a3e635}
  /* shadcn Slider */
  .sc-slider{position:relative;display:inline-flex;align-items:center;height:1.25rem;width:6.5rem;margin-left:.75rem;cursor:pointer;touch-action:none}
  .sc-wrap:has(>#f-state){width:10rem;flex:none}
  .sc-wrap:has(>#f-sort){width:13.5rem;flex:none}
  .sc-trigger{width:100%}
  .sc-trigger .sc-label{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .sc-slider .sc-track{position:relative;height:.375rem;width:100%;border-radius:999px;background:#27272a;overflow:hidden}
  .sc-slider .sc-range{position:absolute;height:100%;background:#a3e635;border-radius:999px}
  .sc-thumb{position:absolute;width:1rem;height:1rem;border-radius:999px;background:#fafafa;border:2px solid #a3e635;box-shadow:0 1px 2px rgba(0,0,0,.4);transform:translateX(-50%);cursor:grab}
  .sc-thumb:focus-visible{outline:none;box-shadow:0 0 0 2px #09090b,0 0 0 4px #a3e635}
  .bar-track{background:#27272a;border-radius:999px;height:.65rem;overflow:hidden}
  .bar-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#65a30d,#a3e635);width:0;transition:width 1.1s cubic-bezier(.22,1,.36,1)}
  .bar-fill.dim{background:linear-gradient(90deg,#3f3f46,#52525b)}
  table.explorer th{font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:#a1a1aa;text-align:left;padding:.55rem .7rem;border-bottom:1px solid #27272a;cursor:pointer;white-space:nowrap}
  table.explorer td{padding:.55rem .7rem;border-bottom:1px solid #1c1c1f;font-size:.85rem;white-space:nowrap}
  table.explorer tr.row:hover td{background:rgba(163,230,53,.05)}
  table.explorer tr.sel td{background:rgba(163,230,53,.12)}
  /* shadcn Input */
  input[type=text]{display:flex;height:2.25rem;background:#09090b;border:1px solid #27272a;border-radius:.375rem;padding:.5rem .75rem;font-size:.875rem;color:#e4e4e7;box-shadow:0 1px 2px rgba(0,0,0,.3)}
  input[type=text]::placeholder{color:#71717a}
  input[type=text]:focus{outline:none;border-color:#a3e635;box-shadow:0 0 0 2px rgba(163,230,53,.25)}
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
      <div class="card p-5 fade-up"><div class="num text-3xl md:text-4xl font-bold text-volt">0.365</div><div class="text-zinc-400 text-sm mt-1">spatial-CV R² (model M4) — vs 0.007 for demographics alone</div></div>
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
        <h2 class="font-disp text-3xl font-bold fade-up">Results — model M4, DC fast charging</h2>
        <p class="text-zinc-400 mt-2 max-w-3xl fade-up">Target: DC fast-charge ports per census tract. Algorithm: a two-stage <strong class="text-zinc-200">hurdle model</strong> — a gradient-boosted classifier for "any DCFC at all" × a gradient-boosted regressor for "how many, given some" (scikit-learn). Validation: 5-fold cross-validation grouped by county, so the model is always scored on counties it has never seen.</p>
      </div>
      <span class="badge badge-volt ml-auto fade-up">M4 · Oct 2026</span>
    </div>

    <div class="grid lg:grid-cols-2 gap-4 mt-8">
      <div class="card p-6 fade-up">
        <h3 class="font-semibold">Explained variance (R²), held-out counties</h3>
        <div class="mt-5 space-y-5">
          <div>
            <div class="flex justify-between text-sm mb-1.5"><span class="text-zinc-300">M4 — M3 + nationwide POI buffers, tract AADT, state encoding, EV corridors</span><span class="num font-semibold text-volt">0.365</span></div>
            <div class="bar-track"><div class="bar-fill" data-w="100"></div></div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1.5"><span class="text-zinc-400">M3 — hurdle + LODES + AADT + OpenStreetMap land use</span><span class="num font-semibold text-zinc-400">0.335</span></div>
            <div class="bar-track"><div class="bar-fill dim" data-w="91.8"></div></div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1.5"><span class="text-zinc-400">M2 — single regressor, full v2 features</span><span class="num font-semibold text-zinc-400">0.209</span></div>
            <div class="bar-track"><div class="bar-fill dim" data-w="57.3"></div></div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1.5"><span class="text-zinc-400">M0 — demographics only</span><span class="num font-semibold text-zinc-400">0.007</span></div>
            <div class="bar-track"><div class="bar-fill dim" data-w="1.9"></div></div>
          </div>
        </div>
        <p class="text-zinc-500 text-sm mt-5 leading-relaxed">Two kinds of wins so far. <strong class="text-zinc-300">Architecture:</strong> the hurdle split beat every loss and tuning variant — Poisson loss collapsed at R² −2.2, and a Tweedie objective now carries the sizing stage. <strong class="text-zinc-300">Land use, completed:</strong> M4's OpenStreetMap coverage is nationwide — 80,794 tracts across all five Geofabrik regions — and three-dimensional: in-tract counts, 1/3/5 km buffers, and densities, joined by tract-level traffic counts and distance to the nearest federally designated EV corridor. Mean absolute error is down to <strong class="text-zinc-300">0.99 ports per tract</strong> from 1.61 at baseline. Gains have flattened over the last three development drafts (each under +0.005 R²); two further data families — LODES job-growth trends and 141.8M Microsoft building footprints — were tested and not shipped (details in the model card).</p>
      </div>

      <div class="card p-6 fade-up">
        <h3 class="font-semibold">What drives placement? <span class="text-zinc-500 font-normal text-sm">— gain importance, both hurdle stages, hover for plain English</span></h3>
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
      <div class="flex flex-wrap xl:flex-nowrap gap-3 items-center">
        <select id="f-state"><option value="">All states</option></select>
        <input type="text" id="f-search" placeholder="Search county or tract…" class="w-44">
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
        <div class="text-sm text-zinc-400 flex items-center gap-2">
          <input type="checkbox" id="f-polys" checked class="accent-lime-400 w-4 h-4"> <span data-check-text class="cursor-pointer select-none">Tract boundaries</span></div>
        <span class="ml-auto flex items-center gap-2">
          <span class="badge" id="f-count"></span>
          <button type="button" id="f-reset" class="sc-icon-btn f-reset" title="Reset filters and map view" aria-label="Reset filters and map view">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
          </button>
        </span>
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
      <p class="text-zinc-500 text-xs mt-3">* EV registrations now cover six states (CA, WA, NY, MD, PA, VA — state open-data portals; NY is battery-electric only, VA is county-level 2022); blank elsewhere — the model handles the missing values natively rather than inventing them.</p>
    </div>
  </section>

  <div class="sep"></div>

  <!-- METHODS -->
  <section id="methods" class="py-14">
    <h2 class="font-disp text-3xl font-bold fade-up">Methods, in the open</h2>
    <div class="mt-6 fade-up" id="method-tabs">
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
          <li><strong>Rank the gaps.</strong> Score every tract; the candidate list is zero-DCF tracts ordered by predicted ports. Full code: <span class="font-mono text-sm">scripts/build_model_m4.py</span>.</li>
        </ol>
      </div>
      <div class="tab-panel hidden" data-panel="features">
        <div class="grid md:grid-cols-2 gap-x-8 gap-y-2 text-[15px] text-zinc-300 leading-relaxed">
          <p><strong class="text-white">Demographics</strong> — population, population density, median household income (ACS 2023 5-year, tract level).</p>
          <p><strong class="text-white">EV registrations</strong> — plug-in vehicles by ZIP for CA, WA, NY, MD, PA (state open-data portals) and by county for VA, allocated to tracts.</p>
          <p><strong class="text-white">Employment</strong> — jobs and establishments by ZIP (Census ZIP Business Patterns 2022), plus tract-native workplace jobs and resident workers from LEHD LODES8 2023, including the net importer balance.</p>
          <p><strong class="text-white">Traffic</strong> — arterial traffic from FHWA HPMS 2024 at two grains — county aggregates (max + length-weighted mean AADT) and a tract-level extraction from 3.84M sections with geometry (74.6% of tracts contain an arterial section) — plus EV corridors: distance to the nearest BTS NTAD-designated EV corridor with 1-mile/5-mile flags.</p>
          <p><strong class="text-white">Land use (OpenStreetMap)</strong> — fuel stations, parking, retail and lodging POIs per tract plus distance to the nearest fuel station, parsed from all five Geofabrik US regions (80,794 tracts), as in-tract counts plus 1/3/5 km buffer totals and per-km² densities from 2.48M geocoded POIs.</p>
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
          <li><strong class="text-white">Supply features cut both ways.</strong> "Ports within 5 km" is the strongest predictor, so the current model is best read as an infill model. Greenfield discovery is a separate family, in development.</li>
          <li><strong class="text-white">EV registration coverage is six states, not fifty.</strong> CA, WA, NY, MD and PA publish ZIP-level counts (NY is battery-electric only); VA publishes only county-level counts through 2022 — too coarse and too old for the harmonized features, so VA is held out. Together the six cover about 40% of tracts; ten other priority states were checked and publish nothing at sub-state geography. The features are missing — honestly, as NaN — elsewhere.</li>
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
      <div class="card p-6 fade-up"><div class="flex items-center gap-3"><h3 class="font-semibold text-lg">Tract Demand — Hurdle GBDT</h3><span class="badge badge-volt">Live · M4</span></div>
        <p class="text-zinc-400 text-sm mt-2 leading-relaxed">The flagship on this page: a two-stage hurdle model (siting classifier × sizing regressor) predicting DC fast-charge ports for all 85,186 U.S. census tracts. Spatial-CV R² 0.365, MAE 0.99 — a LightGBM hurdle ensemble with nationwide land use, tract-level traffic, and EV-corridor proximity.</p></div>
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
    <div class="card mt-8 fade-up">
      <div class="flex flex-wrap items-center gap-3 p-4 border-b border-zinc-800">
        <div class="relative">
          <svg class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
          <input id="dt-search" type="text" placeholder="Search datasets…" autocomplete="off"
            class="h-9 w-64 rounded-md border border-zinc-800 bg-zinc-950 pl-9 pr-3 text-sm text-zinc-200 placeholder:text-zinc-500 outline-none focus:border-lime-400/60 focus:ring-2 focus:ring-lime-400/20 transition">
        </div>
        <select id="dt-type" class="h-9 rounded-md border border-zinc-800 bg-zinc-950 px-2.5 text-sm text-zinc-200 outline-none focus:border-lime-400/60 focus:ring-2 focus:ring-lime-400/20 transition cursor-pointer">
          <option value="">All data types</option>
          <option value="stations">Stations</option>
          <option value="demographics">Demographics</option>
          <option value="geography">Geography</option>
          <option value="employment">Employment</option>
          <option value="registrations">Registrations</option>
          <option value="traffic">Traffic</option>
          <option value="landuse">Land use</option>
        </select>
        <span id="dt-count" class="ml-auto text-xs text-zinc-500 font-mono"></span>
      </div>
      <div class="overflow-x-auto">
      <table class="explorer w-full" id="dt-table">
        <thead><tr><th>Dataset</th><th>Publisher</th><th>Type</th><th>Used for</th><th>Vintage</th><th>Access</th></tr></thead>
        <tbody class="text-zinc-300">
          <tr data-type="stations"><td>Alternative Fuel Stations</td><td>NLR (formerly NREL), U.S. DOE</td><td><span class="dt-badge">Stations</span></td><td>Station census, port counts, target</td><td class="num text-zinc-400">Oct 2026 pull</td><td><a class="text-volt hover:underline" href="https://developer.nlr.gov/docs/transportation/alt-fuel-stations-v1/" target="_blank" rel="noopener">Free API key</a></td></tr>
          <tr data-type="demographics"><td>ACS 5-year estimates</td><td>U.S. Census Bureau</td><td><span class="dt-badge">Demographics</span></td><td>Population, median income by tract</td><td class="num text-zinc-400">2023 (2019–2023)</td><td><a class="text-volt hover:underline" href="https://www.census.gov/programs-surveys/acs" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="geography"><td>TIGER/Line shapefiles</td><td>U.S. Census Bureau</td><td><span class="dt-badge">Geography</span></td><td>Tract &amp; ZCTA boundaries, primary roads</td><td class="num text-zinc-400">2023</td><td><a class="text-volt hover:underline" href="https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="employment"><td>ZIP Business Patterns</td><td>U.S. Census Bureau</td><td><span class="dt-badge">Employment</span></td><td>Establishments by ZIP</td><td class="num text-zinc-400">2022</td><td><a class="text-volt hover:underline" href="https://www.census.gov/programs-surveys/cbp.html" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="employment"><td>LODES8 (LEHD Origin-Destination Employment Statistics)</td><td>U.S. Census Bureau</td><td><span class="dt-badge">Employment</span></td><td>Workplace jobs &amp; resident workers by tract</td><td class="num text-zinc-400">2023</td><td><a class="text-volt hover:underline" href="https://lehd.ces.census.gov/data/lodes/" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="registrations"><td>Electric Vehicle Population Data</td><td>Washington State DOL</td><td><span class="dt-badge">Registrations</span></td><td>EV registrations by ZIP (WA)</td><td class="num text-zinc-400">Oct 2026 snapshot</td><td><a class="text-volt hover:underline" href="https://data.wa.gov/Transportation/Electric-Vehicle-Population-Data/f6w7-q2d2" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="registrations"><td>Vehicle Fuel Type Count by ZIP</td><td>California DMV</td><td><span class="dt-badge">Registrations</span></td><td>EV registrations by ZIP (CA)</td><td class="num text-zinc-400">2025 counts (Jan 2026 file)</td><td><a class="text-volt hover:underline" href="https://data.ca.gov/dataset/vehicle-fuel-type-count-by-zip-code" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="registrations"><td>Vehicle, Snowmobile and Boat Registrations</td><td>New York State (data.ny.gov)</td><td><span class="dt-badge">Registrations</span></td><td>EV registrations by ZIP (NY — battery-electric only)</td><td class="num text-zinc-400">Oct 2026 snapshot</td><td><a class="text-volt hover:underline" href="https://data.ny.gov/d/w4pv-hbkt" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="registrations"><td>Electric and Plug-in Hybrid Vehicle Registrations</td><td>Maryland DOT MVA (opendata.maryland.gov)</td><td><span class="dt-badge">Registrations</span></td><td>EV registrations by ZIP (MD)</td><td class="num text-zinc-400">Aug 2026 (latest month)</td><td><a class="text-volt hover:underline" href="https://opendata.maryland.gov/d/tugr-unu9" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="registrations"><td>EV Registrations by ZIP (ArcGIS service)</td><td>PennDOT</td><td><span class="dt-badge">Registrations</span></td><td>EV registrations by ZIP (PA)</td><td class="num text-zinc-400">2026 (latest quarter)</td><td><a class="text-volt hover:underline" href="https://gis.penndot.pa.gov/gis/rest/services/opendata/evregistrationszip/MapServer" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="registrations"><td>EV Registrations by Jurisdiction</td><td>Virginia Open Data (U.S. DOE-sourced)</td><td><span class="dt-badge">Registrations</span></td><td>EV registrations by county (VA — held out of the harmonized features: county grain, older vintage)</td><td class="num text-zinc-400">2008–2022</td><td><a class="text-volt hover:underline" href="https://data.virginia.gov/dataset/virginia-electric-vehicle-ev" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="traffic"><td>HPMS Spatial All Sections</td><td>FHWA (datahub.transportation.gov)</td><td><span class="dt-badge">Traffic</span></td><td>Arterial traffic counts (AADT) by county and by tract</td><td class="num text-zinc-400">2024 file (2023 AADT)</td><td><a class="text-volt hover:underline" href="https://datahub.transportation.gov/d/42um-tgh5" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="traffic"><td>Alternative Fuel Corridors</td><td>Bureau of Transportation Statistics (NTAD)</td><td><span class="dt-badge">Traffic</span></td><td>EV-designated corridor polylines: tract distance to nearest + 1 mi / 5 mi flags (2,180 segments, 83,366 mi)</td><td class="num text-zinc-400">2026</td><td><a class="text-volt hover:underline" href="https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/NTAD_Alternative_Fuel_Corridors/FeatureServer" target="_blank" rel="noopener">Open</a></td></tr>
          <tr data-type="landuse"><td>OpenStreetMap extracts — all five US regions</td><td>OpenStreetMap contributors, via Geofabrik</td><td><span class="dt-badge">Land use</span></td><td>Points of interest by tract and buffer: fuel, parking, retail, lodging</td><td class="num text-zinc-400">Oct 2026</td><td><a class="text-volt hover:underline" href="https://download.geofabrik.de/north-america.html" target="_blank" rel="noopener">Open</a></td></tr>
          <tr id="dt-empty" class="hidden"><td colspan="6" class="text-center text-zinc-500 py-8">No datasets match your search.</td></tr>
        </tbody>
      </table>
      </div>
    </div>
    <script>
    (function(){
      const q = document.getElementById('dt-search'),
            sel = document.getElementById('dt-type'),
            rows = Array.from(document.querySelectorAll('#dt-table tbody tr[data-type]')),
            empty = document.getElementById('dt-empty'),
            count = document.getElementById('dt-count');
      function apply(){
        const text = q.value.trim().toLowerCase(), type = sel.value;
        let shown = 0;
        rows.forEach(r => {
          const ok = (!type || r.dataset.type === type) &&
                     (!text || r.textContent.toLowerCase().includes(text));
          r.classList.toggle('hidden', !ok);
          if (ok) shown++;
        });
        empty.classList.toggle('hidden', shown > 0);
        count.textContent = shown + ' of ' + rows.length + ' datasets';
      }
      q.addEventListener('input', apply);
      sel.addEventListener('change', apply);
      apply();
    })();
    </script>
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
    <span class="ml-auto font-mono text-xs">Model M4 · data as of Oct 2026</span>
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
 ['DC fast ports within 5 km',0.130,'Charging already near this tract (its own ports excluded). Networks expand where they already are — the strongest single signal in every version so far.'],
 ['Retail POIs (OpenStreetMap)',0.118,'Shops in the tract. Commercial land use remains the signal tract demographics were missing — now measured nationwide.'],
 ['Workplace jobs (LODES)',0.055,'Jobs located in the tract — daytime demand, from LEHD LODES workplace counts.'],
 ['Distance to nearest DCFC',0.044,'How far the closest existing fast charger is. Proximity predicts more build-out — clustering again.'],
 ['Peak arterial traffic in tract (AADT)',0.042,'The busiest arterial section inside the tract itself (FHWA HPMS) — new in M4, replacing county-only traffic.'],
 ['Distance to EV corridor',0.033,'Kilometres to the nearest federally designated EV corridor (BTS NTAD) — new in M4; NEVI-funded build-out follows these lines.'],
 ['Distance to primary road',0.027,'Kilometres from the tract centre to the nearest Interstate or U.S. highway — corridor access.'],
 ['Distance to nearest fuel station',0.022,'The incumbent refuelling footprint marks proven travel-stop locations.'],
 ['Hotels &amp; lodging POIs',0.022,'Tourism=hotel/motel in OpenStreetMap — overnight stops are natural fast-charging hosts.'],
 ['Population density',0.022,'People per square kilometre — a supporting signal once real land use is known.'],
 ['Median household income',0.021,'ACS median income for the tract.'],
 ['State average ports (target encoding)',0.021,'How built-out the tract\u2019s state is overall — computed inside training folds only, so it cannot leak the answer.'],
];
const imp=document.getElementById('importance'),tip=document.getElementById('tooltip');
IMP.forEach(([name,val,gloss])=>{
  const row=document.createElement('div');
  row.innerHTML='<div class="flex justify-between text-sm mb-1"><span class="text-zinc-300">'+name+'</span><span class="num text-zinc-400">+'+val.toFixed(2)+'</span></div><div class="bar-track"><div class="bar-fill" data-w="'+(val/0.232*100).toFixed(1)+'"></div></div>';
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
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',{attribution:'Esri, HERE, Garmin, OpenStreetMap contributors',maxZoom:16}).addTo(map);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',{maxZoom:16}).addTo(map);
map.on('focus',()=>map.scrollWheelZoom.enable());map.on('blur',()=>map.scrollWheelZoom.disable());
let markers={},polys={},filtered=CANDS.slice();
const POLYS=__POLYS__;
function polyStyle(c,sel){return{color:sel?'#bef264':'#a3e635',weight:sel?2.5:1.2,opacity:sel?1:.75,fillColor:'#a3e635',fillOpacity:sel?.28:.10};}

const stateSel=document.getElementById('f-state');
[...new Set(CANDS.map(c=>c.state_name))].sort().forEach(s=>{const o=document.createElement('option');o.value=s;o.textContent=s;stateSel.appendChild(o);});

function render(){
  const st=stateSel.value,q=document.getElementById('f-search').value.trim().toLowerCase(),
        min=+document.getElementById('f-min').value,sort=document.getElementById('f-sort').value;
  document.getElementById('f-min-val').textContent=min;
  filtered=CANDS.filter(c=>(!st||c.state_name===st)&&c.predicted_dcfc>=min&&
    (!q||(c.county_name+' '+c.tract+' '+c.GEOID).toLowerCase().includes(q)));
  filtered.sort((a,b)=>(b[sort]??-1)-(a[sort]??-1));
  document.getElementById('f-count').textContent=filtered.length+' shown';
  const tb=document.getElementById('cand-body');tb.innerHTML='';
  Object.values(markers).forEach(m=>map.removeLayer(m));markers={};
  Object.values(polys).forEach(m=>map.removeLayer(m));polys={};
  const showPolys=document.getElementById('f-polys').checked;
  filtered.forEach((c,i)=>{
    const tr=document.createElement('tr');tr.className='row';tr.dataset.geoid=c.GEOID;
    tr.innerHTML='<td class="text-zinc-500">'+(i+1)+'</td><td class="font-mono text-xs">'+c.GEOID+'<br><span class="text-zinc-500">Tract '+c.tract+'</span></td><td>'+c.county_name+'</td><td>'+c.state_name+'</td><td class="num font-semibold text-volt">'+c.predicted_dcfc+'</td><td>'+fmt(c.population)+'</td><td>'+money(c.median_income)+'</td><td>'+fmt(c.ev_regs)+'</td><td>'+fmt(c.jobs)+'</td><td>'+(c.dist_road_km??'—')+'</td><td>'+(c.dist_nearest_dcfc_km??'—')+'</td>';
    tr.addEventListener('click',()=>select(c,true));
    tb.appendChild(tr);
    const m=L.circleMarker([c.lat,c.lon],{radius:4+c.predicted_dcfc*0.55,color:'#a3e635',weight:1,fillColor:'#a3e635',fillOpacity:.45})
      .bindPopup('<strong>Tract '+c.tract+'</strong><br>'+c.county_name+', '+c.state_name+'<br>Predicted DCFC ports: <strong>'+c.predicted_dcfc+'</strong><br>Nearest DCFC today: '+c.dist_nearest_dcfc_km+' km');
    m.on('click',()=>select(c,false));m.addTo(map);markers[c.GEOID]=m;
    if(showPolys&&POLYS[c.GEOID]){
      const p=L.geoJSON(POLYS[c.GEOID],{style:polyStyle(c,false)})
        .bindPopup('<strong>Tract '+c.tract+'</strong> ('+c.GEOID+')<br>'+c.county_name+', '+c.state_name+'<br>Predicted DCFC ports: <strong>'+c.predicted_dcfc+'</strong>');
      p.on('click',()=>select(c,false));p.addTo(map);polys[c.GEOID]=p;
    }
  });
}
function select(c,fly){
  document.querySelectorAll('#cand-body tr').forEach(r=>r.classList.toggle('sel',r.dataset.geoid===c.GEOID));
  const row=document.querySelector('#cand-body tr[data-geoid="'+c.GEOID+'"]');
  if(row)row.scrollIntoView({block:'nearest'});
  Object.entries(polys).forEach(([g,p])=>{const cc=CANDS.find(x=>x.GEOID===g);p.setStyle(polyStyle(cc,g===c.GEOID));});
  if(fly){
    if(polys[c.GEOID]){map.flyToBounds(polys[c.GEOID].getBounds(),{duration:.8,padding:[24,24]});polys[c.GEOID].openPopup();}
    else if(markers[c.GEOID]){map.flyTo([c.lat,c.lon],10,{duration:.8});markers[c.GEOID].openPopup();}
  }
}
['f-state','f-search','f-min','f-sort','f-polys'].forEach(id=>document.getElementById(id).addEventListener('input',render));
render();

/* ---------- explorer reset (appears when filters or map view differ from start) ---------- */
const HOME={center:[37.5,-96],zoom:4};
const FILTER_DEFAULTS={'f-state':'','f-search':'','f-min':'0','f-sort':'predicted_dcfc'};
const resetBtn=document.getElementById('f-reset');
function filtersDirty(){
  for(const id in FILTER_DEFAULTS) if(document.getElementById(id).value!==FILTER_DEFAULTS[id])return true;
  return !document.getElementById('f-polys').checked;
}
function mapDirty(){
  const c=map.getCenter();
  return map.getZoom()!==HOME.zoom||Math.abs(c.lat-HOME.center[0])>1e-6||Math.abs(c.lng-HOME.center[1])>1e-6;
}
function updateReset(){resetBtn.classList.toggle('show',filtersDirty()||mapDirty());}
['f-state','f-search','f-min','f-sort','f-polys'].forEach(id=>{
  const el=document.getElementById(id);
  el.addEventListener('input',updateReset);el.addEventListener('change',updateReset);
});
map.on('moveend',updateReset);
resetBtn.addEventListener('click',()=>{
  for(const id in FILTER_DEFAULTS){
    const el=document.getElementById(id);el.value=FILTER_DEFAULTS[id];
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
  }
  const polysEl=document.getElementById('f-polys');
  if(!polysEl.checked){polysEl.checked=true;polysEl.dispatchEvent(new Event('input',{bubbles:true}));polysEl.dispatchEvent(new Event('change',{bubbles:true}));}
  map.closePopup();
  map.flyTo(HOME.center,HOME.zoom,{duration:.8});
  updateReset();
});
updateReset();
</script>
<script>
/* ---------- shadcn component kit (vanilla implementations of the
   Radix-based shadcn/ui Select, Checkbox and Slider; the hidden native
   elements remain the state + event source for the page's logic) ----- */
(function(){
  const CHEVRON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>';
  const CHECK = '<svg class="sc-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
  function enhanceSelect(sel){
    if (!sel || sel.dataset.scDone) return; sel.dataset.scDone = 1;
    sel.classList.add('sc-native'); sel.tabIndex = -1;
    const wrap = document.createElement('span'); wrap.className = 'sc-wrap';
    sel.parentNode.insertBefore(wrap, sel); wrap.appendChild(sel);
    const trigger = document.createElement('button');
    trigger.type = 'button'; trigger.className = 'sc-trigger';
    trigger.setAttribute('aria-haspopup', 'listbox');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.innerHTML = '<span class="sc-label"></span>' + CHEVRON;
    wrap.appendChild(trigger);
    const content = document.createElement('div');
    content.className = 'sc-content'; content.setAttribute('role', 'listbox');
    content.hidden = true; wrap.appendChild(content);
    const label = trigger.querySelector('.sc-label');
    let hl = -1, open = false;
    function syncLabel(){ const o = sel.options[sel.selectedIndex]; label.textContent = o ? o.textContent : ''; }
    function build(){
      content.innerHTML = '';
      Array.from(sel.options).forEach((o, i) => {
        const it = document.createElement('div');
        it.className = 'sc-item'; it.setAttribute('role', 'option');
        it.setAttribute('aria-selected', i === sel.selectedIndex ? 'true' : 'false');
        it.innerHTML = '<span></span>' + CHECK;
        it.querySelector('span').textContent = o.textContent;
        it.addEventListener('click', () => { pick(i); });
        it.addEventListener('mousemove', () => setHl(i));
        content.appendChild(it);
      });
      hl = sel.selectedIndex;
      paint();
    }
    function paint(){
      Array.from(content.children).forEach((it, i) => it.dataset.hl = i === hl ? '1' : '0');
      const it = content.children[hl];
      if (it) it.scrollIntoView({block: 'nearest'});
    }
    function setHl(i){ hl = i; paint(); }
    function show(){ build(); open = true; content.hidden = false; trigger.setAttribute('aria-expanded', 'true'); }
    function hide(){ open = false; content.hidden = true; trigger.setAttribute('aria-expanded', 'false'); }
    function pick(i){
      if (i !== sel.selectedIndex){
        sel.selectedIndex = i;
        sel.dispatchEvent(new Event('input', {bubbles: true}));
        sel.dispatchEvent(new Event('change', {bubbles: true}));
      }
      syncLabel(); hide(); trigger.focus();
    }
    trigger.addEventListener('click', () => open ? hide() : show());
    trigger.addEventListener('keydown', e => {
      if (!open && (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ')){ e.preventDefault(); show(); return; }
      if (!open) return;
      if (e.key === 'ArrowDown'){ e.preventDefault(); setHl(Math.min(hl + 1, sel.options.length - 1)); }
      else if (e.key === 'ArrowUp'){ e.preventDefault(); setHl(Math.max(hl - 1, 0)); }
      else if (e.key === 'Home'){ e.preventDefault(); setHl(0); }
      else if (e.key === 'End'){ e.preventDefault(); setHl(sel.options.length - 1); }
      else if (e.key === 'Enter' || e.key === ' '){ e.preventDefault(); pick(hl); }
      else if (e.key === 'Escape'){ e.preventDefault(); hide(); }
      else if (e.key === 'Tab'){ hide(); }
      else if (e.key.length === 1){
        const k = e.key.toLowerCase();
        const idx = Array.from(sel.options).findIndex(o => o.textContent.toLowerCase().startsWith(k));
        if (idx >= 0) setHl(idx);
      }
    });
    document.addEventListener('click', e => { if (open && !wrap.contains(e.target)) hide(); });
    sel.addEventListener('change', syncLabel);
    syncLabel();
  }
  function enhanceCheckbox(box){
    if (!box || box.dataset.scDone) return; box.dataset.scDone = 1;
    box.classList.add('sc-native');
    const btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'sc-checkbox'; btn.setAttribute('role', 'checkbox');
    btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>';
    box.parentNode.insertBefore(btn, box);
    function paint(){
      btn.dataset.state = box.checked ? 'checked' : 'unchecked';
      btn.setAttribute('aria-checked', box.checked ? 'true' : 'false');
      btn.querySelector('svg').style.opacity = box.checked ? '1' : '0';
    }
    btn.addEventListener('click', e => {
      e.preventDefault(); e.stopPropagation();
      box.checked = !box.checked;
      box.dispatchEvent(new Event('input', {bubbles: true}));
      box.dispatchEvent(new Event('change', {bubbles: true}));
      paint();
    });
    const txt = box.parentElement ? box.parentElement.querySelector('[data-check-text]') : null;
    if (txt) txt.addEventListener('click', () => btn.click());
    box.addEventListener('change', paint);
    paint();
  }
  function enhanceRange(inp){
    if (!inp || inp.dataset.scDone) return; inp.dataset.scDone = 1;
    inp.classList.add('sc-native');
    const s = document.createElement('span'); s.className = 'sc-slider';
    s.innerHTML = '<span class="sc-track"><span class="sc-range"></span></span><span class="sc-thumb" tabindex="0" role="slider" aria-label="Minimum predicted ports"></span>';
    inp.parentNode.insertBefore(s, inp);
    const range = s.querySelector('.sc-range'), thumb = s.querySelector('.sc-thumb');
    const min = parseFloat(inp.min), max = parseFloat(inp.max), step = parseFloat(inp.step) || 1;
    function paint(){
      const pct = (parseFloat(inp.value) - min) / (max - min) * 100;
      range.style.width = pct + '%'; thumb.style.left = pct + '%';
      thumb.setAttribute('aria-valuenow', inp.value);
    }
    function setFromEvent(e){
      const r = s.getBoundingClientRect();
      let v = min + (e.clientX - r.left) / r.width * (max - min);
      v = Math.round(v / step) * step;
      v = Math.max(min, Math.min(max, v));
      if (String(v) !== inp.value){ inp.value = v; inp.dispatchEvent(new Event('input', {bubbles: true})); }
      paint();
    }
    s.addEventListener('pointerdown', e => {
      s.setPointerCapture(e.pointerId); setFromEvent(e);
      const mv = ev => setFromEvent(ev);
      s.addEventListener('pointermove', mv);
      s.addEventListener('pointerup', () => s.removeEventListener('pointermove', mv), {once: true});
    });
    thumb.addEventListener('keydown', e => {
      let v = parseFloat(inp.value);
      if (e.key === 'ArrowRight' || e.key === 'ArrowUp') v += step;
      else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') v -= step;
      else if (e.key === 'Home') v = min;
      else if (e.key === 'End') v = max;
      else return;
      e.preventDefault();
      inp.value = Math.max(min, Math.min(max, v));
      inp.dispatchEvent(new Event('input', {bubbles: true}));
      paint();
    });
    inp.addEventListener('input', paint);
    paint();
  }
  enhanceSelect(document.getElementById('dt-type'));
  enhanceSelect(document.getElementById('f-state'));
  enhanceSelect(document.getElementById('f-sort'));
  enhanceCheckbox(document.getElementById('f-polys'));
  enhanceRange(document.getElementById('f-min'));
})();
</script>
</body>
</html>
"""

html = (HEAD + RESULTS + JS).replace("__DATA__", DATA).replace("__POLYS__", POLYS)
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("docs/index.html:", len(html), "bytes")

