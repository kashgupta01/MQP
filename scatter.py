"""
protein_complex_visualisation.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generate two images from a CSV of protein-complex data:

1.  A scatter/bubble plot (`complex_scatter.png`)
    • x-axis      – hidden (organisms are only implicit clusters)
    • y-axis      – number of protein subunits
    • bubble area – proportional to subunit count
    • colour      – one hue per organism

2.  A standalone legend image (`legend.png`)
    • same colours and labels as the plot
-----------------------------------------------------------------
Required columns in the CSV
-----------------------------------------------------------------
Organism           name of the model organism (categorical)
Accession_Mapped   semicolon-delimited list of protein accessions;
                   may contain blanks or the literal “Not Found”
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path


# ───────────────────────────────────────────────────────────────────────────────
# Helper: count valid subunits in “Accession_Mapped”
# ───────────────────────────────────────────────────────────────────────────────
def count_subunits(cell: str | float) -> int:
    """
    Return the number of real protein accessions in a semicolon-delimited cell.
    Ignores blanks and the string 'Not Found' (case-insensitive).
    """
    if pd.isna(cell):
        return 0
    parts = [p.strip() for p in str(cell).split(";")]
    parts = [p for p in parts if p and p.lower() != "not found"]
    return len(parts)


# ───────────────────────────────────────────────────────────────────────────────
# Main visualisation routine
# ───────────────────────────────────────────────────────────────────────────────
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
    """
    Read `csv_path`, create a bubble scatter plot **without x-axis labels**
    and a separate legend image.  Images are saved as PNG to the supplied paths.
    """
    df = pd.read_csv(csv_path)
    df["subunit_count"] = df["Accession_Mapped"].apply(count_subunits)

    # --- assign positions, colours, and marker sizes -------------------------
    orgs = sorted(df["Organism"].dropna().unique())
    org_to_center = {org: i for i, org in enumerate(orgs)}

    cm = mpl.colormaps.get_cmap(cmap)
    org_to_color = {
        org: cm(i / max(1, len(orgs) - 1)) for i, org in enumerate(orgs)
    }

    rng = np.random.default_rng(seed)
    df["x"] = (
        df["Organism"].map(org_to_center) + rng.uniform(-jitter, jitter, len(df))
    )
    df["size"] = base_size + size_scale * df["subunit_count"]
    df["color"] = df["Organism"].map(org_to_color)

    # --- scatter plot (no x-labels) ------------------------------------------
    fig_scatter, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(
        df["x"],
        df["subunit_count"],
        s=df["size"],
        c=df["color"],
        alpha=0.8,
        edgecolors="k",
        linewidths=0.4,
        marker="o",
    )
    ax.set_xticks([])       # remove tick marks
    ax.set_xlabel("")       # no x-axis label
    ax.set_ylabel("Number of protein subunits")
    ax.set_title("Benchmarch Dataset")
    ax.margins(x=0.05)
    fig_scatter.tight_layout()
    fig_scatter.savefig(scatter_png, dpi=300, bbox_inches="tight")
    plt.close(fig_scatter)

    # --- standalone legend ----------------------------------------------------
    fig_leg, ax_leg = plt.subplots(figsize=(3, 0.8 * len(orgs)))
    handles = [
        mpl.lines.Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            markersize=8,
            markerfacecolor=org_to_color[o],
            markeredgecolor="k",
            label=o,
        )
        for o in orgs
    ]
    ax_leg.legend(handles=handles, frameon=False, loc="center")
    ax_leg.axis("off")
    fig_leg.savefig(legend_png, dpi=300, bbox_inches="tight")
    plt.close(fig_leg)

    summary = (
    df.groupby("Organism")["subunit_count"]
        .sum()
        .sort_values(ascending=False)
    )
    print("\nSubunit count per organism (total across all complexes):")
    for org, total in summary.items():
        print(f"  {org}: {total}")

    print(f"Saved scatter plot  → {Path(scatter_png).resolve()}")
    print(f"Saved legend image → {Path(legend_png).resolve()}")


# ───────────────────────────────────────────────────────────────────────────────
# Example usage (uncomment to run directly)
# ───────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    make_complex_plots("manual_mapping2.csv")
