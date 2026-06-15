from __future__ import annotations
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

_SCORE_COLORS = {
    "PASS": "#2ecc71",
    "FAIL": "#e74c3c",
    "WARN": "#f39c12",
    "ERROR": "#95a5a6",
}


def generate_dashboard(
    run_data: dict,
    output_path: str | Path = "dashboard.png",
) -> Path:
    output_path = Path(output_path)
    cases = run_data["cases"]
    scores = [c["score"] for c in cases]
    score_counts = {s: scores.count(s) for s in ["PASS", "FAIL", "WARN", "ERROR"]}

    fig, axes = plt.subplots(1, 2, figsize=(14, max(5, len(cases) * 0.4 + 2)))
    fig.suptitle(
        f"Red-Team Eval — {run_data['suite_name']}\n"
        f"Model: {run_data['model']}  |  Run: {run_data['run_id'][:8]}  |  "
        f"{run_data['timestamp'][:10]}",
        fontsize=11,
    )

    # Left: score distribution pie
    ax = axes[0]
    present = {k: v for k, v in score_counts.items() if v > 0}
    ax.pie(
        list(present.values()),
        labels=list(present.keys()),
        colors=[_SCORE_COLORS[k] for k in present],
        autopct="%1.0f%%",
        startangle=140,
    )
    pass_rate = score_counts.get("PASS", 0) / max(len(cases), 1) * 100
    ax.set_title(f"Score Distribution\nPass rate: {pass_rate:.0f}%")

    # Right: per-case horizontal bar (width = latency, color = score)
    ax2 = axes[1]
    test_ids = [c["test_id"] for c in cases]
    colors = [_SCORE_COLORS.get(c["score"], "#95a5a6") for c in cases]
    latencies = [max(c["latency_ms"], 1) / 1000 for c in cases]

    ax2.barh(test_ids, latencies, color=colors)
    ax2.set_xlabel("Latency (s)")
    ax2.set_title("Per-Case Results\n(color = score, width = latency)")

    legend_patches = [
        mpatches.Patch(color=_SCORE_COLORS[s], label=s)
        for s in ["PASS", "FAIL", "WARN", "ERROR"]
    ]
    ax2.legend(handles=legend_patches, loc="lower right", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path


def generate_regression_dashboard(
    run_a: dict,
    run_b: dict,
    output_path: str | Path = "regression.png",
) -> Path:
    output_path = Path(output_path)

    cases_a = {c["test_id"]: c["score"] for c in run_a["cases"]}
    cases_b = {c["test_id"]: c["score"] for c in run_b["cases"]}
    all_ids = sorted(set(cases_a) | set(cases_b))

    n = len(all_ids)
    fig, ax = plt.subplots(figsize=(12, max(5, n * 0.5 + 2)))

    bar_h = 0.35
    y = list(range(n))
    colors_a = [_SCORE_COLORS.get(cases_a.get(tid, "ERROR"), "#95a5a6") for tid in all_ids]
    colors_b = [_SCORE_COLORS.get(cases_b.get(tid, "ERROR"), "#95a5a6") for tid in all_ids]

    ax.barh(
        [i - bar_h / 2 for i in y], [1] * n, bar_h,
        color=colors_a, label=f"A: {run_a['run_id'][:8]}",
    )
    ax.barh(
        [i + bar_h / 2 for i in y], [1] * n, bar_h,
        color=colors_b, label=f"B: {run_b['run_id'][:8]}",
    )

    ax.set_yticks(y)
    ax.set_yticklabels(all_ids, fontsize=8)
    ax.set_xticks([])

    regressions = [t for t in all_ids if cases_a.get(t) == "PASS" and cases_b.get(t) == "FAIL"]
    fixes = [t for t in all_ids if cases_a.get(t) == "FAIL" and cases_b.get(t) == "PASS"]

    title_lines = [
        "Regression Comparison",
        f"A: {run_a['suite_name']} @ {run_a['model']} ({run_a['timestamp'][:10]})",
        f"B: {run_b['suite_name']} @ {run_b['model']} ({run_b['timestamp'][:10]})",
    ]
    if regressions:
        title_lines.append(f"REGRESSIONS (PASS→FAIL): {', '.join(regressions)}")
    if fixes:
        title_lines.append(f"FIXES (FAIL→PASS): {', '.join(fixes)}")
    ax.set_title("\n".join(title_lines), fontsize=9)

    legend_patches = [
        mpatches.Patch(color=_SCORE_COLORS[s], label=s)
        for s in ["PASS", "FAIL", "WARN", "ERROR"]
    ]
    ax.legend(handles=legend_patches, fontsize=8, loc="lower right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path
