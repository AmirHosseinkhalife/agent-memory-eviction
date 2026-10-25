"""Event-driven simulator for AMEP with irrevocable eviction."""

import time

import numpy as np


def simulate(trace, policy, capacity: float, seed: int = 0) -> dict:
    """Run `policy` on `trace` with memory budget `capacity` (tokens).

    Eviction is irrevocable: an evicted item can never be re-admitted, so every
    later request for it is a miss. Returns utility, hit and retention metrics.
    """
    rng = np.random.default_rng(seed)
    policy.reset(trace, rng)
    items = trace.items
    size = {}            # current (possibly compressed) size of held items
    vfrac = {}           # fraction of value retained (1.0 unless compressed)
    used = 0.0
    utility = hits = requests = 0
    crit_hits = crit_requests = 0
    n_compress = 0
    on_request = getattr(policy, "on_request", None)

    t0 = time.perf_counter()
    for t, (kind, i) in enumerate(trace.events):
        if kind == "arr":
            size[i] = items[i].size
            vfrac[i] = 1.0
            used += size[i]
            policy.on_insert(i, t)
            while used > capacity + 1e-9:
                action, j = policy.decide(size, t)
                if action == "compress":
                    new = size[j] * policy.rho
                    used -= size[j] - new
                    size[j] = new
                    vfrac[j] *= policy.gamma
                    n_compress += 1
                else:
                    used -= size.pop(j)
                    vfrac.pop(j)
                    policy.on_evict(j, t)
        else:
            requests += 1
            if on_request:
                on_request(t)
            crit = items[i].critical
            crit_requests += crit
            if i in size:
                hits += 1
                crit_hits += crit
                utility += items[i].value * vfrac[i]
                policy.on_access(i, t)
    elapsed = time.perf_counter() - t0

    return dict(
        policy=policy.name,
        utility=float(utility),
        hits=hits,
        requests=requests,
        hit_rate=hits / max(1, requests),
        critical_recall=(crit_hits / crit_requests) if crit_requests else np.nan,
        n_compress=n_compress,
        us_per_event=1e6 * elapsed / len(trace.events),
    )
