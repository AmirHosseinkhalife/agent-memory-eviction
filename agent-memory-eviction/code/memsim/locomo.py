"""Real-data traces from LoCoMo (Maharana et al., 2024).

Memory items are the real dialogue turns (size = estimated tokens). Requests are
the benchmark's QA questions: a question requests each of its annotated evidence
turns. Each item has true value 1, so utility = number of evidence retrievals
served. value_hat is an LLM-judged importance score computed online, from the
turn's own session only, without access to the questions.

Question timing (LoCoMo poses all questions after the last session):
  - "end":         all questions after the final session (the benchmark protocol);
  - "interleaved": each question is asked at a uniformly random session boundary
                   after its latest evidence session, so retrieval needs arise
                   while the conversation continues.
Adversarial questions (category 5) are excluded, as is standard.
"""

import json
import math
import re
from pathlib import Path

import numpy as np

from .workloads import Item, Trace

DATA = Path(__file__).resolve().parents[1] / "data" / "locomo"


def load():
    return json.loads((DATA / "locomo10.json").read_text(encoding="utf-8"))


def _sessions(conv):
    nums = sorted(int(m.group(1)) for k in conv if (m := re.fullmatch(r"session_(\d+)", k)))
    return [(n, conv.get(f"session_{n}_date_time", ""), conv[f"session_{n}"]) for n in nums]


def _turn_text(t):
    text = t.get("text", "")
    if t.get("blip_caption"):
        text += f" [shares an image: {t['blip_caption']}]"
    return text


def all_sessions(data):
    """{f"{sample_id}/{n}": (date, [(dia_id, speaker, text), ...])} for LLM rating."""
    out = {}
    for conv in data:
        for n, date, turns in _sessions(conv["conversation"]):
            out[f"{conv['sample_id']}/{n}"] = (
                date, [(t["dia_id"], t["speaker"], _turn_text(t)) for t in turns])
    return out


def score_to_value(score):
    """Map a 1-10 importance score to a log-scale value estimate in [e^-3, e^3]."""
    return math.exp((score - 5.5) / 1.5)


def build_trace(conv, scores, protocol="interleaved", seed=0, value_hat="llm"):
    rng = np.random.default_rng(seed)
    sid = conv["sample_id"]
    sessions = _sessions(conv["conversation"])
    items, idx, session_of = [], {}, {}
    arrivals = []                                   # per session: list of item ids
    for n, _, turns in sessions:
        ids = []
        for t in turns:
            i = len(items)
            size = max(4.0, len(_turn_text(t)) / 4.0)
            s = scores.get(f"{sid}/{n}", {}).get(t["dia_id"], 5)
            vh = score_to_value(s) if value_hat == "llm" else 1.0
            items.append(Item(i, -1, size, 1.0, vh, False, "turn"))
            idx[t["dia_id"]] = i
            session_of[i] = n
            ids.append(i)
        arrivals.append((n, ids))

    last_session = sessions[-1][0]
    asks = {n: [] for n, _ in arrivals}             # session after which questions are asked
    n_q = 0
    for qa in conv["qa"]:
        if qa.get("category") == 5:
            continue
        ev = []
        for e in qa.get("evidence", []):
            for part in re.split(r"[;,\s]+", e):
                if part in idx:
                    ev.append(idx[part])
        ev = sorted(set(ev))
        if not ev:
            continue
        latest = max(session_of[i] for i in ev)
        if protocol == "end":
            at = last_session
        else:
            later = [n for n, _ in arrivals if n >= latest]
            at = later[rng.integers(len(later))]
        asks[at].append(ev)
        n_q += 1

    events = []
    for n, ids in arrivals:
        for i in ids:
            items[i].arrival = len(events)
            events.append(("arr", i))
        qs = asks[n]
        rng.shuffle(qs)
        for ev in qs:
            for i in ev:
                events.append(("req", i))
    return Trace(f"locomo-{protocol}", items, events,
                 params={"sample_id": sid, "protocol": protocol, "seed": seed,
                         "value_hat": value_hat, "n_questions": n_q})
