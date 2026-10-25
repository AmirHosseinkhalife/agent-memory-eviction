"""Synthetic workload generators for AMEP.

A trace is a sequence of T events. Each event is either the arrival of a new
memory item or a request (retrieval need) for a previously arrived item.
The requested item is drawn with probability proportional to its current
popularity weight w_i(t); workloads differ only in how w_i(t) is defined.
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Item:
    id: int
    arrival: int
    size: float          # tokens
    value: float         # true utility per successful retrieval
    value_hat: float     # noisy estimate available to policies (e.g. LLM-judged importance)
    critical: bool = False
    kind: str = "regular"
    lam: float = 1.0                 # ground-truth popularity parameters (hidden from online
    tau: float = float("inf")        # policies; used only by the privileged DENSITY* reference)
    topic: int = 0


@dataclass
class Trace:
    name: str
    items: list
    events: list                     # list of ("arr", i) | ("req", i)
    params: dict = field(default_factory=dict)

    @property
    def total_size(self) -> float:
        return float(sum(it.size for it in self.items))

    def requests_of(self) -> dict:
        """Map item id -> sorted list of request times."""
        out = {it.id: [] for it in self.items}
        for t, (kind, i) in enumerate(self.events):
            if kind == "req":
                out[i].append(t)
        return out


WORKLOADS = ["irm", "temporal", "rare_critical", "drift", "mixed"]

DEFAULTS = dict(
    T=3000,
    p_arrival=0.3,
    size_median=50.0, size_sigma=0.6, size_min=8.0, size_max=400.0,
    value_sigma=1.0,
    rate_shape=1.5,               # Pareto shape for popularity (heavy tail)
    value_noise=0.5,              # log-normal sigma of value_hat / value
    tau=150.0,                    # recency time-scale for temporal workloads (steps)
    critical_frac=0.05, critical_value_mult=30.0, critical_rate_mult=0.15,
    n_topics=10, n_phases=5,
)


def _sample_attrs(rng, p):
    size = float(np.clip(rng.lognormal(np.log(p["size_median"]), p["size_sigma"]),
                         p["size_min"], p["size_max"]))
    value = float(rng.lognormal(0.0, p["value_sigma"]))
    rate = float(rng.pareto(p["rate_shape"]) + 1.0)
    return size, value, rate


def generate(name: str, seed: int, **overrides) -> Trace:
    """Generate a trace for workload `name` with the given seed."""
    if name not in WORKLOADS:
        raise ValueError(f"unknown workload {name!r}")
    p = {**DEFAULTS, **overrides}
    rng = np.random.default_rng(seed)
    T = p["T"]

    items, events = [], []
    lam, arr, tau = [], [], []           # per-item base rate, arrival time, decay scale (inf = none)
    topic = []
    phase_len = max(1, T // p["n_phases"])
    topic_pop = rng.dirichlet(np.full(p["n_topics"], 0.5), size=p["n_phases"] + 1)

    for t in range(T):
        if not items or rng.random() < p["p_arrival"]:
            i = len(items)
            size, value, rate = _sample_attrs(rng, p)
            kind, critical, it_tau = "regular", False, np.inf

            if name == "temporal":
                it_tau = p["tau"]
            elif name == "rare_critical":
                if rng.random() < p["critical_frac"]:
                    critical, kind = True, "critical"
                    value *= p["critical_value_mult"]
                    rate *= p["critical_rate_mult"]
            elif name == "mixed":
                u = rng.random()
                if u < p["critical_frac"]:
                    critical, kind = True, "critical"
                    value *= p["critical_value_mult"]
                    rate *= p["critical_rate_mult"]
                elif u < p["critical_frac"] + 0.25:
                    kind = "persistent"
                else:
                    kind, it_tau = "ephemeral", p["tau"] * 0.5
                    rate *= 3.0

            value_hat = float(value * np.exp(rng.normal(0.0, p["value_noise"])))
            items.append(Item(i, t, size, value, value_hat, critical, kind,
                              lam=rate, tau=it_tau, topic=int(rng.integers(p["n_topics"]))))
            lam.append(rate); arr.append(t); tau.append(it_tau)
            topic.append(items[-1].topic)
            events.append(("arr", i))
        else:
            lam_a, arr_a, tau_a = np.asarray(lam), np.asarray(arr), np.asarray(tau)
            w = lam_a * np.exp(-(t - arr_a) / tau_a)
            if name == "drift":
                w = w * topic_pop[t // phase_len][np.asarray(topic)]
            w = w / w.sum()
            events.append(("req", int(rng.choice(len(w), p=w))))

    return Trace(name, items, events, params={**p, "seed": seed, "topic_pop": topic_pop,
                                              "phase_len": phase_len})


def true_weight(trace, item, t):
    """Ground-truth popularity w_i(t) of an item (for the privileged DENSITY* reference)."""
    w = item.lam * np.exp(-(t - item.arrival) / item.tau)
    if trace.name == "drift":
        w *= trace.params["topic_pop"][t // trace.params["phase_len"]][item.topic]
    return float(w)
