"""Clairvoyant offline optimum for AMEP via integer linear programming.

Because eviction is irrevocable, every feasible schedule holds item i over a
contiguous interval starting at its arrival. Let r_{i,1} < ... < r_{i,K_i} be
the request times of item i, and let y_{i,k} = 1 iff i is still held at its
k-th request. Then

    max   sum_{i,k} v_i * y_{i,k}
    s.t.  y_{i,k} <= y_{i,k-1}                              (irrevocability)
          sum_i s_i * y_{i, next_i(t)} <= B   for every arrival time t   (capacity)
          y in {0,1}

where next_i(t) is the index of i's first request after t. Memory load can only
grow at arrival events, so capacity constraints at arrivals suffice. Holding an
item with no future request is never useful, so such items do not appear.
"""

import numpy as np
from scipy.optimize import LinearConstraint, milp
from scipy.sparse import coo_matrix


def build_ilp(trace, capacity):
    req = trace.requests_of()
    var = {}                                  # (i, k) -> column, k = 0-based request index
    values = []
    for it in trace.items:
        for k in range(len(req[it.id])):
            var[(it.id, k)] = len(values)
            values.append(it.value)
    n = len(values)

    rows, cols, data, lo, hi = [], [], [], [], []
    r = 0
    for it in trace.items:                    # y_{i,k} - y_{i,k-1} <= 0
        for k in range(1, len(req[it.id])):
            rows += [r, r]; cols += [var[(it.id, k)], var[(it.id, k - 1)]]; data += [1.0, -1.0]
            lo.append(-np.inf); hi.append(0.0); r += 1

    arrivals = [(t, i) for t, (kind, i) in enumerate(trace.events) if kind == "arr"]
    ptr = {it.id: 0 for it in trace.items}    # index of next request after current time
    live = []                                 # items arrived so far with requests remaining
    for t, i in arrivals:
        if req[i]:
            live.append(i)
        still = []
        terms = []
        for j in live:
            rj = req[j]
            while ptr[j] < len(rj) and rj[ptr[j]] <= t:
                ptr[j] += 1
            if ptr[j] < len(rj):
                still.append(j)
                terms.append((var[(j, ptr[j])], trace.items[j].size))
        live = still
        if sum(s for _, s in terms) > capacity:   # skip constraints that can never bind
            for c, s in terms:
                rows.append(r); cols.append(c); data.append(s)
            lo.append(-np.inf); hi.append(capacity); r += 1

    A = coo_matrix((data, (rows, cols)), shape=(r, n)).tocsr()
    return np.asarray(values), A, np.asarray(lo), np.asarray(hi)


def solve_opt(trace, capacity, relax=False, time_limit=120.0) -> dict:
    """Return the offline optimum (or its LP upper bound if relax=True)."""
    c, A, lo, hi = build_ilp(trace, capacity)
    if len(c) == 0:
        return dict(utility=0.0, status="empty", gap=0.0)
    cons = [LinearConstraint(A, lo, hi)] if A.shape[0] else []
    res = milp(
        -c, constraints=cons, bounds=(0, 1),
        integrality=np.zeros_like(c) if relax else np.ones_like(c),
        options={"time_limit": time_limit, "mip_rel_gap": 1e-4},
    )
    if res.x is None:
        raise RuntimeError(f"ILP failed: {res.message}")
    gap = getattr(res, "mip_gap", 0.0) or 0.0
    return dict(utility=float(-res.fun), status=res.message, gap=float(gap),
                n_vars=len(c), n_cons=A.shape[0])
