"""Figures and tables for the extended experiments:  python -m memsim.figures_extra"""

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from .experiments import DEFAULT_CAP, RESULTS
from .figures import (FIG, INK, MUTED, SERIES, WL_LABEL, _legend_below, _lines, _logx,
                      ci95, matplotlib, plt, save)
from .policies import POLICY_NAMES

OUT = []


def md(title, body):
    OUT.append(f"\n### {title}\n\n{body}")


def paired(df, a, b, keys):
    x = df[df.policy == a].set_index(keys)["ratio"]
    y = df[df.policy == b].set_index(keys)["ratio"]
    x, y = x.align(y, join="inner")
    d = x - y
    p = wilcoxon(x, y).pvalue if (d != 0).any() else 1.0
    return dict(A=a, B=b, n=len(d), mean_diff_pt=round(100 * d.mean(), 2),
                win_rate=f"{(d > 0).mean():.0%}", p_value=f"{p:.1e}")


def stats_tables():
    main = pd.read_csv(RESULTS / "main.csv")
    keys = ["workload", "seed", "cap_frac"]
    pairs = [("VRS+C", "GDS"), ("VRS+C", "VRS"), ("VRS", "GDS"), ("VRS", "GenAgents"),
             ("VRS", "ImpDecay"), ("GDS", "LRU"), ("GenAgents", "LRU"), ("LRU", "Random"),
             ("Ebbinghaus", "Random")]
    rows = [dict(scope="all budgets, all workloads", **paired(main, a, b, keys)) for a, b in pairs]
    d10 = main[main.cap_frac == DEFAULT_CAP]
    rows += [dict(scope="B = 10%", **paired(d10, a, b, keys)) for a, b in pairs[:4]]
    for w in WL_LABEL:
        rows.append(dict(scope=f"{WL_LABEL[w]}, all budgets",
                         **paired(main[main.workload == w], "VRS", "GDS", keys)))
    md("Paired Wilcoxon signed-rank tests (synthetic)", pd.DataFrame(rows).to_markdown(index=False))


def oracle_info():
    d = pd.read_csv(RESULTS / "oracle_info.csv")
    d10 = d[d.cap_frac == DEFAULT_CAP]
    g = d10.groupby(["workload", "policy"])["ratio"].mean().unstack()
    t = pd.DataFrame({
        "Workload": [WL_LABEL[w] for w in g.index],
        "DENSITY* (% OPT)": (100 * g["DENSITY*"]).round(1),
        "VRS (% OPT)": (100 * g["VRS"]).round(1),
        "GDS (% OPT)": (100 * g["GDS"]).round(1),
        "Information gap (OPT − DENSITY*)": (100 * (1 - g["DENSITY*"])).round(1),
        "Estimation gap (DENSITY* − VRS)": (100 * (g["DENSITY*"] - g["VRS"])).round(1),
        "VRS (% of DENSITY*)": (100 * g["VRS"] / g["DENSITY*"]).round(1),
    })
    md("Gap decomposition at B = 10% (points of OPT)", t.to_markdown(index=False))
    cap = d.groupby(["cap_frac", "policy"])["ratio"].mean().unstack().round(3)
    md("DENSITY* / VRS / GDS across budgets (avg over workloads, fraction of OPT)", cap.to_markdown())


def clairvoyance():
    d = pd.read_csv(RESULTS / "clairvoyance.csv")
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    styles = {(100, 1): ("#2a78d6", "o"), (1000, 1): ("#eb6834", "s"),
              (100, 10): ("#1baf7a", "^"), (1000, 10): ("#eda100", "D")}
    for (n, B), (col, mk) in styles.items():
        g = d[(d.n == n) & (d.B == B)]
        ax.plot(g.req_per_item, g.ratio, color=col, marker=mk, label=f"n={n}, B={B}")
        ax.plot(g.req_per_item, g.bound, color=col, ls=":", lw=1.2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.minorticks_off()
    ax.set_xticks([0.25, 1, 4, 16, 64, 256], ["0.25", "1", "4", "16", "64", "256"])
    ax.set_yticks([1, 1.5, 2, 3, 5, 10], ["1", "1.5", "2", "3", "5", "10"])
    ax.set_ylim(0.95, 12)
    ax.set_xlabel("Requests per item (H / n)")
    ax.set_ylabel("E[OPT] / E[best online]")
    ax.set_title("Price of clairvoyance (solid: simulated; dotted: Thm 5a bound, one per n)",
                 loc="left", fontsize=8.5, color=INK)
    _legend_below(fig, ax)
    save(fig, "fig5_clairvoyance")
    piv = d.pivot_table(index="req_per_item", columns=["n", "B"], values="ratio").round(3)
    md("Price of clairvoyance, simulated E[OPT]/E[DENSITY]", piv.to_markdown())


def sensitivity():
    c = pd.read_csv(RESULTS / "sens_compress.csv")
    g = c.groupby(["rho", "gamma", "policy"])["ratio"].mean().unstack().round(3)
    md("Compression sensitivity (avg over workloads at B = 10%, fraction of evict-only OPT)",
       g.to_markdown())
    d = pd.read_csv(RESULTS / "sens_dist.csv")
    ov = [c for c in d.columns if c.startswith("ov_")]
    d["variant"] = d[ov].apply(lambda r: next(f"{k[3:]}={v}" for k, v in r.items()
                                              if pd.notna(v)), axis=1)
    pols = ["LRU", "Ebbinghaus", "GenAgents", "GDS", "VRS", "VRS+C"]
    g = d[d.policy.isin(pols)].groupby(["workload", "variant", "policy"])["ratio"].mean()
    t = g.unstack()[pols].round(3)
    t["best"] = t.idxmax(axis=1)
    md("Workload-distribution sensitivity (fraction of OPT, B = 10%)", t.to_markdown())


def locomo():
    d = pd.read_csv(RESULTS / "locomo.csv")
    pols = POLICY_NAMES + ["VRS+C", "GenAgents+C", "LRU+C", "VRS-noRate", "VRS-noValue",
                           "VRS-noSize", "VRS (no LLM)", "GDS (no LLM)", "GenAgents (no LLM)"]
    for proto in ["interleaved", "end"]:
        x = d[d.protocol == proto]
        g = x.groupby(["policy", "cap_frac"])["ratio"].agg(["mean", "std"])
        cols = sorted(x.cap_frac.unique())
        lines = ["| Policy | " + " | ".join(f"B = {int(100 * c)}%" for c in cols)
                 + " | Evidence recall @10% |", "|---" * (len(cols) + 2) + "|"]
        best = {c: g.xs(c, level="cap_frac")["mean"].max() for c in cols}
        for p in pols:
            if p not in g.index.get_level_values(0):
                continue
            cells = []
            for c in cols:
                m, s = g.loc[(p, c)]
                txt = f"{100 * m:.1f} ± {100 * s:.1f}"
                cells.append(f"**{txt}**" if abs(m - best[c]) < 1e-12 else txt)
            rec = x[(x.policy == p) & (x.cap_frac == 0.1)]["hit_rate"].mean()
            lines.append(f"| {p} | " + " | ".join(cells) + f" | {100 * rec:.1f}% |")
        md(f"LoCoMo ({proto} protocol): % of OPT (mean ± std)", "\n".join(lines))

    keys = ["conv", "seed", "cap_frac"]
    x = d[d.protocol == "interleaved"]
    pairs = [("VRS", "GDS"), ("VRS+C", "GDS"), ("VRS+C", "VRS"), ("VRS", "GenAgents"),
             ("VRS", "LRU"), ("GDS", "LRU"), ("VRS", "VRS (no LLM)"), ("GDS", "GDS (no LLM)"),
             ("GenAgents", "GenAgents (no LLM)")]
    rows = [dict(scope="interleaved, all budgets", **paired(x, a, b, keys)) for a, b in pairs]
    e = d[d.protocol == "end"]
    rows += [dict(scope="end, all budgets", **paired(e, a, b, keys)) for a, b in pairs[:6]]
    md("LoCoMo paired Wilcoxon tests", pd.DataFrame(rows).to_markdown(index=False))

    info = d.drop_duplicates(["conv", "protocol", "seed", "cap_frac"])
    md("LoCoMo instance statistics",
       f"- conversations: {d.conv.nunique()}; items per conversation: "
       f"{info.n_items.min()}–{info.n_items.max()} (total {d.drop_duplicates('conv').n_items.sum()}); "
       f"questions used: {d.drop_duplicates('conv').n_questions.sum()}\n"
       f"- oracle instances: {len(info)}; max MIP gap {info.opt_gap.max():.1e}")

    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6), sharey=True)
    series = {**SERIES, "VRS+C": ("#6250d6", "P")}
    for ax, proto, title in zip(axes, ["interleaved", "end"],
                                ["(a) Interleaved questions", "(b) Questions at the end"]):
        _lines(ax, d[d.protocol == proto], "cap_frac", "ratio", series)
        _logx(ax, [0.05, 0.1, 0.2, 0.4], ["5%", "10%", "20%", "40%"])
        ax.set_title(title, loc="left", fontsize=9, color=INK)
        ax.set_xlabel("Budget B (% of conversation tokens)", fontsize=8)
    axes[0].set_ylabel("% of OPT")
    axes[0].set_ylim(0, 1.02)
    axes[0].yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    _legend_below(fig, axes[0])
    save(fig, "fig6_locomo")

    imp = d[(d.protocol == "interleaved") & (d.policy == "VRS") & (d.cap_frac == 0.1)]
    return imp


if __name__ == "__main__":
    import sys
    stats_tables()
    oracle_info()
    clairvoyance()
    sensitivity()
    if (RESULTS / "locomo.csv").exists() and "--no-locomo" not in sys.argv:
        locomo()
    (RESULTS / "tables_extra.md").write_text("\n".join(OUT), encoding="utf-8")
    print("ok")
