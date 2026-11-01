"""Correctness checks: ILP oracle == brute force on tiny instances, and no online
policy ever beats the oracle."""

import itertools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memsim import Item, Trace, make_policy, simulate, solve_opt  # noqa: E402
from memsim.policies import ABLATION_NAMES, COMPRESSION_NAMES, POLICY_NAMES  # noqa: E402
from memsim.workloads import WORKLOADS, generate  # noqa: E402


def random_tiny_trace(rng, n_events=14):
    items, events = [], []
    for t in range(n_events):
        if not items or rng.random() < 0.4:
            i = len(items)
            v = float(rng.integers(1, 6))
            items.append(Item(i, t, float(rng.integers(1, 4)), v, v))
            events.append(("arr", i))
        else:
            events.append(("req", int(rng.integers(len(items)))))
    return Trace("tiny", items, events)


def brute_force(trace, capacity):
    req = trace.requests_of()
    ids = [it.id for it in trace.items]
    best = 0.0
    for ks in itertools.product(*[range(len(req[i]) + 1) for i in ids]):
        # item i is held from arrival until (and including) its ks[i]-th request
        until = {i: (req[i][k - 1] if k else -1) for i, k in zip(ids, ks)}
        ok = True
        for t, (kind, j) in enumerate(trace.events):
            if kind != "arr":
                continue
            load = sum(trace.items[i].size for i in ids
                       if trace.items[i].arrival <= t < until[i])
            if load > capacity + 1e-9:
                ok = False
                break
        if ok:
            best = max(best, sum(trace.items[i].value * k for i, k in zip(ids, ks)))
    return best


def test_oracle_matches_brute_force():
    rng = np.random.default_rng(0)
    for _ in range(60):
        tr = random_tiny_trace(rng)
        cap = float(rng.integers(2, 6))
        assert abs(solve_opt(tr, cap)["utility"] - brute_force(tr, cap)) < 1e-6


def test_no_policy_beats_oracle():
    names = POLICY_NAMES + ABLATION_NAMES + ["LRU+C", "VRS+C"]
    for w in WORKLOADS:
        tr = generate(w, seed=7, T=400)
        cap = 0.1 * tr.total_size
        opt = solve_opt(tr, cap)["utility"]
        lp = solve_opt(tr, cap, relax=True)["utility"]
        assert lp >= opt - 1e-6
        for name in names:
            if name.endswith("+C"):
                continue  # compression changes the feasible set; not bounded by this oracle
            u = simulate(tr, make_policy(name), cap)["utility"]
            assert u <= opt + 1e-6, (w, name, u, opt)


if __name__ == "__main__":
    test_oracle_matches_brute_force()
    test_no_policy_beats_oracle()
    print("all tests passed")
