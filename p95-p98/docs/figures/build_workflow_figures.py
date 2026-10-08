"""Build the three workflow figures from Claude's FIGURES_TODO.md.

Sources (relative to this directory):
  FIGURES_TODO.md; ../METHOD.md; ../PROMOD3.md; ../NATIVE_RUNTIME.md;
  ../closeout/DISCOVERY.md; ../../README.md.
Text in those source documents is not modified. No scientific runs are performed.
Run: python3 build_workflow_figures.py
Outputs: editable-text SVG and 180 dpi PNG, one pair per diagram.
"""
from pathlib import Path
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "ngngk-workflow-mpl"))
from figure_style import (plt, FancyBboxPatch, FancyArrowPatch, INK, MUTED,
                          BLUE, PALE, LIGHT_BLUE, GRAY, GRID, PAPER, save)

plt.rcParams["svg.hashsalt"] = "ngngk-workflow-20261008"
PEOPLE = "#936D32"
PEOPLE_PALE = "#FAF3E8"
HOST_PALE = "#F4F6F7"


def start(title, subtitle, height):
    fig = plt.figure(figsize=(16, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 16), ylim=(0, height))
    ax.axis("off")
    ax.text(.6, height-.48, title, fontsize=25, fontweight="bold", va="top")
    ax.text(.6, height-1.03, subtitle, fontsize=14, color=MUTED, va="top")
    return fig, ax


def panel(ax, x, y, w, h, color=GRAY, fill=HOST_PALE):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.015,rounding_size=0.10",
                 facecolor=fill, edgecolor=color, linewidth=1.15))


def txt(ax, x, y, text, size=14, color=INK, bold=False, ha="left", va="top"):
    return ax.text(x, y, text, fontsize=size, color=color,
                   fontweight="bold" if bold else "normal", ha=ha, va=va,
                   linespacing=1.4)


def route(ax, points, color=MUTED, width=1.6, head=True, dashed=False):
    """Orthogonal connectors stay in the whitespace between cards."""
    for a, b in zip(points[:-2], points[1:-1]):
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=width,
                ls="--" if dashed else "-", solid_capstyle="round")
    a, b = points[-2:]
    if head:
        ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>",
                     mutation_scale=15, color=color, lw=width,
                     linestyle="--" if dashed else "-", shrinkA=0, shrinkB=3))
    else:
        ax.plot([a[0], b[0]], [a[1], b[1]], color=color, lw=width,
                ls="--" if dashed else "-")


def role_card(ax, x, y, w, h, role, title, body, color=GRAY, fill=HOST_PALE):
    panel(ax, x, y, w, h, color, fill)
    txt(ax, x+.22, y+h-.2, role.upper(), 13, color, True)
    txt(ax, x+.22, y+h-.60, title, 16, INK, True)
    txt(ax, x+.22, y+h-1.04, body, 13)


def search_loop():
    fig, ax = start("OpenEvolve search loop",
                    "How the programs were found, then deployed", 9.2)
    role_card(ax, .6, 5.25, 3.2, 2.25, "People", "Set the rules",
              "Editable decide(view)\nAllowed observations\nFive objectives + budgets",
              PEOPLE, PEOPLE_PALE)
    role_card(ax, 4.45, 5.25, 3.2, 2.25, "LLM", "Propose a code edit",
              "Parent + peer programs\nFeedback scores",
              BLUE, PALE)
    role_card(ax, 8.30, 5.25, 3.2, 2.25, "Host software", "Apply and check",
              "Apply the patch\nStatic + interface checks")
    role_card(ax, 12.15, 5.25, 3.25, 2.25, "Host software", "Run real modeling",
              "Rosetta NGK / ProMod3\n48 BENCH48 inputs")
    for a, b in [(3.8, 4.45), (7.65, 8.30), (11.5, 12.15)]:
        route(ax, [(a, 6.38), (b, 6.38)])

    role_card(ax, 8.30, 2.70, 7.10, 1.75, "Host software",
              "Score results and update the archive",
              "Five objectives → feedback for the next proposal")
    route(ax, [(13.8, 5.25), (13.8, 4.45)])
    route(ax, [(8.30, 3.60), (6.05, 3.60), (6.05, 5.25)], BLUE)
    txt(ax, 6.22, 4.72, "Feedback", 13, BLUE)
    txt(ax, .60, 4.36, "About 100 proposals", 17, INK, True)
    txt(ax, .60, 3.92, "At most two at a time; wave by wave", 13, MUTED)
    txt(ax, .60, 3.25, "101 starts → 100 returned → 99 evaluated", 13, INK)

    # The archive exit crosses the discovery/deployment boundary only once.
    route(ax, [(9.45, 2.70), (9.45, 2.27), (2.20, 2.27), (2.20, 1.46)], BLUE)
    ax.plot([.6, 15.4], [1.93, 1.93], color=GRAY, lw=1.15, ls=(0, (5, 4)))
    txt(ax, 15.38, 2.19, "DISCOVERY", 13, MUTED, True, ha="right")
    txt(ax, 15.38, 1.75, "DEPLOYMENT", 13, MUTED, True, ha="right")
    steps = [(.6, "1  Pick P95 and P98", "From the search archive"),
             (4.45, "2  Freeze the programs", "Keep the selected code fixed"),
             (8.30, "3  Test on new proteins", "CASP15"),
             (12.15, "4  Run ordinary CPU code", "No LLM calls")]
    for x, title, body in steps:
        w = 3.25 if x == 12.15 else 3.20
        panel(ax, x, .31, w, 1.14, LIGHT_BLUE, PALE)
        txt(ax, x+.18, 1.23, title, 14, BLUE, True)
        txt(ax, x+.18, .78, body, 13)
    for a, b in [(3.8, 4.45), (7.65, 8.30), (11.5, 12.15)]:
        route(ax, [(a, .89), (b, .89)], BLUE)
    save(fig, "search_loop")


def decide_interface():
    fig, ax = start("What the frozen program sees and controls",
                    "Input structure and current candidates → decide(view) → decision + updated memory", 10)
    panel(ax, .6, 3.16, 4.58, 5.13)
    txt(ax, .86, 8.00, "Host builds the view", 18, INK, True)
    txt(ax, .86, 7.42, "event", 15, BLUE, True)
    txt(ax, .86, 7.06, "Host event for this call", 14)
    txt(ax, .86, 6.49, "observation", 15, BLUE, True)
    txt(ax, .86, 6.09,
        "Starting + current geometry\nFixed energies\nPer-loop + per-residue data\nRemaining budget + available actions\nLimited history", 14)
    txt(ax, .86, 4.17, "memory", 15, BLUE, True)
    txt(ax, .86, 3.79, "Notes kept for this run", 14)

    panel(ax, 5.93, 4.62, 3.45, 2.17, LIGHT_BLUE, PALE)
    txt(ax, 7.655, 6.45, "Frozen P95 / P98", 18, BLUE, True, ha="center")
    txt(ax, 7.655, 5.89, "decide(view)", 18, INK, True, ha="center")
    txt(ax, 7.655, 5.30, "Decision + updated memory", 13, INK, ha="center")
    route(ax, [(5.18, 5.72), (5.93, 5.72)])
    route(ax, [(9.38, 5.72), (9.81, 5.72), (9.81, 6.67), (10.24, 6.67)], BLUE)
    route(ax, [(9.81, 5.72), (9.81, 4.03), (10.24, 4.03)], BLUE)

    panel(ax, 10.24, 5.26, 5.16, 3.03, LIGHT_BLUE, PALE)
    txt(ax, 10.5, 7.99, "Outer routing", 18, BLUE, True)
    txt(ax, 10.5, 7.48, "Choose an action", 14, INK, True)
    txt(ax, 10.5, 7.10,
        "ProMod3 database lookup\nNGK refine / rebuild\nMinimize / deliver", 14)
    txt(ax, 10.5, 5.89, "Choose the parent · keep candidates", 14)
    panel(ax, 10.24, 2.68, 5.16, 2.11, LIGHT_BLUE, PALE)
    txt(ax, 10.5, 4.50, "Inner NGK callbacks", 18, BLUE, True)
    txt(ax, 10.5, 3.98, "Stop early\nNative acceptance or temperature × 0.75", 14)
    txt(ax, 10.5, 3.07, "Native-low delivery", 13, MUTED)

    route(ax, [(7.65, 4.62), (7.65, 2.70), (3.23, 2.70), (3.23, 3.16)], BLUE)
    txt(ax, 7.35, 3.72, "Updated memory\nfor the next call", 13, BLUE, ha="right")

    # A separate wall makes the excluded information visibly disconnected.
    ax.plot([.6, 15.4], [2.20, 2.20], color=GRAY, lw=3.0)
    panel(ax, .6, .40, 14.8, 1.36, GRAY, HOST_PALE)
    txt(ax, .86, 1.52, "Never enters a running program", 16, INK, True)
    txt(ax, .86, 1.06, "Reference coordinates\nReference RMSD", 14, MUTED)
    txt(ax, 5.25, 1.06, "Benchmark labels\nPDB / file IDs", 14, MUTED)
    txt(ax, 9.71, 1.06, "Offline evaluation results\nAlphaFold confidence scores", 14, MUTED)
    save(fig, "decide_interface")


def runtime_architecture():
    fig, ax = start("Install layout: two Python environments",
                    "Data flow of one P95 / P98 run", 10.5)
    panel(ax, .6, 7.85, 6.50, 1.19)
    txt(ax, .86, 8.81, "Run inputs", 17, INK, True)
    txt(ax, .86, 8.40,
        "Input JSON: complete PDB + target sequence\nWork profile (reference tariff) + CPU / wall budget", 13)
    panel(ax, 9.2, 7.85, 6.20, 1.19)
    txt(ax, 9.46, 8.81, "One-time resource build", 17, INK, True)
    txt(ax, 9.46, 8.40,
        "protected.json → build_resources → resources/\nExclude the input before modeling", 13)

    panel(ax, .6, 2.72, 6.50, 4.57)
    txt(ax, .88, 6.96, "Host process", 19, INK, True)
    txt(ax, .88, 6.43, "Linux x86-64 · Python 3.12", 15)
    panel(ax, .89, 5.15, 5.92, .91, LIGHT_BLUE, PALE)
    txt(ax, 1.10, 5.81, "p95p98 CLI + frozen P95 / P98 policy", 16, BLUE, True)
    txt(ax, .88, 4.76, "Legacy NGK scheduler", 16, INK, True)
    txt(ax, .88, 4.26, "Licensed PyRosetta", 14)
    txt(ax, .88, 3.88, "2026.03+releasequarterly.5e498f1409", 14)
    ax.plot([.88, 6.81], [3.45, 3.45], color=GRID, lw=1.1)
    txt(ax, .88, 3.18, "Before refinement: check runtime version", 13, MUTED)

    panel(ax, 9.2, 2.72, 6.20, 4.57)
    txt(ax, 9.48, 6.96, "ProMod3 worker", 19, INK, True)
    txt(ax, 9.48, 6.43, "Python 3.14", 15)
    txt(ax, 9.48, 5.94, "ProMod3 3.7.0 + OpenStructure 2.12.0", 14)
    txt(ax, 9.48, 5.43, "--promod-python wrapper", 14, INK, True)
    txt(ax, 9.48, 5.05, "PYTHONPATH: p95-p98/src", 14)
    txt(ax, 9.48, 4.55, "resources/", 14, INK, True)
    txt(ax, 9.48, 4.16, "Manifest · filter ledger · StructureDB · FragDB", 13)
    ax.plot([9.48, 15.11], [3.72, 3.72], color=GRID, lw=1.1)
    txt(ax, 9.48, 3.48,
        "Before modeling: check native versions,\ndatabase SHA256 values + input filter ledger", 13, MUTED)

    route(ax, [(3.85, 7.85), (3.85, 7.29)])
    route(ax, [(12.3, 7.85), (12.3, 7.29)])
    route(ax, [(7.1, 5.40), (9.2, 5.40)], BLUE)
    route(ax, [(9.2, 4.73), (7.1, 4.73)], BLUE)
    txt(ax, 8.15, 6.02, "PDB + JSON\nfiles only", 14, BLUE, True, ha="center")

    route(ax, [(3.85, 2.72), (3.85, 1.95)])
    panel(ax, .6, .56, 14.80, 1.39)
    txt(ax, .88, 1.64, "Run outputs", 17, INK, True)
    txt(ax, .88, 1.14,
        "final.pdb     result.json     endpoint.json.gz     route_steps/     actions/", 15)
    save(fig, "runtime_architecture")


if __name__ == "__main__":
    search_loop()
    decide_interface()
    runtime_architecture()
