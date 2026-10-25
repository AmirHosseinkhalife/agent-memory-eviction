"""Eviction policies for AMEP.

Every policy sees only online information: item sizes, the noisy value
estimate value_hat, arrival times, and the access history of items it still
holds. When memory exceeds capacity, the simulator repeatedly asks the policy
for a victim; the policy may return ("evict", i) or, if it supports
compression, ("compress", i).
"""

import math

import numpy as np


class Policy:
    name = "base"
    value_aware = False

    def __init__(self, **hp):
        self.hp = hp

    def reset(self, trace, rng):
        self.items = trace.items
        self.rng = rng
        self.last = {}
        self.count = {}
        self.compressed = set()

    def on_insert(self, i, t):
        self.last[i] = t
        self.count[i] = 0

    def on_access(self, i, t):
        self.last[i] = t
        self.count[i] += 1

    def on_evict(self, i, t):
        pass

    def score(self, i, t):
        """Lower score = evicted first."""
        raise NotImplementedError

    def decide(self, mem, t):
        victim = min(mem, key=lambda i: self.score(i, t))
        return "evict", victim


class Random(Policy):
    name = "Random"

    def decide(self, mem, t):
        keys = list(mem)
        return "evict", keys[self.rng.integers(len(keys))]


class FIFO(Policy):
    name = "FIFO"

    def score(self, i, t):
        return self.items[i].arrival


class LRU(Policy):
    name = "LRU"

    def score(self, i, t):
        return self.last[i]


class LFU(Policy):
    name = "LFU"

    def score(self, i, t):
        return (self.count[i], self.last[i])


class GreedyDualSize(Policy):
    """GreedyDual-Size (Cao & Irani, 1997) with cost = value_hat."""
    name = "GDS"
    value_aware = True

    def reset(self, trace, rng):
        super().reset(trace, rng)
        self.L = 0.0
        self.H = {}

    def _h(self, i):
        it = self.items[i]
        return self.L + it.value_hat / it.size

    def on_insert(self, i, t):
        super().on_insert(i, t)
        self.H[i] = self._h(i)

    def on_access(self, i, t):
        super().on_access(i, t)
        self.H[i] = self._h(i)

    def score(self, i, t):
        return self.H[i]

    def on_evict(self, i, t):
        self.L = self.H.pop(i)


class Ebbinghaus(Policy):
    """MemoryBank-style forgetting curve: R = exp(-dt / S), S grows with recalls."""
    name = "Ebbinghaus"

    def score(self, i, t):
        strength = self.hp.get("S0", 100.0) * (1 + self.count[i])
        return math.exp(-(t - self.last[i]) / strength)


class GenerativeAgents(Policy):
    """Generative-Agents-style retention score: recency + importance (equal weights).

    Relevance is query-dependent and therefore undefined at eviction time; it is omitted.
    """
    name = "GenAgents"
    value_aware = True

    def score(self, i, t):
        decay = self.hp.get("decay", 0.995)
        recency = decay ** (t - self.last[i])
        importance = min(1.0, max(0.0, (math.log(self.items[i].value_hat) + 3.0) / 6.0))
        return recency + importance


class ImportanceDecay(Policy):
    """FadeMem-inspired: importance-weighted forgetting curve."""
    name = "ImpDecay"
    value_aware = True

    def score(self, i, t):
        strength = self.hp.get("S0", 100.0) * (1 + self.count[i])
        return self.items[i].value_hat * math.exp(-(t - self.last[i]) / strength)


class VRS(Policy):
    """Value-Rate-Size index policy (ours): evict argmin  lambda_hat * value_hat / size.

    lambda_hat is an empirical-Bayes estimate of the item's request rate:
        lambda_hat = (c_i + m * b0) / (E_i + b0)
    where c_i is the (optionally discounted) access count, E_i the matching
    exposure time, m the population mean rate observed so far, and b0 the
    prior strength in steps. Ablations drop one of the three factors.
    """
    name = "VRS"
    value_aware = True

    def __init__(self, use_rate=True, use_value=True, use_size=True, name=None, **hp):
        super().__init__(**hp)
        self.use_rate, self.use_value, self.use_size = use_rate, use_value, use_size
        if name:
            self.name = name
        self.value_aware = use_value

    def reset(self, trace, rng):
        super().reset(trace, rng)
        self.c = {}
        self.t_upd = {}
        self.n_arrived = 0
        self.sum_arrival = 0.0
        self.n_requests = 0

    def on_insert(self, i, t):
        super().on_insert(i, t)
        self.c[i] = 0.0
        self.t_upd[i] = t
        self.n_arrived += 1
        self.sum_arrival += t

    def on_access(self, i, t):
        super().on_access(i, t)
        h = self.hp.get("half_life", math.inf)
        self.c[i] = self.c[i] * self._disc(t - self.t_upd[i], h) + 1.0
        self.t_upd[i] = t

    def on_request(self, t):
        self.n_requests += 1

    @staticmethod
    def _disc(dt, h):
        return 1.0 if math.isinf(h) else 0.5 ** (dt / h)

    def rate(self, i, t):
        h = self.hp.get("half_life", math.inf)
        b0 = self.hp.get("b0", 200.0)
        exposure_total = self.n_arrived * t - self.sum_arrival
        m = (self.n_requests + 1.0) / (exposure_total + 1.0)
        age = t - self.items[i].arrival
        if math.isinf(h):
            c, e = self.c[i], age
        else:
            k = math.log(2) / h
            c = self.c[i] * self._disc(t - self.t_upd[i], h)
            e = (1.0 - math.exp(-k * age)) / k
        return (c + m * b0) / (e + b0)

    def score(self, i, t):
        it = self.items[i]
        s = 1.0
        if self.use_rate:
            s *= self.rate(i, t)
        if self.use_value:
            s *= it.value_hat
        if self.use_size:
            s /= it.size
        return s


class DensityStar(Policy):
    """Privileged reference (not deployable): the index policy of Theorem 4 with the
    ground-truth popularity w_i(t) and true value v_i. Its gap to OPT measures the price
    of not knowing future requests; the gap between VRS and DENSITY* measures the price
    of estimating rates and values online."""
    name = "DENSITY*"
    value_aware = True

    def reset(self, trace, rng):
        super().reset(trace, rng)
        from .workloads import true_weight
        self.trace, self.true_weight = trace, true_weight

    def score(self, i, t):
        it = self.items[i]
        return self.true_weight(self.trace, it, t) * it.value / it.size


class Compressing(Policy):
    """Wraps a policy: the first time an item is chosen as victim it is compressed
    (size *= rho, value *= gamma) instead of evicted; a second selection evicts it."""

    def __init__(self, base: Policy, rho=0.25, gamma=0.6):
        super().__init__()
        self.base, self.rho, self.gamma = base, rho, gamma
        self.name = base.name + "+C"
        self.value_aware = base.value_aware

    def reset(self, trace, rng):
        self.base.reset(trace, rng)
        self.compressed = set()

    def on_insert(self, i, t):
        self.base.on_insert(i, t)

    def on_access(self, i, t):
        self.base.on_access(i, t)

    def on_evict(self, i, t):
        self.base.on_evict(i, t)

    def on_request(self, t):
        if hasattr(self.base, "on_request"):
            self.base.on_request(t)

    def score(self, i, t):
        s = self.base.score(i, t)
        # A compressed item keeps a fraction gamma of its value in a fraction rho of its size.
        if i in self.compressed and isinstance(s, float):
            s *= self.gamma / self.rho
        return s

    def decide(self, mem, t):
        if isinstance(self.base, Random):
            _, victim = self.base.decide(mem, t)
        else:
            victim = min(mem, key=lambda i: self.score(i, t))
        if victim in self.compressed:
            return "evict", victim
        self.compressed.add(victim)
        return "compress", victim


# Default hyper-parameters; tuned on validation seeds by experiments.tune().
DEFAULT_HP = {
    "Ebbinghaus": {"S0": 100.0},
    "GenAgents": {"decay": 0.995},
    "ImpDecay": {"S0": 100.0},
    "VRS": {"b0": 200.0, "half_life": math.inf},
}

POLICY_NAMES = [
    "Random", "FIFO", "LRU", "LFU", "GDS", "Ebbinghaus", "GenAgents", "ImpDecay",
    "VRS",
]
ABLATION_NAMES = ["VRS-noRate", "VRS-noValue", "VRS-noSize"]
COMPRESSION_NAMES = ["LRU+C", "GenAgents+C", "VRS+C"]


def make_policy(name: str, hp: dict | None = None) -> Policy:
    hp = hp or {}
    if name.endswith("+C"):
        return Compressing(make_policy(name[:-2], hp), **hp.get("compress", {}))
    if name == "DENSITY*":
        return DensityStar()
    vrs_hp = {**DEFAULT_HP["VRS"], **hp.get("VRS", {})}
    simple = {
        "Random": Random, "FIFO": FIFO, "LRU": LRU, "LFU": LFU, "GDS": GreedyDualSize,
        "Ebbinghaus": Ebbinghaus, "GenAgents": GenerativeAgents, "ImpDecay": ImportanceDecay,
    }
    if name in simple:
        return simple[name](**{**DEFAULT_HP.get(name, {}), **hp.get(name, {})})
    if name == "VRS":
        return VRS(**vrs_hp)
    if name == "VRS-noRate":
        return VRS(use_rate=False, name=name, **vrs_hp)
    if name == "VRS-noValue":
        return VRS(use_value=False, name=name, **vrs_hp)
    if name == "VRS-noSize":
        return VRS(use_size=False, name=name, **vrs_hp)
    raise ValueError(f"unknown policy {name!r}")
