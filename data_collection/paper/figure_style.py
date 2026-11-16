"""Reusable matplotlib style for research figures — apply the project defaults once.

Import this instead of re-deriving the rules in every plot script:

    import sys; sys.path.insert(0, "<path>/research-figures/scripts")
    from figure_style import (apply_style, figsize, lock_box_aspect, legend_outside,
                              diverging, DIVERGING, sequential_to_white, PASTEL, MUTED)

    apply_style()                                  # English + Arial, no title, box on, grid off,
                                                   # constrained_layout on (panels never collide)
    fig, axes = plt.subplots(1, 2, figsize=figsize("4:3", ncols=2))  # grid-sized -> each panel 4:3
    lock_box_aspect(axes, "4:3")                    # GATE 1 — every panel holds the ratio, not the figure
    ax.plot(x, y, color=MUTED[0], lw=2.2, ms=5)     # lines -> MUTED (pastel washes out on thin strokes)
    ax.bar(x, h, color=PASTEL[:n])                  # filled areas -> PASTEL (no edge by default)
    ax.imshow(M, cmap=diverging("red-white-blue"))           # high<->low (red = high)
    ax.imshow(M, cmap=diverging("red-white-blue", reverse=True))  # inverse (red = low)
    ax.imshow(V, cmap=sequential_to_white("#4878D0"))        # values within one category

The defaults encode the standard: figure text is **English + Arial**, there is **no in-figure
title** (its content belongs in the report caption or the prompt answer), the axes are drawn as
a full **box on** (Matlab-style), and the **grid is off** unless asked for. Nothing here is
mandatory machinery — every value is a plain rcParam or a colormap you can override per figure.
"""
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

# --- Font sizes (pt) ---------------------------------------------------------
# Defaults, with the smaller values you may drop to *only* for readability — when labels
# overlap, when text covers the key result, or when the figure is shrunk into a Word body
# (12 pt). Do not go below the documented floor; tiny text defeats the figure.
LABEL_SIZE = 14   # axis labels      — default 14, readability floor 12 then 10
TICK_SIZE = 12    # axis tick labels — default 12, readability floor 10 then 8
LEGEND_SIZE = 10  # legend text      — default 10, readability floor 8 then 6


def apply_style(label=LABEL_SIZE, tick=TICK_SIZE, legend=LEGEND_SIZE,
                box=True, grid=False, layout=True, raster_dpi=300):
    """Set the research-figure rcParams globally. Call once before plotting.

    Arial is selected as the sans-serif face (falls back if the machine lacks it).
    `axes.unicode_minus=False` keeps minus signs on the ASCII glyph Arial always has.

    box    — draw the full axes rectangle (all four spines), i.e. Matlab `box on`. Default True.
             Set False for an open top/right (higher data-ink ratio) when a journal prefers it.
    grid   — light grid. Default False (off); set True to overlay a faint grid.
    layout — constrained_layout ON by default (GATE 3): matplotlib auto-reserves room for tick
             labels, axis labels and colourbars so adjacent panels never collide. Do NOT also
             call `fig.tight_layout()` — the two layout engines conflict. Set False only if you
             drive spacing by hand with `subplots_adjust`.

    Titles are not disabled here — they are simply never set; if a caller insists on one it is
    sized like a label.
    """
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "axes.labelsize": label,
        "axes.titlesize": label,
        "xtick.labelsize": tick,
        "ytick.labelsize": tick,
        "legend.fontsize": legend,
        "axes.spines.top": box,        # box on -> full rectangle (Matlab `box on`)
        "axes.spines.right": box,
        "axes.grid": grid,             # grid off by default; opt in
        "grid.linewidth": 0.5,
        "grid.alpha": 0.4,
        "legend.frameon": False,
        "figure.constrained_layout.use": layout,  # GATE 3 — auto-space panels, no collisions
        "figure.dpi": 120,             # on-screen
        "savefig.dpi": raster_dpi,     # raster export — 300+ for publication
        "savefig.bbox": "tight",
    })


# --- Aspect ratio ------------------------------------------------------------
# One of three aspect ratios only — 1:1, 4:3, 16:9 — so a figure set looks uniform.
# Orientation is free: landscape (wide) or portrait (tall) swaps width and height.
#
# GATE 1 — the approved ratio is held by *each subplot's axes box*, not the whole figure. For a
# (1, 2) grid a square overall figure would squash each panel to ~0.5:1; instead size the figure
# from the grid (`figsize(..., nrows, ncols)`) and hard-lock every panel's box with
# `lock_box_aspect(axes, ratio)`. With multiple panels the overall figure ratio is then free.
RATIOS = {"1:1": 1.0, "4:3": 4 / 3, "16:9": 16 / 9}


def figsize(ratio="4:3", long=6.4, orient="landscape", nrows=1, ncols=1):
    """Return a (width, height) tuple sized so *each subplot* holds an approved ratio.

    `long` is the longer side of a single panel in inches. landscape -> panel (long, short);
    portrait -> (short, long); 1:1 is square either way. The figure is the panel size scaled by
    the grid: width *= ncols, height *= nrows. With nrows=ncols=1 this is the whole-figure size
    (backward compatible). constrained_layout then adds the label/colourbar margins.
    """
    if ratio not in RATIOS:
        raise ValueError(f"ratio must be one of {list(RATIOS)}, got {ratio!r}")
    short = long / RATIOS[ratio]
    cell_w, cell_h = (long, short) if orient == "landscape" else (short, long)
    return (cell_w * ncols, cell_h * nrows)


def box_aspect(ratio="4:3", orient="landscape"):
    """Return the height/width value for `ax.set_box_aspect(...)` (GATE 1).

    matplotlib's `set_box_aspect` takes height-over-width; RATIOS stores width-over-height, so
    landscape is the reciprocal and portrait is the ratio itself. 1:1 -> 1.0 either way.
    """
    if ratio not in RATIOS:
        raise ValueError(f"ratio must be one of {list(RATIOS)}, got {ratio!r}")
    r = RATIOS[ratio]
    return (1 / r) if orient == "landscape" else r


def lock_box_aspect(axes, ratio="4:3", orient="landscape"):
    """Force every axes in `axes` to an approved box ratio (GATE 1), independent of figure shape.

    `axes` may be a single Axes, a list/tuple, or the ndarray that `plt.subplots` returns. Skip
    this on `imshow` panels where `aspect='equal'` should drive the box from the data grid.
    """
    a = box_aspect(ratio, orient)
    try:
        flat = list(axes.flat)                       # numpy array of Axes
    except AttributeError:
        flat = list(axes) if isinstance(axes, (list, tuple)) else [axes]
    for ax in flat:
        ax.set_box_aspect(a)
    return axes


# --- Legend placement --------------------------------------------------------
# GATE 2 — no text may cover the plotted data. Keep a legend inside only when it sits in clearly
# empty space; otherwise move it outside with this helper. With constrained_layout on (GATE 3) the
# figure reserves room for an outside legend automatically. If even outside it would shrink the
# data area to illegibility, OMIT the legend from the figure and state the series in prose (the
# prompt reply or the report caption) so the user adds it in PowerPoint/Word.
def legend_outside(ax, side="right", **kw):
    """Place `ax`'s legend just outside the axes so it never overlaps data (GATE 2).

    side="right" -> column to the right of the axes; side="top" -> row above it. Extra keyword
    args pass straight to `ax.legend` (e.g. `ncol=3`, `title=...`).
    """
    anchors = {"right": dict(loc="upper left", bbox_to_anchor=(1.02, 1.0)),
               "top": dict(loc="lower center", bbox_to_anchor=(0.5, 1.02))}
    opts = dict(anchors.get(side, anchors["right"]), borderaxespad=0.0)
    opts.update(kw)
    return ax.legend(**opts)


# --- Colormaps ---------------------------------------------------------------
# Diverging maps for quantities that run high <-> low. Two are ColorBrewer built-ins; the
# green-grey-purple one is built here so its MIDPOINT is light grey (not white), as specified.
# Default orientation: red is the HIGH end. Use diverging(name, reverse=True) to invert (red low).
# Center the norm at the meaningful midpoint (matplotlib.colors.TwoSlopeNorm(vcenter=0)) so the
# neutral colour lands on it.
_GREEN_GREY_PURPLE = LinearSegmentedColormap.from_list(
    "GreenGreyPurple", ["#762a83", "#d9d9d9", "#1b7837"]  # low purple -> grey -> high green
)
DIVERGING = {
    "red-yellow-blue": mpl.colormaps["RdYlBu_r"],   # low blue -> yellow -> high red
    "red-white-blue": mpl.colormaps["RdBu_r"],      # low blue -> white -> high red
    "green-grey-purple": _GREEN_GREY_PURPLE,        # low purple -> light grey -> high green
}


def diverging(name, reverse=False):
    """Return an approved diverging colormap; `reverse=True` flips it (e.g. red = low)."""
    cmap = DIVERGING[name]
    return cmap.reversed() if reverse else cmap


def sequential_to_white(color, name="seq"):
    """White -> `color` single-hue sequential map.

    Use for different values *within one category* (one variable, one condition): the hue
    identifies the category, the white->saturated ramp encodes magnitude. `color` is any
    matplotlib colour (hex like "#4878D0" or a name).
    """
    return LinearSegmentedColormap.from_list(name, ["#ffffff", color])


# Calm, modern qualitative palettes for distinct categories with NO high/low ordering and NO
# within-category gradient. Two saturations of the same idea:
#   PASTEL — soft tones for FILLED areas (bars, scatter fills, swatches), where a large coloured
#            region at full pastel still reads clearly.
#   MUTED  — deeper companions for THIN STROKES (line plots), because pastels wash out on 1-2 px
#            lines. Same modern feel, more saturation so a stroke stays visible.
PASTEL = [
    "#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF",
    "#DEBB9B", "#FAB0E4", "#CFCFCF", "#FFFEA3", "#B9F2F0",
]
MUTED = [
    "#4878D0", "#EE854A", "#6ACC64", "#D65F5F", "#956CB4",
    "#8C613C", "#DC7EC0", "#797979", "#D5BB67", "#82C6E2",
]
