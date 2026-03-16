"""
Plot frontier models Pass@K/5 vs Threshold for AIME 2024, 2025, 2026.
6 subplots: 2 rows (Base, Impossible) x 3 columns (AIME24, AIME25, AIME26).
Uses post-drop data.

Output: images/frontier_pass5_all_aime.pdf
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pathlib import Path

# ── Data sources ──
AIME24_25_CSV = Path("run notebooks/results/frontier_models/all_models_compact.csv")
AIME2026_DIR = Path("results_AIME2026_pass@5_1st inference/frontier_aime2026_merged")

# ── Drops ──
DROP_AIME25_EDGE = [0, 5, 28, 29]
DROP_AIME25_NODE = [29]
DROP_AIME2026_EDGE = [11, 21, 24, 26]
DROP_AIME2026_NODE = [7, 18, 25, 29]

# ── Plot config ──
plot_models = ['sonnet-4.6', 'kimi-k2.5', 'deepseek-v3.2', 'sonnet-3.7', 'mistral-lg3']
model_labels = ['Sonnet 4.6', 'Kimi K2.5', 'DeepSeek V3.2', 'Sonnet 3.7', 'Mistral Large 3']
model_colors = ['#2196F3', '#E91E63', '#FF9800', '#4CAF50', '#9C27B0']
model_markers = ['s', 'o', 'D', '^', 'v']


def load_aime24_25():
    df = pd.read_csv(AIME24_25_CSV)
    df = df[df['model'].isin(plot_models)]
    df['is_solved'] = df.apply(
        lambda r: r['is_correct_exact'] if r['variant'] == 'original'
        else str(r['predicted_answer']).strip() == str(r['original_answer']).strip(),
        axis=1
    )
    # Apply AIME25 drops
    df = df[~((df['split'] == 'AIME25') & (df['variant'] == 'edge_deletion') & (df['problem_idx'].isin(DROP_AIME25_EDGE)))]
    df = df[~((df['split'] == 'AIME25') & (df['variant'] == 'node_deletion') & (df['problem_idx'].isin(DROP_AIME25_NODE)))]
    return df


def load_aime2026():
    dfs = []
    for m in plot_models:
        path = AIME2026_DIR / f"results_{m}.csv"
        if path.exists():
            d = pd.read_csv(path)
            dfs.append(d)
    df = pd.concat(dfs, ignore_index=True)
    df = df[df['model'].isin(plot_models)]
    df['is_solved'] = df.apply(
        lambda r: r['is_correct_exact'] if r['variant'] == 'original'
        else str(r['predicted_answer']).strip() == str(r['original_answer']).strip(),
        axis=1
    )
    # Apply AIME2026 drops
    df = df[~((df['variant'] == 'edge_deletion') & (df['problem_idx'].isin(DROP_AIME2026_EDGE)))]
    df = df[~((df['variant'] == 'node_deletion') & (df['problem_idx'].isin(DROP_AIME2026_NODE)))]
    return df


def compute_run_counts(df, split=None):
    """For each (model, problem_idx, variant), count how many runs were correct."""
    if split:
        df = df[df['split'] == split]
    counts = df.groupby(['model', 'problem_idx', 'variant'])['is_solved'].sum().reset_index()
    counts.columns = ['model', 'problem_idx', 'variant', 'correct_count']
    return counts


def compute_passk_curve(counts, model, variant_filter, total_problems):
    """Compute fraction of problems solved at each threshold >=1/5 ... 5/5."""
    mc = counts[(counts['model'] == model)]
    if variant_filter == 'original':
        mc = mc[mc['variant'] == 'original']
        thresholds = [1, 2, 3, 4, 5]
        fracs = []
        for t in thresholds:
            solved = (mc['correct_count'] >= t).sum()
            fracs.append(solved / total_problems if total_problems > 0 else 0)
        return fracs
    else:
        # Unique: for each problem, take max(node, edge) correct count
        # A problem is "solved" at threshold t if max(node_count, edge_count) >= t
        node = mc[mc['variant'] == 'node_deletion'].set_index('problem_idx')['correct_count']
        edge = mc[mc['variant'] == 'edge_deletion'].set_index('problem_idx')['correct_count']
        all_pids = set(node.index) | set(edge.index)
        max_counts = [max(node.get(pid, 0), edge.get(pid, 0)) for pid in all_pids]
        thresholds = [1, 2, 3, 4, 5]
        fracs = []
        for t in thresholds:
            solved = sum(1 for c in max_counts if c >= t)
            fracs.append(solved / total_problems if total_problems > 0 else 0)
        return fracs


def get_total_problems(counts, variant_filter):
    """Get total unique problems for denominator."""
    if variant_filter == 'original':
        c = counts[counts['variant'] == 'original']
        for m in plot_models:
            n = len(c[c['model'] == m])
            if n > 0:
                return n
    else:
        # Unique problems: count distinct problem_idx that have node or edge
        for m in plot_models:
            mc = counts[(counts['model'] == m) & (counts['variant'].isin(['node_deletion', 'edge_deletion']))]
            n = mc['problem_idx'].nunique()
            if n > 0:
                return n
    return 0


# ── Load data ──
print("Loading AIME24+25...")
df_24_25 = load_aime24_25()
print("Loading AIME2026...")
df_2026 = load_aime2026()

# Split name for AIME2026 in merged CSV
aime2026_split = df_2026['split'].unique()
print(f"AIME2026 splits found: {aime2026_split}")

counts_24 = compute_run_counts(df_24_25, 'AIME24')
counts_25 = compute_run_counts(df_24_25, 'AIME25')
counts_26 = compute_run_counts(df_2026)

# ── Problem counts ──
splits_data = [
    ('AIME 2024', counts_24),
    ('AIME 2025', counts_25),
    ('AIME 2026', counts_26),
]

# ── Plot: 2 rows x 3 cols ──
threshold_labels = ['$\\geq$1/5', '$\\geq$2/5', '$\\geq$3/5', '$\\geq$4/5', '5/5']

plt.rcParams.update({'font.size': 18, 'axes.labelsize': 20, 'axes.titlesize': 22,
                      'xtick.labelsize': 17, 'ytick.labelsize': 17, 'legend.fontsize': 16})
fig, axes = plt.subplots(2, 3, figsize=(26, 14))

for col, (split_name, counts) in enumerate(splits_data):
    for row, (variant_filter, row_label) in enumerate([('original', 'Original (Base)'), ('impossible', 'Impossible (Unique)')]):
        ax = axes[row, col]
        n_problems = get_total_problems(counts, variant_filter)

        for i, (m, label, color, marker) in enumerate(zip(plot_models, model_labels, model_colors, model_markers)):
            model_total = get_total_problems(counts, variant_filter)
            if model_total == 0:
                continue

            curve = compute_passk_curve(counts, m, variant_filter, model_total)
            ax.plot(range(5), curve, color=color, marker=marker, linewidth=3,
                    markersize=11, label=label, zorder=3)

        ax.set_xticks(range(5))
        ax.set_xticklabels(threshold_labels, fontsize=17)
        ax.set_ylim(-0.05, 1.05)
        ax.set_yticks(np.arange(0, 1.1, 0.1))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x:.0%}'))
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylabel('Accuracy', fontsize=18)

        if row == 0:
            ax.set_title(f'{split_name}\n({n_problems} problems)', fontsize=17, fontweight='bold')
        if row == 1:
            ax.set_xlabel('Threshold (x correct out of 5)', fontsize=18)

# Add row labels on left margin (only once, outside the loop)
axes[0, 0].annotate('Original\n(Base)', xy=(-0.25, 0.5), xycoords='axes fraction',
                     fontsize=19, fontweight='bold', ha='center', va='center', rotation=90)
axes[1, 0].annotate('Impossible\n(Unique)', xy=(-0.25, 0.5), xycoords='axes fraction',
                     fontsize=19, fontweight='bold', ha='center', va='center', rotation=90)

# Single legend at top
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc='upper center', ncol=len(plot_models),
           fontsize=17, framealpha=0.9, bbox_to_anchor=(0.5, 0.99))

plt.tight_layout(rect=[0, 0, 1, 0.96])

out_path = 'paperWriting/images/frontier_pass5_all_aime.pdf'
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"\nSaved: {out_path}")
plt.close('all')
