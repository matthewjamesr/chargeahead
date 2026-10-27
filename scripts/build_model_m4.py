#!/usr/bin/env python3
"""M3_draft8 — LODES 2019->2023 trend features + EV-corridor proximity on
draft7's winning spec (BASE44 + tract AADT, state encoding in-fold,
LightGBM hurdle, Tweedie-1.5).
  D8-A: + trends (wac_growth, rac_growth — shrunk log ratios)
  D8-B: + corridors (log dist to nearest EV-designated corridor, 1mi/5mi flags)
  D8-C: + both
Adjudicated against draft7 D single-seed (0.3602 / 0.9976).
Winner -> 3-seed ensemble -> full fit -> candidates."""
import json
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_absolute_error
import lightgbm as lgb

R = {}
def save(): json.dump(R, open("m3_draft8_results.json", "w"), indent=1)
def score(p): return {"r2": round(r2_score(y, p), 4), "mae": round(mean_absolute_error(y, p), 4)}

feat = pd.read_csv("tract_features_m3d2.csv", dtype={"GEOID": str})
aadt = pd.read_csv("data/hpms_aadt_by_county.csv", dtype={"county_fips": str})
county = feat.GEOID.str[:5]
feat["log_max_aadt"] = np.log1p(county.map(aadt.set_index("county_fips").max_aadt_art))
feat["log_wavg_aadt"] = np.log1p(county.map(aadt.set_index("county_fips").wavg_aadt_art))
state = feat.GEOID.str[:2]
ev_h = feat.ev_regs2.where(state != "51")
feat["ev_regs_h"] = ev_h; feat["log_ev_h"] = np.log1p(ev_h)
feat["ev_per_1000_h"] = 1000 * ev_h / feat.population.replace(0, np.nan)
feat["ev_data_h"] = ev_h.notna().astype(int)
feat["ev_bev_only"] = (state == "36").astype(int)
poi = pd.read_csv("data/poi_by_tract_draft4.csv", dtype={"GEOID": str})
feat = feat.merge(poi, on="GEOID", how="left")
POI = [c for c in poi.columns if c != "GEOID"]
buf = pd.read_csv("data/poi_buffer_by_tract.csv", dtype={"GEOID": str})
feat = feat.merge(buf, on="GEOID", how="left")
BUF = [c for c in buf.columns if c != "GEOID"]
ta = pd.read_csv("data/aadt_by_tract.csv", dtype={"GEOID": str})
feat = feat.merge(ta, on="GEOID", how="left")
tr = pd.read_csv("data/lodes_trends_by_tract.csv", dtype={"GEOID": str})
feat = feat.merge(tr, on="GEOID", how="left")
co = pd.read_csv("data/corridor_by_tract.csv", dtype={"GEOID": str})
feat = feat.merge(co, on="GEOID", how="left")

EXT = ["log_pop","log_density","median_income","log_jobs","establishments",
       "log_ev","ev_per_1000","ev_data","dist_road_km","dcfc_5km",
       "dcfc_10km","dist_nearest_dcfc_km","centroid_lat","centroid_lon",
       "dist_interchange_km","l2_5km","dist_nearest_l2_km",
       "dcfc_recent_10km","years_since_first_dcfc_10km"]
REGH = ["log_ev_h","ev_per_1000_h","ev_data_h","ev_bev_only"]
LOD = ["log_lodes_work","lodes_workers_home","lodes_net_jobs"]
AADT = ["log_max_aadt","log_wavg_aadt"]
FULL = [c for c in EXT if c != "log_jobs"] + REGH + LOD + AADT + POI
DROP = ["dist_interchange_km","dist_nearest_l2_km","log_wavg_aadt",
        "dcfc_recent_10km","log_ev","ev_per_1000"]
PRUNED = [c for c in FULL if c not in DROP]
BASE44 = PRUNED + BUF                       # draft6 D6-A feature set
TRACT = ["log_tract_max_aadt", "log_tract_wavg_aadt", "has_tract_aadt"]
ENC = ["st_mean_ports", "st_prev", "st_ports_per_1k"]
TREND = ["wac_growth", "rac_growth"]
CORR = ["log_dist_corridor_km", "corr_1mi", "corr_5mi"]
WINBASE = BASE44 + TRACT                    # draft7 D7-A columns
D8A = WINBASE + TREND
D8B = WINBASE + CORR
D8C = WINBASE + TREND + CORR

y = feat.dcfc_ports.values
FOLDS = list(GroupKFold(5).split(feat, y, county.values))
BASE = {"learning_rate": 0.05, "n_estimators": 600, "num_leaves": 63,
        "min_child_samples": 40, "subsample": 0.9, "colsample_bytree": 0.9,
        "reg_lambda": 1.0}
STATE = state.values
POP = feat.population.values

def state_enc(tr_idx, apply_idx):
    df = pd.DataFrame({"st": STATE[tr_idx], "y": y[tr_idx], "pop": POP[tr_idx]})
    g = df.groupby("st")
    stats = pd.DataFrame({"st_mean_ports": g.y.mean(),
                          "st_prev": g.y.apply(lambda s: (s > 0).mean()),
                          "st_ports_per_1k": 1000 * g.y.sum() / g["pop"].sum()})
    gm = {"st_mean_ports": df.y.mean(), "st_prev": (df.y > 0).mean(),
          "st_ports_per_1k": 1000 * df.y.sum() / df["pop"].sum()}
    out = {}
    for c in ENC:
        m = stats[c]
        out[c] = pd.Series(STATE[apply_idx]).map(m).fillna(gm[c]).values
    return out

def oof(cols, seed, use_enc=False):
    pred = np.zeros(len(feat))
    for tr, te in FOLDS:
        Xtr = feat[cols].iloc[tr].copy(); Xte = feat[cols].iloc[te].copy()
        if use_enc:
            etr = state_enc(tr, tr); ete = state_enc(tr, te)
            for c in ENC: Xtr[c] = etr[c]; Xte[c] = ete[c]
        ytr = y[tr]; pos = ytr > 0
        clf = lgb.LGBMClassifier(objective="binary", verbose=-1, seed=seed, **BASE).fit(Xtr, pos.astype(int))
        rp = dict(BASE, verbose=-1, seed=seed, objective="tweedie", tweedie_variance_power=1.5)
        reg = lgb.LGBMRegressor(**rp).fit(Xtr[pos], ytr[pos])
        pred[te] = clf.predict_proba(Xte)[:, 1] * np.clip(reg.predict(Xte), 0, None)
    return pred

BASE_SCORE = {"r2": 0.3629, "mae": 0.9915}   # D8-B single seed 42
ENS_SCORE = {"r2": 0.3652, "mae": 0.9915}      # D8-B 3-seed ensemble OOF

WIN = WINBASE + CORR
assert len(WIN) == 50, len(WIN)

# ---- full-data fit, 3 seeds (identical recipe to draft8's final fit) ----
X = feat[WIN].copy()
full = state_enc(np.arange(len(feat)), np.arange(len(feat)))
for c in ENC: X[c] = full[c]
pos = y > 0
models, preds = [], []
for s in (42, 7, 2026):
    clf = lgb.LGBMClassifier(objective="binary", verbose=-1, seed=s, **BASE).fit(X, pos.astype(int))
    rp = dict(BASE, verbose=-1, seed=s, objective="tweedie", tweedie_variance_power=1.5)
    reg = lgb.LGBMRegressor(**rp).fit(X[pos], y[pos])
    models.append((clf, reg))
    preds.append(clf.predict_proba(X)[:, 1] * np.clip(reg.predict(X), 0, None))
feat["predicted_dcfc_m4"] = np.mean(preds, axis=0)

# ---- consistency: released candidates must equal draft8's ----
cand = feat[feat.dcfc_ports == 0].nlargest(500, "predicted_dcfc_m4")[
    ["GEOID","STATEFP","COUNTYFP","NAME","population","median_income",
     "ev_regs2","jobs","dist_road_km","dist_nearest_dcfc_km","predicted_dcfc_m4"]]
d8 = pd.read_csv("candidate_tracts_dcfc_m3d8_top500.csv", dtype={"GEOID": str})
same = list(cand.GEOID) == list(d8.GEOID)
maxdiff = float(np.abs(cand.predicted_dcfc_m4.values -
                       d8.predicted_dcfc_m3d8.values).max())
print("candidates identical order:", same, "| max pred diff:", maxdiff)
assert same and maxdiff < 1e-6

# ---- artifact: models + state-encoding table + feature list ----
import joblib
st_stats = {}
for c in ENC:
    st_stats[c] = {str(st): float(v) for st, v in zip(STATE, full[c][
        pd.Series(STATE).drop_duplicates().index])}
# rebuild per-state stats cleanly from the full-data frame
tmp = pd.DataFrame({"st": STATE, "y": y, "pop": POP})
g = tmp.groupby("st")
enc_table = pd.DataFrame({"st_mean_ports": g.y.mean(),
                          "st_prev": g.y.apply(lambda s: (s > 0).mean()),
                          "st_ports_per_1k": 1000 * g.y.sum() / g["pop"].sum()})
enc_globals = {"st_mean_ports": float(tmp.y.mean()),
               "st_prev": float((tmp.y > 0).mean()),
               "st_ports_per_1k": float(1000 * tmp.y.sum() / tmp["pop"].sum())}
artifact = {
    "model_id": "M4",
    "models": models,                      # [(clf, reg) x 3 seeds]
    "features": WIN + ENC,
    "enc_table": {str(k): {c: float(enc_table.loc[k, c]) for c in ENC}
                  for k in enc_table.index},
    "enc_globals": enc_globals,
    "predict": "apply state encoding from enc_table by 2-digit state FIPS "
               "(fallback enc_globals), then mean over seeds of "
               "P(any) * clip(sizing, 0, None)",
}
joblib.dump(artifact, "/home/hatch/workspace/chargeahead/models/m4_hurdle.joblib",
            compress=3)
print("artifact dumped")

cand_out = cand.rename(columns={"predicted_dcfc_m4": "predicted_dcfc"})
cand_out.to_csv("/home/hatch/workspace/chargeahead/results/candidate_tracts_dcfc_m4_top500.csv",
                index=False)
feat.to_csv("tract_features_m4_scored.csv", index=False)

results = {"model": "M4", "released": "2026-10-27",
           "spec": "LightGBM hurdle (binary x Tweedie-1.5), 3-seed ensemble, "
                   "53 features + in-fold state target encoding",
           "spatial_cv_ensemble": ENS_SCORE,
           "spatial_cv_single_seed": BASE_SCORE,
           "vs_M3": {"r2": 0.3353, "mae": 1.1690},
           "features": WIN + ENC}
json.dump(results, open("/home/hatch/workspace/chargeahead/results/m4_results.json", "w"), indent=1)

# ---- gain importances (mean across seeds and stages, normalized) ----
imp = np.zeros(len(WIN) + len(ENC))
for clf, reg in models:
    imp += clf.booster_.feature_importance(importance_type="gain")
    imp += reg.booster_.feature_importance(importance_type="gain")
imp = imp / imp.sum()
imp_map = {f: round(float(v), 4) for f, v in zip(WIN + ENC, imp)}
json.dump(imp_map, open("/home/hatch/workspace/chargeahead/data/m4_importances.json", "w"), indent=1)
print("top importances:", sorted(imp_map.items(), key=lambda kv: -kv[1])[:8])
print("RELEASE BUILD DONE")
