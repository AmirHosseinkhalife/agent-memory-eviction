"""LLM-judged importance scores for real conversation turns (OpenAI-compatible API).

The API key is read from the AVALAI_API_KEY environment variable and is never stored.
Scores are cached in data/locomo/importance.json so experiments are reproducible offline.
"""

import json
import os
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE_URL = os.environ.get("AVALAI_BASE_URL", "https://api.avalai.ir/v1")
MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")

PROMPT = """You manage the long-term memory of a personal AI assistant that will later be asked \
questions about the two speakers below (facts about their lives, events, dates, plans, preferences, \
relationships). Memory is limited, so some conversation turns will be forgotten.

For EACH numbered turn of the session below, rate from 1 to 10 how important it is to keep in memory \
because it is likely to be needed to answer future questions (10 = essential personal fact or event, \
1 = small talk with no lasting information). Judge each turn only by its content.

Session date: {date}
{turns}

Respond with ONLY a JSON array of {n} integers, one per turn, in order."""


def _chat(messages, api_key, max_tokens=4000, retries=4):
    body = json.dumps({"model": MODEL, "messages": messages, "temperature": 0,
                       "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=body, headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception:  # network / rate-limit errors: back off and retry
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 3)


def rate_session(key, date, turns, api_key):
    """turns: list of (dia_id, speaker, text). Returns {dia_id: score}."""
    lines = "\n".join(f"{k + 1}. {spk}: {txt}" for k, (_, spk, txt) in enumerate(turns))
    prompt = PROMPT.format(date=date, turns=lines, n=len(turns))
    for _ in range(5):
        out = _chat([{"role": "user", "content": prompt}], api_key)
        m = re.search(r"\[[\d,\s]+\]", out or "")
        if m:
            scores = json.loads(m.group(0))
            if len(scores) == len(turns):
                return key, {t[0]: int(min(10, max(1, s))) for t, s in zip(turns, scores)}
    if len(turns) > 1:  # long sessions occasionally get a miscounted array: rate halves separately
        half = len(turns) // 2
        _, a = rate_session(key, date, turns[:half], api_key)
        _, b = rate_session(key, date, turns[half:], api_key)
        return key, {**a, **b}
    raise RuntimeError(f"could not parse scores for {key}")


def rate_all(sessions, cache_path, workers=8):
    """sessions: {key: (date, turns)}. Fills and returns the cache {key: {dia_id: score}}."""
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    todo = {k: v for k, v in sessions.items() if k not in cache}
    if todo:
        api_key = os.environ["AVALAI_API_KEY"]
        with ThreadPoolExecutor(workers) as ex:
            futs = [ex.submit(rate_session, k, d, t, api_key) for k, (d, t) in todo.items()]
            for n, f in enumerate(futs, 1):
                k, scores = f.result()
                cache[k] = scores
                if n % 20 == 0 or n == len(futs):
                    cache_path.write_text(json.dumps(cache))
                    print(f"  rated {n}/{len(futs)} sessions", flush=True)
    return cache
