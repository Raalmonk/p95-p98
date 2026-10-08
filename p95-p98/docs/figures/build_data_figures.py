"""Render three documentation charts from retained scalar tables only.

Run with Python 3 and matplotlib. No model, structure, or evaluator is run.
The JSON sidecar records exact plotted values, row joins and source hashes.
"""

from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

from figure_style import BLUE, LIGHT_BLUE, GRAY, LIGHT_GRAY, GRID, INK, MUTED, OUT, plt, save
from matplotlib.lines import Line2D

plt.rcParams.update({"svg.hashsalt": "ngngk-data-figures-v1", "font.size": 13})

DOCS = OUT.parent
CASP = DOCS / "closeout/casp15/results_per_input.csv"
COUNTS = DOCS / "closeout/casp15/mc_control_counts.csv"
BENCH = DOCS / "closeout/results/per_input.csv"
SUMMARY = DOCS / "closeout/results/summary.json"
METHODS = ("P95", "P98", "native_NGK", "short_NGK")
TARGETS = ("T1104", "T1109", "T1123", "T1139", "T1187", "T1194")
COLORS = {"P95": LIGHT_BLUE, "P98": BLUE, "native_NGK": GRAY, "short_NGK": LIGHT_GRAY}
NAMES = {"P95": "P95", "P98": "P98", "native_NGK": "Native NGK", "short_NGK": "Short NGK"}
MARKERS = {"P95": "o", "P98": "o", "native_NGK": "s", "short_NGK": "D"}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(rows, field):
    return statistics.mean(float(row[field]) for row in rows)


def source_record(path):
    return {"path": path.relative_to(DOCS).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def derive_data():
    rows = read_csv(CASP)
    counts = read_csv(COUNTS)
    assert len(rows) == 48
    expected = {(t, s, m) for t in TARGETS for s in ("AlphaFold2", "ESMFold") for m in METHODS}
    by_key = {(r["target"], r["start_model"], r["method"]): r for r in rows}
    assert set(by_key) == expected and len(by_key) == len(rows)
    assert all(r["status"] == "COMPLETE" and r["geometry_valid"] == "true" for r in rows)
    count_by_key = {(r["target"], r["start_model"], r["method"]): r for r in counts}
    assert len(count_by_key) == len(counts) == 24
    panels = {}
    for start in ("AlphaFold2", "ESMFold"):
        selected = [r for r in rows if r["start_model"] == start]
        sources = {}
        for r in selected:
            value = float(r["source_local_bb_rmsd_A"])
            assert r["target"] not in sources or sources[r["target"]] == value
            sources[r["target"]] = value
        assert len(sources) == 6
        native_cpu = mean([r for r in selected if r["method"] == "native_NGK"], "method_cpu_seconds")
        methods = {}
        for method in METHODS:
            subset = [r for r in selected if r["method"] == method]
            assert len(subset) == 6
            methods[method] = {
                "n": len(subset),
                "mean_method_cpu_seconds": mean(subset, "method_cpu_seconds"),
                "mean_local_bb_rmsd_A": mean(subset, "local_bb_rmsd_A"),
                "cpu_percent_native": 100 * mean(subset, "method_cpu_seconds") / native_cpu,
                "input_indices": [int(r["index"]) for r in subset],
            }
        panels[start] = {"n": 6, "source_mean_local_bb_rmsd_A": statistics.mean(sources.values()),
                         "methods": methods}
    early = {}
    for start, targets in (("AlphaFold2", TARGETS), ("ESMFold", ("T1123", "T1139"))):
        items = []
        for target in targets:
            p98 = by_key[(target, start, "P98")]
            native = by_key[(target, start, "native_NGK")]
            counter = count_by_key[(target, start, "P98")]
            assert math.isclose(float(p98["method_cpu_seconds"]), float(counter["method_cpu_seconds"]), abs_tol=1e-6)
            assert p98["index"] == counter["index"]
            items.append({"target": target, "P98_cpu_seconds": float(p98["method_cpu_seconds"]),
                          "native_cpu_seconds": float(native["method_cpu_seconds"]),
                          "P98_kic_attempts": int(counter["kic"]), "P98_safe_stops": int(counter["safe_stop"]),
                          "P98_index": int(p98["index"]), "native_index": int(native["index"]),
                          "P98_terminal_sha256": counter["terminal_sha256"]})
        early[start] = {"shown": len(items), "total": 6, "rows": items}
    assert [r["P98_kic_attempts"] for r in early["AlphaFold2"]["rows"]] == [0, 0, 13, 2, 0, 27]
    assert all(r["P98_safe_stops"] == 1 for r in early["AlphaFold2"]["rows"])
    assert all(r["P98_kic_attempts"] == 800 and r["P98_safe_stops"] == 0 for r in early["ESMFold"]["rows"])

    bench_rows = read_csv(BENCH)
    assert len(bench_rows) == 144
    bench = {(r["method"], int(r["input_index"])): r for r in bench_rows}
    assert len(bench) == 144
    reference = json.loads(SUMMARY.read_text(encoding="utf-8"))["paired_valid_deltas_method_minus_NGK"]
    deltas = []
    for group in ("WS", "hard"):
        for method in ("P95", "P98"):
            pairs = []
            excluded = []
            for index in range(48):
                a, b = bench[(method, index)], bench[("NGK", index)]
                assert (a["input_index"], a["episode_id"], a["component"], a["domain"]) == (
                    b["input_index"], b["episode_id"], b["component"], b["domain"])
                if (a["domain"] == "ws280") != (group == "WS"):
                    continue
                if a["valid"] == b["valid"] == "True":
                    pairs.append((a, b))
                else:
                    excluded.append(index)
            assert len(pairs) == (32 if group == "WS" else 15)
            values = {field: statistics.mean(float(a[field]) - float(b[field]) for a, b in pairs)
                      for field in ("legacy_local_rmsd_A", "legacy_global_rmsd_A")}
            for field, value in values.items():
                assert math.isclose(value, reference[method][group][field], rel_tol=0, abs_tol=1e-12)
            assert len(pairs) == reference[method][group]["n"]
            deltas.append({"method": method, "group": group, "n": len(pairs),
                           "planned": 32 if group == "WS" else 16, **values,
                           "paired_input_indices": [int(a["input_index"]) for a, _ in pairs],
                           "excluded_input_indices": excluded})
    return {"sources": [source_record(p) for p in (CASP, COUNTS, BENCH, SUMMARY)],
            "derivation": {"casp15": "Unweighted means of the six retained scalar rows per method/start; CPU ratio is ratio of group means.",
                           "early_stopping": "Retained method CPU joined to counters by target/start/method and checked by index.",
                           "bench48": "Mean of paired method-minus-NGK frozen raw RMSD differences; exact input/episode/component/domain joins; both-valid pairs only."},
            "casp15_quality_cost": panels, "casp15_early_stopping": early,
            "bench48_subgroup_deltas": deltas}


def base(title, subtitle, size):
    fig = plt.figure(figsize=size)
    fig.text(.055, .962, title, fontsize=25, fontweight="bold", va="top")
    fig.text(.055, .901, subtitle, fontsize=14, color=MUTED, va="top")
    return fig


def clean_axis(ax):
    ax.set_axisbelow(True)
    ax.grid(color=GRID, linewidth=.8)
    ax.tick_params(labelsize=13, length=0, pad=9)


def point_label(ax, x, y, text, color, ha="left", leader=None):
    ax.text(x, y, text, ha=ha, va="top", fontsize=13, color=color, linespacing=1.5, zorder=5)
    if leader:
        ax.plot([p[0] for p in leader], [p[1] for p in leader], color=color, lw=1.15, zorder=2)


def quality_cost(data):
    fig = base("New proteins: CPU time and accuracy",
               "Mean results on six targets per starting model", (16, 11))
    panels = data["casp15_quality_cost"]
    for panel_index, start in enumerate(("AlphaFold2", "ESMFold")):
        group = panels[start]
        bottom = .535 if panel_index == 0 else .145
        cpu_ax = fig.add_axes([.165, bottom, .365, .225])
        rmsd_ax = fig.add_axes([.625, bottom, .33, .225])
        fig.text(.055, bottom + .303, f"{start} starts (n = 6)", fontsize=21,
                 fontweight="bold", va="bottom")
        for ax in (cpu_ax, rmsd_ax):
            clean_axis(ax)
            ax.grid(axis="y", visible=False)
            ax.set_ylim(3.65, -.65)
            ax.tick_params(labelsize=14)
            ax.spines["left"].set_visible(False)
        cpu_ax.set(xlim=(0, 400), xticks=[0, 100, 200, 300, 400])
        rmsd_ax.set(xlim=(0, 6.5), xticks=[0, 1, 2, 3, 4, 5, 6])
        cpu_ax.set_yticks(range(4), [NAMES[m] for m in METHODS], fontsize=16)
        rmsd_ax.set_yticks([])
        cpu_ax.set_title("CPU time (s) · % of NGK", loc="left", fontsize=18, fontweight="bold", pad=36)
        rmsd_ax.set_title("Local backbone RMSD (Å)", loc="left", fontsize=18,
                          fontweight="bold", pad=36)
        source = group["source_mean_local_bb_rmsd_A"]
        rmsd_ax.axvline(source, color=INK, linestyle=(0, (4, 4)), linewidth=1.5, zorder=4)
        rmsd_ax.text(0, 1.075, f"Dashed line: untouched source {source:.3f} Å",
                     transform=rmsd_ax.transAxes, fontsize=13, color=MUTED, va="bottom")
        for row_index, method in enumerate(METHODS):
            item = group["methods"][method]
            cpu = item["mean_method_cpu_seconds"]
            rmsd = item["mean_local_bb_rmsd_A"]
            ratio = item["cpu_percent_native"]
            cpu_ax.barh(row_index, cpu, height=.54, color=COLORS[method], zorder=3)
            rmsd_ax.barh(row_index, rmsd, height=.54, color=COLORS[method], zorder=3)
            cpu_ax.text(cpu + 6, row_index, f"{cpu:.1f} s · {ratio:.1f}%", va="center",
                        fontsize=15, color=INK, zorder=5)
            rmsd_ax.text(rmsd + .10, row_index, f"{rmsd:.3f}", va="center",
                         fontsize=15, color=INK, zorder=5)
    fig.text(.165, .060, "Lower is better in both columns.",
             fontsize=14, color=MUTED)
    # Embed glyph outlines for this chart so GitHub does not substitute fonts.
    with plt.rc_context({"svg.fonttype": "path"}):
        save(fig, "casp15_quality_cost")


def early_stopping(data):
    fig = base("P98 stopped early on AlphaFold2 starts",
               "Recorded method CPU and P98 KIC-attempt counts", (16, 11))
    axes = [fig.add_axes([.105, .435, .82, .375]), fig.add_axes([.105, .19, .82, .14])]
    sections = data["casp15_early_stopping"]
    for i, (ax, start) in enumerate(zip(axes, sections)):
        items = sections[start]["rows"]
        n = len(items)
        clean_axis(ax)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, 500)
        ax.set_xticks(range(0, 501, 100))
        ax.set_ylim(n - .45, -.6)
        ax.set_yticks(range(n), [r["target"] for r in items])
        label = "A   AlphaFold2 starts: all 6 targets" if i == 0 else "B   ESMFold starts: selected 2 of 6 targets"
        ax.set_title(label, fontsize=18, fontweight="bold", loc="left", pad=21)
        for j, item in enumerate(items):
            p98, native = item["P98_cpu_seconds"], item["native_cpu_seconds"]
            ax.barh(j - .16, p98, height=.255, color=BLUE, zorder=3)
            ax.barh(j + .16, native, height=.255, color=GRAY, zorder=3)
            stop = "stopped early" if item["P98_safe_stops"] else "no stop"
            blue_text = f"{p98:.3f} s · {item['P98_kic_attempts']} KIC attempts · {stop}"
            ax.text(p98 + 4 if i == 0 else 5, j - .16, blue_text, fontsize=13, va="center", color=BLUE if i == 0 else "white", zorder=4)
            ax.text(native + 4, j + .16, f"{native:.3f} s", fontsize=13, va="center", color=INK, zorder=4)
        ax.set_xlabel("Method CPU per input (s)", labelpad=11, fontsize=14)
    handles = [Line2D([0], [0], lw=8, color=BLUE, label="P98"), Line2D([0], [0], lw=8, color=GRAY, label="Native warm-start NGK")]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(.93, .925), frameon=False, ncol=2, fontsize=13)
    fig.text(.105, .072, "Zero KIC attempts does not mean zero work: setup, sidechain steps and minimization still run.", fontsize=13, color=MUTED)
    fig.text(.105, .043, "Panel B shows only the two ESMFold runs discussed in the docs.", fontsize=13, color=MUTED)
    save(fig, "casp15_early_stopping")


def subgroup_deltas(data):
    fig = base("BENCH48: better on W/S, worse on hard inputs",
               "Mean paired change versus NGK · method minus NGK · matched valid results", (16, 8.8))
    rows = data["bench48_subgroup_deltas"]
    axes = [fig.add_axes([.15, .30, .32, .46]), fig.add_axes([.645, .30, .32, .46])]
    fields = ("legacy_local_rmsd_A", "legacy_global_rmsd_A")
    ranges = ((-.25, 1.02), (-.09, .255))
    ticks = ((-.2, 0, .2, .4, .6, .8, 1.0), (-.05, 0, .05, .10, .15, .20, .25))
    for i, (ax, field) in enumerate(zip(axes, fields)):
        clean_axis(ax)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(*ranges[i])
        ax.set_xticks(ticks[i])
        ax.set_ylim(3.65, -.65)
        ax.axvline(0, color=INK, linewidth=1.3, zorder=2)
        ax.axhline(1.5, color=GRID, linewidth=1, zorder=1)
        ax.set_yticks(range(4), [f"{r['method']} {'W/S' if r['group'] == 'WS' else 'hard'} (n = {r['n']})" for r in rows])
        ax.set_title(f"{'A   Local' if i == 0 else 'B   Global'} RMSD", loc="left", fontsize=18, fontweight="bold", pad=20)
        ax.set_xlabel("Mean paired change (Å)", fontsize=14, labelpad=14)
        for j, r in enumerate(rows):
            value = r[field]
            ax.barh(j, value, height=.50, color=COLORS[r["method"]], zorder=3)
            gap = (ranges[i][1] - ranges[i][0]) * .021
            if value < 0:
                ax.text(value, j - .30, f"{value:+.3f}", ha="left", va="bottom", fontsize=14, color=INK,
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5}, zorder=4)
            else:
                ax.text(value + gap, j, f"{value:+.3f}", ha="left", va="center", fontsize=14, color=INK)
    fig.text(.15, .197, "Left of zero = closer to the experimental structure than NGK.", fontsize=14, color=INK)
    fig.text(.055, .128, "Frozen raw RMSD: W/S uses backbone atoms; hard uses CA atoms. Local regions are expanded W/S regions and hard loop unions.", fontsize=13, color=MUTED)
    fig.text(.055, .094, "Compare within each group. NGK’s one invalid hard result is excluded (15 of 16 pairs).", fontsize=13, color=MUTED)
    fig.text(.055, .060, "These are paired means, not the README’s display CA medians, where both programs look better than NGK.", fontsize=13, color=MUTED)
    save(fig, "bench48_subgroup_deltas")


def main():
    data = derive_data()
    quality_cost(data)
    early_stopping(data)
    subgroup_deltas(data)
    data["export"] = {"format": ["SVG: outlined text in casp15_quality_cost; selectable text in the other two figures", "PNG"], "png_dpi": 180,
                      "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      "style_sha256": hashlib.sha256((OUT / "figure_style.py").read_bytes()).hexdigest(),
                      "figures": {name: {suffix: hashlib.sha256((OUT / f"{name}.{suffix}").read_bytes()).hexdigest()
                                          for suffix in ("svg", "png")}
                                  for name in ("casp15_quality_cost", "casp15_early_stopping", "bench48_subgroup_deltas")}}
    (OUT / "data_figures_provenance.json").write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print("Rendered 3 SVGs, 3 PNGs and exact derived-data provenance; all retained-data checks passed.")


if __name__ == "__main__":
    main()
