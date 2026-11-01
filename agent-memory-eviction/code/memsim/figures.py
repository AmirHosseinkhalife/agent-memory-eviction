"""Figures and tables for the paper:  python -m memsim.figures"""

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .experiments import DEFAULT_CAP, RESULTS  # noqa: E402
from .policies import POLICY_NAMES  # noqa: E402

FIG = RESULTS.parent / "figures"
FIG.mkdir(exist_ok=True)

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BASELINE_GRAY = "#a8a7a2"
# Fixed categorical order (validated reference palette); colour follows the policy.
SERIES = {
    "VRS": ("#2a78d6", "o"),
    "GDS": ("#eb6834", "s"),
    "GenAgents": ("#1baf7a", "^"),
    "LRU": ("#eda100", "D"),
    "Ebbinghaus": ("#e87ba4", "v"),
}
WL_LABEL = {"irm": "IRM (stationary)", "temporal": "Temporal locality",
            "rare_critical": "Rare-critical", "drift": "Drift", "mixed": "Mixed assistant"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
    "lines.linewidth": 2, "lines.markersize": 5, "savefig.bbox": "tight",
})


def ci95(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    return 1.96 * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else 0.0


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=200)
    plt.close(fig)


def fig1_teaser(main):
    d = main[main.cap_frac == DEFAULT_CAP]
    pols = POLICY_NAMES + ["VRS+C"]
    # average over workloads per seed, then CI over seeds
    per_seed = d[d.policy.isin(pols)].groupby(["policy", "seed"])["ratio"].mean().reset_index()
    agg = per_seed.groupby("policy")["ratio"].agg(["mean", ci95]).sort_values("mean")
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    colors = ["#2a78d6" if p.startswith("VRS") else BASELINE_GRAY for p in agg.index]
    ax.barh(agg.index, 100 * agg["mean"], xerr=100 * agg["ci95"], color=colors,
            height=0.62, error_kw=dict(ecolor=MUTED, lw=1, capsize=2))
    for y, (m, c) in enumerate(zip(agg["mean"], agg["ci95"])):
        ax.text(100 * (m + c) + 1, y, f"{100 * m:.1f}%", va="center", color=INK, fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Utility as % of clairvoyant optimum (higher is better)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Memory policies vs. the offline optimum (B = 10% of stream)",
                 loc="left", fontsize=9, color=INK)
    save(fig, "fig1_teaser")
    return agg


def _logx(ax, ticks, labels):
    ax.set_xscale("log")
    ax.minorticks_off()
    ax.set_xticks(ticks, labels)


def _legend_below(fig, ax):
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=len(l), bbox_to_anchor=(0.5, -0.17), fontsize=8)


def _lines(ax, d, x, y, pols=SERIES):
    for p, (col, mk) in pols.items():
        g = d[d.policy == p].groupby(x)[y].agg(["mean", ci95])
        ax.plot(g.index, g["mean"], color=col, marker=mk, label=p)
        ax.fill_between(g.index, g["mean"] - g["ci95"], g["mean"] + g["ci95"],
                        color=col, alpha=0.12, lw=0)


def fig2_critical(main):
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6), sharey=True)
    for ax, w in zip(axes, ["rare_critical", "mixed"]):
        _lines(ax, main[main.workload == w], "cap_frac", "critical_recall")
        _logx(ax, [0.025, 0.05, 0.1, 0.2, 0.4], ["2.5%", "5%", "10%", "20%", "40%"])
        ax.set_title(WL_LABEL[w], loc="left", fontsize=9, color=INK)
        ax.set_xlabel("Memory budget B (% of total stream size)")
    axes[0].set_ylabel("Critical-fact recall")
    axes[0].set_ylim(0, 1.02)
    _legend_below(fig, axes[0])
    save(fig, "fig2_critical")


def fig3_capacity(main):
    fig, axes = plt.subplots(1, 5, figsize=(11, 2.5), sharey=True)
    for ax, w in zip(axes, WL_LABEL):
        _lines(ax, main[main.workload == w], "cap_frac", "ratio")
        _logx(ax, [0.025, 0.1, 0.4], ["2.5%", "10%", "40%"])
        ax.set_title(WL_LABEL[w], loc="left", fontsize=9, color=INK)
        ax.set_xlabel("Budget B")
    axes[0].set_ylabel("% of OPT")
    axes[0].set_ylim(0, 1.02)
    axes[0].yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    _legend_below(fig, axes[0])
    save(fig, "fig3_capacity")


def fig4_robust(noise, drift):
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6), sharey=True)
    _lines(axes[0], noise[noise.workload == "mixed"], "ov_value_noise", "ratio")
    axes[0].set_xlabel("Value-estimate noise σ (log-normal)")
    axes[0].set_title("(a) Noisy importance estimates — Mixed", loc="left", fontsize=9, color=INK)
    _lines(axes[1], drift, "ov_n_phases", "ratio")
    _logx(axes[1], [1, 2, 5, 10, 20, 50], ["1", "2", "5", "10", "20", "50"])
    axes[1].set_xlabel("Number of popularity regimes (drift speed)")
    axes[1].set_title("(b) Popularity drift", loc="left", fontsize=9, color=INK)
    axes[0].set_ylabel("% of OPT")
    axes[0].yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    _legend_below(fig, axes[0])
    save(fig, "fig4_robust")


def fmt(m, s):
    return f"{100 * m:.1f} ± {100 * s:.1f}"


def tables(main, noise, drift):
    out = []
    d = main[main.cap_frac == DEFAULT_CAP]
    wl = list(WL_LABEL)

    def block(title, pols, metric="ratio"):
        g = d[d.policy.isin(pols)].groupby(["policy", "workload"])[metric].agg(["mean", "std"])
        per_seed = d[d.policy.isin(pols)].groupby(["policy", "seed"])[metric].mean()
        avg = per_seed.groupby("policy").agg(["mean", "std"])
        out.append(f"\n### {title}\n")
        out.append("| Policy | " + " | ".join(WL_LABEL[w] for w in wl) + " | Average |")
        out.append("|---" * (len(wl) + 2) + "|")
        best = {w: g.xs(w, level="workload")["mean"].max() for w in wl}
        for p in pols:
            cells = []
            for w in wl:
                m, s = g.loc[(p, w)]
                c = fmt(m, s)
                cells.append(f"**{c}**" if abs(m - best[w]) < 1e-12 else c)
            cells.append(fmt(*avg.loc[p]))
            out.append(f"| {p} | " + " | ".join(cells) + " |")

    block("Table 1 — % of OPT at B = 10% (mean ± std over 10 seeds)", POLICY_NAMES)
    block("Table 2 — Compression (% of evict-only OPT)",
          ["LRU", "LRU+C", "GenAgents", "GenAgents+C", "VRS", "VRS+C"])
    block("Table 3 — VRS ablations", ["VRS", "VRS-noRate", "VRS-noValue", "VRS-noSize"])

    out.append("\n### Critical-fact recall at B = 10%\n")
    cr = d[d.workload.isin(["rare_critical", "mixed"])]
    g = cr.groupby(["policy", "workload"])["critical_recall"].mean().unstack()
    out.append(g.loc[POLICY_NAMES + ["VRS+C"]].round(3).to_markdown())

    out.append("\n### Runtime (µs per event, mean over all runs)\n")
    out.append(main.groupby("policy")["us_per_event"].mean().round(1).to_markdown())

    out.append("\n### Oracle statistics\n")
    o = main.drop_duplicates("key")
    out.append(f"- instances: {len(o)}; max relative MIP gap: {o.opt_gap.max():.2e}; "
               f"mean gap: {o.opt_gap.mean():.2e}")

    out.append("\n### Value-noise sweep (% of OPT, mean)\n")
    out.append(noise.groupby(["workload", "ov_value_noise", "policy"])["ratio"].mean()
               .unstack().round(3).to_markdown())
    out.append("\n### Drift sweep (% of OPT, mean)\n")
    out.append(drift.groupby(["ov_n_phases", "policy"])["ratio"].mean().unstack().round(3).to_markdown())

    out.append("\n### Capacity sweep — average over workloads (% of OPT)\n")
    out.append(main[main.policy.isin(POLICY_NAMES + ["VRS+C"])]
               .groupby(["cap_frac", "policy"])["ratio"].mean().unstack().round(3).to_markdown())
    (RESULTS / "tables.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main = pd.read_csv(RESULTS / "main.csv")
    noise = pd.read_csv(RESULTS / "noise.csv")
    drift = pd.read_csv(RESULTS / "drift.csv")
    print(fig1_teaser(main))
    fig2_critical(main)
    fig3_capacity(main)
    fig4_robust(noise, drift)
    tables(main, noise, drift)
    print("figures ->", FIG)
