# What Should an Agent Forget?
### A Competitive Analysis of Memory Eviction for LLM Agents

**Amir Hossein Khalifeh, Mehdi Gholami** · Contact: Amirkhalife.biz@gmail.com

This repository contains the paper and **MemSim**, the simulator and exact offline oracle behind it.

- 📄 Paper (English): [`paper.en.md`](paper.en.md)
- 📄 مقاله (فارسی): [`paper.fa.md`](paper.fa.md)
- 🧪 Code: [`code/memsim/`](code/memsim/)

## TL;DR

LLM agents keep long-term memories in bounded stores and must decide what to forget. Unlike a cache, **a forgotten memory cannot be re-fetched**. We formalize this as the *Agent Memory Eviction Problem* (AMEP) and show:

- **Belady's rule fails** under irrevocable eviction, and **no online policy is worst-case competitive**.
- **Value-oblivious policies** (LRU, LFU, FIFO, Ebbinghaus forgetting curves) can be forced to a $B/n$ fraction of achievable utility, even on benign stochastic workloads.
- Under an independent re-access model, a **value–rate–size index** is $(1 - s_{\max}/B)$-competitive; with LLM-predicted values it is consistent and smooth, but no policy can be robust.
- The **price of clairvoyance** (best online vs. hindsight optimum) is $\Theta(\log n / \log\log n)$ when requests are sparse and vanishes as they become dense.

## Key results

| | Synthetic (250 instances) | LoCoMo real conversations (440 instances) |
|---|---|---|
| Value-oblivious (LRU, LFU, FIFO, Ebbinghaus) | 39–61% of OPT | 30–31% of OPT (random: 25%) |
| Best existing value-aware heuristic | 77.7% (GDS) | 45.9% (GDS, interleaved) |
| VRS (ours) | 78.0% | 43.9% interleaved / **47.0% end** |
| VRS+C (ours, with compression) | **82.4%** | 54.0% / 64.5% |
| GenAgents+C (baseline + our compression wrapper) | 76.5% | **60.8% / 70.5%** |
| Critical-fact recall, LRU vs. VRS+C | 18–32% vs. **99%+** | — |
| Effect of LLM-predicted importance | — | **+12 to +25 points** (AUC 0.83) |

*Budget B = 10%; % of the exact clairvoyant optimum. Full results, statistical tests and sensitivity analyses are in the paper.*

![Policies vs. the offline optimum](code/figures/fig1_teaser.png)

## Reproduce

```bash
cd code
pip install -r requirements.txt
sh data/get_locomo.sh                       # LoCoMo benchmark (real-data experiment)
python tests/test_oracle.py                 # oracle == brute force; no policy beats OPT
python -m memsim.experiments all            # all experiments -> results/*.csv
python -m memsim.figures                    # figures/*.pdf, results/tables.md
python -m memsim.figures_extra              # extended figures, results/tables_extra.md
```

LLM importance scores for LoCoMo are cached in `code/data/locomo/importance.json`, so no API key is needed to reproduce the results. To re-score with your own model, set `AVALAI_API_KEY` (and optionally `AVALAI_BASE_URL`, `LLM_MODEL` for any OpenAI-compatible endpoint) and delete the cache.

## Repository layout

```
paper.en.md, paper.fa.md     the paper (English / Persian, identical structure)
code/memsim/
  workloads.py               synthetic workloads: IRM, temporal, rare-critical, drift, mixed
  locomo.py                  real-data traces from LoCoMo
  llm.py                     LLM-judged importance scores (OpenAI-compatible API)
  policies.py                8 baselines, VRS (ours), ablations, DENSITY*, compression wrapper
  simulator.py               event-driven engine with irrevocable eviction
  oracle.py                  exact ILP offline optimum (HiGHS) and LP bound
  experiments.py             tuning and all experiment grids
  figures.py, figures_extra.py
code/tests/test_oracle.py    correctness checks
code/results/                raw CSVs, tuned hyper-parameters, tables
code/figures/                all figures (PDF + PNG)
```

## Citation

```bibtex
@misc{agentmemoryeviction2026,
  title  = {What Should an Agent Forget? A Competitive Analysis of Memory Eviction for LLM Agents},
  author = {Khalifeh, Amir Hossein and Gholami, Mehdi},
  year   = {2026},
  url    = {https://github.com/AmirHosseinkhalife/agent-memory-eviction}
}
```

## License

Code: MIT. The LoCoMo dataset is not redistributed here; it is © its authors (CC BY-NC 4.0) and is downloaded by `data/get_locomo.sh`.
