import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

thresholds = [1, 3, 5, 10, 25]
threshold_labels = ["≥1/50", "≥3/50", "≥5/50", "≥10/50", "≥25/50"]

# --- BASE data: (label, [num/den per threshold]) ---
base_raw = [
    ("DeepSeek-Math-7B\n(AIME24)",    [(2,2),(2,2),(2,2),(0,2),(0,2)]),
    ("DeepSeek-Math-7B\n(AIME25)",    [(0,1),(0,1),(0,1),(0,1),(0,1)]),
    ("InternLM2-Math-7B\n(AIME24)",   [(0,1),(0,1),(0,1),(0,1),(0,1)]),
    ("InternLM2-Chat-7B\n(AIME25)",   [(0,1),(0,1),(0,1),(0,1),(0,1)]),
    ("Qwen2.5-7B-Inst\n(AIME24)",     [(7,7),(6,7),(6,7),(4,7),(3,7)]),
    ("Qwen2.5-7B-Inst\n(AIME25)",     [(5,6),(5,6),(5,6),(4,6),(1,6)]),
    ("Qwen2.5-Math-7B\n(AIME24)",     [(4,5),(4,5),(4,5),(4,5),(1,5)]),
    ("Qwen2.5-Math-7B\n(AIME25)",     [(7,9),(7,9),(5,9),(3,9),(2,9)]),
]

# --- VARIATIONS data ---
var_raw = [
    ("DeepSeek-Math-7B\n(AIME24)",        [(1,2),(1,2),(1,2),(0,2),(0,2)]),
    ("DeepSeek-Math-7B\n(AIME25)",        [(0,1),(0,1),(0,1),(0,1),(0,1)]),
    ("InternLM2-Math-7B\n(AIME24)",       [(0,1),(0,1),(0,1),(0,1),(0,1)]),
    ("InternLM2-Math-7B\n(AIME25)",       [(0,1),(0,1),(0,1),(0,1),(0,1)]),
    ("InternLM2-Chat-7B\n(AIME25)",       [(0,1),(0,1),(0,1),(0,1),(0,1)]),
    ("Qwen2.5-7B-Inst\n(AIME24)",         [(1,2),(1,2),(1,2),(1,2),(0,2)]),
    ("Qwen2.5-7B-Inst\n(AIME25)",         [(4,4),(3,4),(1,4),(1,4),(0,4)]),
    ("Qwen2.5-Math-7B-Inst\n(AIME24)",    [(3,6),(1,6),(1,6),(1,6),(0,6)]),
    ("Qwen2.5-Math-7B-Inst\n(AIME25)",    [(1,2),(1,2),(1,2),(1,2),(1,2)]),
]

def to_pct(pairs):
    return [n / d * 100 if d > 0 else 0.0 for n, d in pairs]

# Blue palette for base (bright, vivid blues)
blues = [
    "#1565c0", "#1e88e5", "#42a5f5", "#64b5f6",
    "#00b0ff", "#0091ea", "#0288d1", "#0277bd",
]
# Red/orange palette for variations (bright, vivid reds/oranges)
reds = [
    "#d50000", "#e53935", "#f4511e", "#ff7043",
    "#ff5722", "#ff6d00", "#ff9100", "#ff6e40", "#ff1744",
]

linestyles = ["-", "--", "-.", ":", (0,(3,1,1,1)), (0,(5,2)), (0,(1,1)), (0,(4,1,1,1,1,1))]
markers    = ["o", "s", "D", "^", "v", "P", "X", "*", "h"]

fig, ax = plt.subplots(figsize=(11, 6))
fig.patch.set_facecolor("#f8f9fb")
ax.set_facecolor("#f8f9fb")

# Plot base (blue)
for i, (label, pairs) in enumerate(base_raw):
    y = to_pct(pairs)
    ax.plot(thresholds, y,
            color=blues[i % len(blues)],
            linestyle=linestyles[i % len(linestyles)],
            marker=markers[i % len(markers)],
            linewidth=1.8, markersize=6,
            label=f"[Base] {label.replace(chr(10),' ')}")

# Plot variations (red)
for i, (label, pairs) in enumerate(var_raw):
    y = to_pct(pairs)
    ax.plot(thresholds, y,
            color=reds[i % len(reds)],
            linestyle=linestyles[i % len(linestyles)],
            marker=markers[i % len(markers)],
            linewidth=1.8, markersize=6, alpha=0.88,
            label=f"[Var] {label.replace(chr(10),' ')}")

# Axes styling
ax.set_xticks(thresholds)
ax.set_xticklabels(threshold_labels, fontsize=11)
ax.set_yticks(range(0, 101, 10))
ax.set_yticklabels([f"{v}%" for v in range(0, 101, 10)], fontsize=10)
ax.set_xlim(-0.5, 27)
ax.set_ylim(-3, 103)

ax.set_xlabel("Pass@k Threshold", fontsize=13, labelpad=8)
ax.set_ylabel("Problems Passing Threshold (%)", fontsize=13, labelpad=8)
ax.set_title("Base vs. Variations — Pass Rate Across Thresholds", fontsize=15, fontweight="bold", pad=14)

ax.grid(axis="y", linestyle="--", alpha=0.45, color="gray")
ax.grid(axis="x", linestyle=":", alpha=0.3, color="gray")
ax.spines[["top","right"]].set_visible(False)

# Legend: two proxy patches to explain color families, then the full legend
blue_patch = mpatches.Patch(color="#2171b5", label="Base (blue shades)")
red_patch  = mpatches.Patch(color="#cb181d", label="Variations (red shades)")

# Split legend into two columns with a small separator header
handles, labels = ax.get_legend_handles_labels()
leg = ax.legend(
    handles=[blue_patch, red_patch] + handles,
    labels=["Base (blue shades)", "Variations (red shades)"] + labels,
    loc="upper right",
    fontsize=7.8,
    framealpha=0.9,
    ncol=2,
    columnspacing=1,
    handlelength=2.2,
    borderpad=0.8,
)
leg.get_frame().set_edgecolor("#cccccc")

plt.tight_layout()
plt.savefig("threshold_comparison.png", dpi=150, bbox_inches="tight")
print("Saved: threshold_comparison.png")
plt.show()
