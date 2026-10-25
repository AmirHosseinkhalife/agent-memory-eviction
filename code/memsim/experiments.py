"""Experiment pipeline for the paper.

    python -m memsim.experiments tune      # hyper-parameter selection on validation seeds
    python -m memsim.experiments main      # RQ1-RQ3, ablations, compression (test seeds)
    python -m memsim.experiments noise     # RQ4a: value-estimate noise
    python -m memsim.experiments drift     # RQ4b: popularity drift
    python -m memsim.experiments oracle_info   # DENSITY* decomposition (information vs. estimation gap)
    python -m memsim.experiments sensitivity   # compression (rho, gamma) and workload distributions
    python -m memsim.experiments clairvoyance  # price of clairvoyance (Theorem 5), Monte Carlo
    python -m memsim.experiments locomo        # real-data experiment on LoCoMo
    python -m memsim.experiments all

Validation seeds (1000-1004) are disjoint from test seeds (0-9).
"""

import hashlib
import itertools
import json
import math
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

from .oracle import solve_opt
from .policies import ABLATION_NAMES, COMPRESSION_NAMES, POLICY_NAMES, make_policy
from .simulator import simulate
from .workloads import WORKLOADS, generate

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)
OPT_CACHE = RESULTS / "opt_cache.json"
HP_FILE = RESULTS / "hyperparameters.json"

TEST_SEEDS = list(range(10))
VAL_SEEDS = list(range(1000, 1005))
CAPS = [0.025, 0.05, 0.1, 0.2, 0.4]
DEFAULT_CAP = 0.1
N_PROC = int(os.environ.get("MEMSIM_PROCS", 24))
OPT_TIME_LIMIT = 90.0

ALL_POLICIES = POLICY_NAMES + ABLATION_NAMES + COMPRESSION_NAMES


# ---------------------------------------------------------------- oracle cache

def _trace_key(tr, cap_frac):
    h = hashlib.sha1()
    h.update(repr(tr.events).encode())
    h.update(repr([(it.size, it.value) for it in tr.items]).encode())
    h.update(repr(cap_frac).encode())
    return h.hexdigest()


def _opt_job(args):
    workload, seed, overrides, cap_frac = args
    tr = generate(workload, seed, **overrides)
    t0 = time.perf_counter()
    res = solve_opt(tr, cap_frac * tr.total_size, time_limit=OPT_TIME_LIMIT)
    res["seconds"] = time.perf_counter() - t0
    return _trace_key(tr, cap_frac), res


def ensure_opt(jobs):
    """Solve (and cache) the offline optimum for every (workload, seed, overrides, cap)."""
    cache = json.loads(OPT_CACHE.read_text()) if OPT_CACHE.exists() else {}
    todo, seen = [], set()
    for job in jobs:
        tr = generate(job[0], job[1], **job[2])
        k = _trace_key(tr, job[3])
        if k not in cache and k not in seen:
            todo.append(job)
            seen.add(k)
    if todo:
        print(f"solving {len(todo)} ILPs ...", flush=True)
        with Pool(N_PROC) as pool:
            for n, (k, res) in enumerate(pool.imap_unordered(_opt_job, todo), 1):
                cache[k] = res
                if n % 10 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)}", flush=True)
                    OPT_CACHE.write_text(json.dumps(cache))
    return cache


# ---------------------------------------------------------------- policy runs

def _sim_job(args):
    workload, seed, overrides, cap_frac, policies, hp, tag = args
    tr = generate(workload, seed, **overrides)
    cap = cap_frac * tr.total_size
    rows = []
    for name in policies:
        r = simulate(tr, make_policy(name, hp), cap, seed=seed)
        r.update(workload=workload, seed=seed, cap_frac=cap_frac, tag=tag,
                 key=_trace_key(tr, cap_frac), **{f"ov_{k}": v for k, v in overrides.items()})
        rows.append(r)
    return rows


def run_grid(configs, policies, hp, tag):
    """configs: list of (workload, seed, overrides, cap_frac)."""
    cache = ensure_opt(configs)
    jobs = [(w, s, ov, c, policies, hp, tag) for (w, s, ov, c) in configs]
    with Pool(N_PROC) as pool:
        rows = [r for chunk in pool.imap_unordered(_sim_job, jobs) for r in chunk]
    df = pd.DataFrame(rows)
    df["opt"] = df["key"].map(lambda k: cache[k]["utility"])
    df["opt_gap"] = df["key"].map(lambda k: cache[k]["gap"])
    df["ratio"] = df["utility"] / df["opt"]
    return df


def load_hp():
    return json.loads(HP_FILE.read_text()) if HP_FILE.exists() else {}


# ---------------------------------------------------------------- experiments

TUNE_GRID = {
    "Ebbinghaus": {"S0": [25, 50, 100, 200, 400, 800, 1600]},
    "GenAgents": {"decay": [0.95, 0.98, 0.99, 0.995, 0.998, 0.999, 0.9995]},
    "ImpDecay": {"S0": [25, 50, 100, 200, 400, 800, 1600]},
    "VRS": {"b0": [50, 200, 800], "half_life": [100, 300, 1000, 3000, math.inf]},
}


def tune():
    configs = [(w, s, {}, DEFAULT_CAP) for w in WORKLOADS for s in VAL_SEEDS]
    ensure_opt(configs)
    best = {}
    records = []
    for pol, grid in TUNE_GRID.items():
        keys = list(grid)
        scores = []
        for vals in itertools.product(*grid.values()):
            hp = {pol: dict(zip(keys, vals))}
            df = run_grid(configs, [pol], hp, "tune")
            score = df.groupby("workload")["ratio"].mean().mean()
            scores.append((score, hp[pol]))
            records.append(dict(policy=pol, **hp[pol], val_ratio=score))
            print(f"  {pol} {hp[pol]} -> {score:.4f}", flush=True)
        best[pol] = max(scores, key=lambda x: x[0])[1]
    HP_FILE.write_text(json.dumps(best, indent=2, default=str))
    pd.DataFrame(records).to_csv(RESULTS / "tuning.csv", index=False)
    print("selected:", best)


def _hp_for_runtime():
    hp = load_hp()
    for v in hp.values():
        for k, x in v.items():
            if x == "inf" or x == math.inf:
                v[k] = math.inf
    return hp


def main():
    hp = _hp_for_runtime()
    configs = [(w, s, {}, c) for w in WORKLOADS for s in TEST_SEEDS for c in CAPS]
    df = run_grid(configs, ALL_POLICIES, hp, "main")
    df.to_csv(RESULTS / "main.csv", index=False)
    print(df[df.cap_frac == DEFAULT_CAP].groupby(["workload", "policy"])["ratio"].mean().unstack(0).round(3))


def noise():
    hp = _hp_for_runtime()
    configs = [(w, s, {"value_noise": sig}, DEFAULT_CAP)
               for w in ["mixed", "rare_critical", "irm"] for s in TEST_SEEDS
               for sig in [0.0, 0.25, 0.5, 1.0, 1.5, 2.0]]
    df = run_grid(configs, POLICY_NAMES + ["VRS+C"], hp, "noise")
    df.to_csv(RESULTS / "noise.csv", index=False)


def drift():
    hp = _hp_for_runtime()
    configs = [(w, s, {"n_phases": k}, DEFAULT_CAP)
               for w in ["drift"] for s in TEST_SEEDS for k in [1, 2, 5, 10, 20, 50]]
    df = run_grid(configs, POLICY_NAMES + ["VRS+C"], hp, "drift")
    df.to_csv(RESULTS / "drift.csv", index=False)


def oracle_info():
    hp = _hp_for_runtime()
    configs = [(w, s, {}, c) for w in WORKLOADS for s in TEST_SEEDS for c in CAPS]
    df = run_grid(configs, ["DENSITY*", "VRS", "GDS"], hp, "oracle_info")
    df.to_csv(RESULTS / "oracle_info.csv", index=False)


def sensitivity():
    hp = _hp_for_runtime()
    base = [(w, s, {}, DEFAULT_CAP) for w in WORKLOADS for s in TEST_SEEDS]
    frames = []
    for rho in [0.1, 0.25, 0.5]:
        for gamma in [0.3, 0.6, 0.9]:
            if gamma <= rho:
                continue
            h = {**hp, "compress": {"rho": rho, "gamma": gamma}}
            df = run_grid(base, ["VRS+C", "GDS+C", "GenAgents+C"], h, "compress")
            df["rho"], df["gamma"] = rho, gamma
            frames.append(df)
    pd.concat(frames).to_csv(RESULTS / "sens_compress.csv", index=False)

    variants = {"value_sigma": [0.5, 1.0, 2.0], "rate_shape": [1.1, 1.5, 3.0],
                "size_sigma": [0.3, 0.6, 1.0], "critical_value_mult": [10.0, 30.0, 100.0]}
    configs = [(w, s, {k: v}, DEFAULT_CAP) for k, vals in variants.items() for v in vals
               for w in ["irm", "mixed"] for s in TEST_SEEDS]
    df = run_grid(configs, POLICY_NAMES + ["VRS+C"], hp, "dist")
    df.to_csv(RESULTS / "sens_dist.csv", index=False)


def clairvoyance(reps=4000):
    """Static arrivals, unit sizes/values, uniform IRM: E[OPT]/E[DENSITY] vs requests per item."""
    import numpy as np
    rng = np.random.default_rng(0)
    rows = []
    for n in [100, 1000]:
        for B in [1, 10]:
            for hn in [0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256]:
                H = int(round(hn * n))
                counts = rng.multinomial(H, np.full(n, 1.0 / n), size=reps)
                opt = np.sort(counts, axis=1)[:, -B:].sum(axis=1).mean()
                dens = B * H / n
                L = np.log(n + 1)
                bound = 1 + (B / dens) * (np.sqrt(2 * H / n * L) + L / 3)
                rows.append(dict(n=n, B=B, req_per_item=hn, H=H, ratio=opt / dens, bound=bound))
    pd.DataFrame(rows).to_csv(RESULTS / "clairvoyance.csv", index=False)


# ---------------------------------------------------------------- real data (LoCoMo)

LOCOMO_CAPS = [0.05, 0.1, 0.2, 0.4]
LOCOMO_POLICIES = POLICY_NAMES + ABLATION_NAMES + COMPRESSION_NAMES


def _locomo_trace(conv_idx, protocol, seed, value_hat):
    from . import locomo
    data = locomo.load()
    scores = json.loads((locomo.DATA / "importance.json").read_text())
    return locomo.build_trace(data[conv_idx], scores, protocol, seed, value_hat)


def _locomo_opt_job(args):
    conv_idx, protocol, seed, cap_frac = args
    tr = _locomo_trace(conv_idx, protocol, seed, "llm")
    res = solve_opt(tr, cap_frac * tr.total_size, time_limit=OPT_TIME_LIMIT)
    return _trace_key(tr, cap_frac), res


def _locomo_sim_job(args):
    conv_idx, protocol, seed, cap_frac, hp = args
    rows = []
    for vh in ["llm", "none"]:
        tr = _locomo_trace(conv_idx, protocol, seed, vh)
        cap = cap_frac * tr.total_size
        names = LOCOMO_POLICIES if vh == "llm" else ["VRS", "GDS", "GenAgents"]
        for name in names:
            r = simulate(tr, make_policy(name, hp), cap, seed=seed)
            if vh == "none":
                r["policy"] += " (no LLM)"
            r.update(conv=conv_idx, protocol=protocol, seed=seed, cap_frac=cap_frac,
                     key=_trace_key(tr, cap_frac), n_items=len(tr.items),
                     n_questions=tr.params["n_questions"])
            rows.append(r)
    return rows


def locomo():
    hp = _hp_for_runtime()
    configs = [(c, p, s, cap) for c in range(10) for p in ["interleaved", "end"]
               for s in (TEST_SEEDS if p == "interleaved" else [0]) for cap in LOCOMO_CAPS]
    cache = json.loads(OPT_CACHE.read_text()) if OPT_CACHE.exists() else {}
    todo = [cfg for cfg in configs
            if _trace_key(_locomo_trace(cfg[0], cfg[1], cfg[2], "llm"), cfg[3]) not in cache]
    if todo:
        print(f"solving {len(todo)} LoCoMo ILPs ...", flush=True)
        with Pool(N_PROC) as pool:
            for n, (k, res) in enumerate(pool.imap_unordered(_locomo_opt_job, todo), 1):
                cache[k] = res
                if n % 20 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)}", flush=True)
                    OPT_CACHE.write_text(json.dumps(cache))
    with Pool(N_PROC) as pool:
        rows = [r for chunk in pool.imap_unordered(
            _locomo_sim_job, [(*cfg, hp) for cfg in configs]) for r in chunk]
    df = pd.DataFrame(rows)
    df["opt"] = df["key"].map(lambda k: cache[k]["utility"])
    df["opt_gap"] = df["key"].map(lambda k: cache[k]["gap"])
    df["ratio"] = df["utility"] / df["opt"]
    df.to_csv(RESULTS / "locomo.csv", index=False)
    print(df[df.cap_frac == 0.1].groupby(["protocol", "policy"])["ratio"].mean().unstack(0).round(3))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    steps = {"tune": [tune], "main": [main], "noise": [noise], "drift": [drift],
             "oracle_info": [oracle_info], "sensitivity": [sensitivity],
             "clairvoyance": [clairvoyance], "locomo": [locomo],
             "all": [tune, main, noise, drift, oracle_info, sensitivity, clairvoyance, locomo]}[cmd]
    for f in steps:
        t0 = time.time()
        print(f"== {f.__name__}", flush=True)
        f()
        print(f"== {f.__name__} done in {time.time() - t0:.0f}s", flush=True)
