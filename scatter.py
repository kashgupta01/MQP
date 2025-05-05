"""
scatter_split.py
────────────────
Visualise a benchmark CSV as scatter plots (zero-shot / few-shot / contextual)
and generate a whitespace-free legend image.

Outputs
-------
complex_scatter.png   three aligned scatter plots
legend.png            tightly cropped legend

CSV requirements
----------------
Technique          (“zero-shot”, “few-shot”, or “contextual” – case-insensitive)
Organism
Accession_Mapped   semicolon-separated accession list
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def count_subunits(field: str | float) -> int:
    """Return the number of protein accessions in a semicolon-delimited field."""
    if pd.isna(field):
        return 0
    parts = [p for p in str(field).split(";") if p and p.strip().lower() != "not found"]
    return len(parts)


# ──────────────────────────────────────────────────────────────────────────────
# Main routine
# ──────────────────────────────────────────────────────────────────────────────
def make_complex_plots(
    csv_path: str | Path,
    *,
    scatter_png: str | Path = "complex_scatter.png",
    legend_png: str | Path = "legend.png",
    jitter: float = 0.25,
    base_size: float = 40,
    size_scale: float = 40,
    seed: int = 42,
    cmap: str = "tab10",
) -> None:
    """Read *csv_path* and write both PNGs."""
    # ─── load & augment data ──────────────────────────────────────────────────
    df = pd.read_csv(csv_path)
    df["subunit_count"] = df["Accession_Mapped"].apply(count_subunits)

    # Organism order & colour mapping
    orgs = sorted(df["Organism"].dropna().unique())
    org_to_center = {o: i for i, o in enumerate(orgs)}

    cm = mpl.colormaps.get_cmap(cmap)
    org_to_color = {o: cm(i / max(1, len(orgs) - 1)) for i, o in enumerate(orgs)}

    # Identical x-coords & colours for every subplot
    rng = np.random.default_rng(seed)
    df["x"] = df["Organism"].map(org_to_center) + rng.uniform(-jitter, jitter, len(df))
    df["area"] = base_size + size_scale * df["subunit_count"]
    df["color"] = df["Organism"].map(org_to_color)

    # ─── three technique-specific panels ──────────────────────────────────────
    techniques = ["zero-shot", "few-shot", "contextual"]
    ncols = len(techniques)

    fig_scatter, axes = plt.subplots(
        1,
        ncols,
        figsize=(6 * ncols, 6),
        sharey=True,
    )

    for ax, tech in zip(axes, techniques):
        mask = df["Technique"].str.contains(tech, case=False, na=False)

        ax.scatter(
            df.loc[mask, "x"],
            df.loc[mask, "subunit_count"],
            s=df.loc[mask, "area"],
            c=df.loc[mask, "color"],
            alpha=0.8,
            edgecolors="k",
            linewidths=0.4,
            marker="o",
        )

        ax.set_xticks([])
        ax.set_xlabel("")
        ax.set_title(tech.capitalize(), pad=10, weight="bold")

    axes[0].set_ylabel("Number of protein sub-units")
    fig_scatter.suptitle("GPT-4o Data Spread", weight="bold", y=0.98)
    fig_scatter.tight_layout()
    fig_scatter.savefig(scatter_png, dpi=300, bbox_inches="tight")
    plt.close(fig_scatter)

    # ─── tight-cropped legend ─────────────────────────────────────────────────
    handles = [
        mpl.lines.Line2D(
            [], [], marker="o", linestyle="", markersize=8,
            markerfacecolor=org_to_color[o], markeredgecolor="k", label=o,
        )
        for o in orgs
    ]

    fig_leg = plt.figure(figsize=(2.0, 0.36 * len(orgs)))
    legend = fig_leg.legend(
        handles=handles,
        loc="center left",
        frameon=False,
        borderaxespad=0,
        labelspacing=0.35,
        handletextpad=0.4,
    )

    fig_leg.canvas.draw()
    bbox = legend.get_window_extent().transformed(fig_leg.dpi_scale_trans.inverted())
    fig_leg.savefig(legend_png, dpi=300, bbox_inches=bbox, pad_inches=0)
    plt.close(fig_leg)

    # ─── console summary: totals per technique *and* organism ────────────────
    print("\nSub-unit totals per organism, split by prompt technique:")
    summary = (
        df.groupby(["Technique", "Organism"])["subunit_count"]
        .sum()
        .sort_index(level=0)
    )
    for tech in techniques:
        print(f"\n  {tech.capitalize()}:")
        subtot = summary.loc[summary.index.get_level_values("Technique").str.contains(tech, case=False)]
        for org, total in subtot.items():
            print(f"    {org}: {total}")

    print(f"\nSaved scatter → {Path(scatter_png).resolve()}")
    print(f"Saved legend  → {Path(legend_png).resolve()}")


# ──────────────────────────────────────────────────────────────────────────────
# Run directly
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    make_complex_plots("manual_mapping2.csv")  # adjust path as needed
