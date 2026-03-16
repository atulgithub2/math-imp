"""
Recreate AIME 2026 Pass@K/5 line graph from merged v2 results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pathlib import Path

MERGED_DIR = Path("results/frontier_aime2026_merged")

plot_models = ['kimi-k2.5', 'sonnet-4.6', 'sonnet-3.7', 'deepseek-v3.2', 'mistral-lg3']
model_labels = ['Kimi K2.5', 'Sonnet 4.6', 'Sonnet 3.7', 'DeepSeek V3.2', 'Mistral Large 3']
model_colors = ['#E91E63', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
model_markers = ['o', 's', '^', 'D', 'v']


def load_data():
    dfs = {}
    for m in plot_models:
        path = MERGED_DIR / f"results_{m}.csv"
        df = pd.read_csv(path)
        df['is_solved'] = df.apply(
            lambda row: row['is_correct_exact'] if row['variant'] == 'original'
            else str(row['predicted_answer']).strip() == str(row['original_answer']).strip(),
            axis=1
        )
        dfs[m] = df

    model_run_counts = {}
    for m in plot_models:
        df = dfs[m]
        counts = df.groupby(['split', 'problem_idx', 'variant'])['is_solved'].sum().reset_index()
        counts.columns = ['split', 'problem_idx', 'variant', 'correct_count']
        model_run_counts[m] = counts.set_index(['split', 'problem_idx', 'variant'])['correct_count']

    all_keys = set()
    for m in plot_models:
        all_keys.update(model_run_counts[m].index)

    orig_keys = sorted([k for k in all_keys if k[2] == 'original'])
    node_keys = sorted([k for k in all_keys if k[2] == 'node_deletion'])
    edge_keys = sorted([k for k in all_keys if k[2] == 'edge_deletion'])
    imp_combined_keys = sorted(node_keys + edge_keys)
    base_problem_ids = sorted(set((s, pi) for (s, pi, v) in all_keys if v == 'original'))

    return model_run_counts, orig_keys, imp_combined_keys, base_problem_ids


def compute_passk_curve(mc, model, keys):
    counts = mc[model]
    total = len(keys)
    thresholds = [1, 2, 3, 4, 5]
    return [sum(1 for k in keys if k in counts.index and counts[k] >= t) / total for t in thresholds]


def compute_unique_imp_passk(mc, model, problem_ids):
    counts = mc[model]
    total = len(problem_ids)
    thresholds = [1, 2, 3, 4, 5]
    fracs = []
    for t in thresholds:
        solved = sum(1 for (s, pi) in problem_ids
                     if max(counts.get((s, pi, 'node_deletion'), 0),
                            counts.get((s, pi, 'edge_deletion'), 0)) >= t)
        fracs.append(solved / total)
    return fracs


mc, orig_keys, imp_combined_keys, base_problem_ids = load_data()

n_orig = len(orig_keys)
n_unique = len(base_problem_ids)
n_imp = len(imp_combined_keys)

variant_groups = [
    (f'Original (Base)\n{n_orig} problems', 'standard', orig_keys),
    (f'Unique IMP (Node OR Edge)\n{n_unique} problems', 'unique_imp', base_problem_ids),
    (f'Node + Edge Combined\n{n_imp} problems', 'standard', imp_combined_keys),
]

threshold_labels = ['>=1/5', '>=2/5', '>=3/5', '>=4/5', '5/5']
model_str = ', '.join(model_labels)

fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

for ax, (title, mode, keys) in zip(axes, variant_groups):
    for i, (m, label, color, marker) in enumerate(zip(plot_models, model_labels, model_colors, model_markers)):
        if mode == 'standard':
            curve = compute_passk_curve(mc, m, keys)
        else:
            curve = compute_unique_imp_passk(mc, m, keys)

        ax.plot(range(len(threshold_labels)), curve,
                color=color, marker=marker, linewidth=2.5, markersize=8, label=label, zorder=3)

        # Add value labels on each point
        for xi, yi in enumerate(curve):
            ax.annotate(f'{yi:.0%}', (xi, yi), textcoords="offset points",
                        xytext=(0, 10), ha='center', fontsize=7.5, color=color, fontweight='bold')

    ax.set_xticks(range(len(threshold_labels)))
    ax.set_xticklabels(threshold_labels, fontsize=10)
    ax.set_xlabel('Threshold (>=x correct out of 5)', fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_ylim(-0.05, 1.05)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

axes[0].set_ylabel('Fraction of Problems Solved', fontsize=12)
axes[1].legend(fontsize=9, loc='upper right', framealpha=0.9)

fig.suptitle(f'AIME 2026 (v2) — Pass@K/5 vs Threshold\n({model_str})',
             fontsize=14, fontweight='bold', y=1.03)
plt.tight_layout()
out = 'images/frontier_5model_passk_line_aime2026_v2.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"Saved: {out}")
plt.close('all')
