"""
Plot frontier model (5-model) solve distribution and Pass@K/5 line graphs.
Two sets of plots: Base (math-imp-bench8) and AIME2026.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from collections import Counter
import os

models = ['kimi-k2.5', 'sonnet-4.6', 'sonnet-3.7', 'deepseek-v3.2', 'mistral-lg3']
model_labels = ['Kimi K2.5', 'Sonnet 4.6', 'Sonnet 3.7', 'DeepSeek V3.2', 'Mistral Large 3']
model_colors = ['#E91E63', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
model_markers = ['o', 's', '^', 'D', 'v']

os.makedirs('images', exist_ok=True)


def load_and_process(base_dir):
    dfs = {}
    for m in models:
        path = f"{base_dir}results_{m}.csv"
        df = pd.read_csv(path)
        df['is_solved'] = df.apply(
            lambda row: row['is_correct_exact'] if row['variant'] == 'original'
            else str(row['predicted_answer']).strip() == str(row['original_answer']).strip(),
            axis=1
        )
        dfs[m] = df

    model_run_counts = {}
    for m in models:
        df = dfs[m]
        counts = df.groupby(['split', 'problem_idx', 'variant'])['is_solved'].sum().reset_index()
        counts.columns = ['split', 'problem_idx', 'variant', 'correct_count']
        model_run_counts[m] = counts.set_index(['split', 'problem_idx', 'variant'])['correct_count']

    all_keys = set()
    for m in models:
        all_keys.update(model_run_counts[m].index)

    orig_keys = sorted([k for k in all_keys if k[2] == 'original'])
    node_keys = sorted([k for k in all_keys if k[2] == 'node_deletion'])
    edge_keys = sorted([k for k in all_keys if k[2] == 'edge_deletion'])
    imp_combined_keys = sorted(node_keys + edge_keys)
    base_problem_ids = sorted(set((s, pi) for (s, pi, v) in all_keys if v == 'original'))

    return model_run_counts, orig_keys, imp_combined_keys, base_problem_ids


def get_histogram(mc, model, keys):
    counts_list = [int(mc[model][k]) if k in mc[model].index else 0 for k in keys]
    hist = Counter(counts_list)
    return [hist.get(i, 0) for i in range(6)]


def get_unique_imp_histogram(mc, model, problem_ids):
    counts = mc[model]
    max_counts = []
    for (s, pi) in problem_ids:
        nc = int(counts.get((s, pi, 'node_deletion'), 0))
        ec = int(counts.get((s, pi, 'edge_deletion'), 0))
        max_counts.append(max(nc, ec))
    hist = Counter(max_counts)
    return [hist.get(i, 0) for i in range(6)]


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


def make_plots(mc, orig_keys, imp_combined_keys, base_problem_ids, dataset_name, suffix):
    n_orig = len(orig_keys)
    n_imp = len(imp_combined_keys)
    n_unique = len(base_problem_ids)

    variant_groups = [
        (f'Original (Base)\n{n_orig} problems', 'standard', orig_keys),
        (f'Unique IMP (Node OR Edge)\n{n_unique} problems', 'unique_imp', base_problem_ids),
        (f'Node + Edge Combined\n{n_imp} problems', 'standard', imp_combined_keys),
    ]

    model_str = ', '.join(model_labels)

    # ── PLOT 1: Grouped histogram ──
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    x = np.arange(5)
    n_models = len(models)
    bar_width = 0.15
    offsets = np.arange(n_models) - (n_models - 1) / 2

    for ax, (title, mode, keys) in zip(axes, variant_groups):
        for i, (m, label, color) in enumerate(zip(models, model_labels, model_colors)):
            if mode == 'standard':
                hist = get_histogram(mc, m, keys)
            else:
                hist = get_unique_imp_histogram(mc, m, keys)
            hist_no_zero = hist[1:]
            positions = x + offsets[i] * bar_width
            bars = ax.bar(positions, hist_no_zero, bar_width, label=label, color=color,
                          edgecolor='white', linewidth=0.5, zorder=3)
            for bar, val in zip(bars, hist_no_zero):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                            str(val), ha='center', va='bottom', fontsize=9, fontweight='bold')

        ax.set_xlabel('# Times Solved (out of 5 runs)', fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(['1/5', '2/5', '3/5', '4/5', '5/5'])
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, axis='y', alpha=0.2, linestyle='--')

    axes[0].set_ylabel('# Problems', fontsize=12)
    axes[1].legend(fontsize=9, loc='upper right', framealpha=0.9)

    fig.suptitle(f'{dataset_name} — Per-Model Solve Distribution (5 Runs)\n({model_str})',
                 fontsize=14, fontweight='bold', y=1.03)
    plt.tight_layout()
    path1 = f'images/frontier_5model_grouped_histogram_{suffix}.png'
    plt.savefig(path1, dpi=150, bbox_inches='tight')
    print(f"Saved: {path1}")
    plt.close('all')

    # ── PLOT 2: Pass@K/5 line graph ──
    threshold_labels = ['≥1/5', '≥2/5', '≥3/5', '≥4/5', '5/5']
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

    for ax, (title, mode, keys) in zip(axes, variant_groups):
        for i, (m, label, color, marker) in enumerate(zip(models, model_labels, model_colors, model_markers)):
            if mode == 'standard':
                curve = compute_passk_curve(mc, m, keys)
            else:
                curve = compute_unique_imp_passk(mc, m, keys)
            ax.plot(range(len(threshold_labels)), curve,
                    color=color, marker=marker, linewidth=2, markersize=7, label=label, zorder=3)

        ax.set_xticks(range(len(threshold_labels)))
        ax.set_xticklabels(threshold_labels, fontsize=10)
        ax.set_xlabel('Threshold (≥x correct out of 5)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    axes[0].set_ylabel('Fraction of Problems Solved', fontsize=12)
    axes[1].legend(fontsize=9, loc='upper right', framealpha=0.9)

    fig.suptitle(f'{dataset_name} — Pass@K/5 vs Threshold\n({model_str})',
                 fontsize=14, fontweight='bold', y=1.03)
    plt.tight_layout()
    path2 = f'images/frontier_5model_passk_line_{suffix}.png'
    plt.savefig(path2, dpi=150, bbox_inches='tight')
    print(f"Saved: {path2}")
    plt.close('all')


# ── Generate both sets of plots ──────────────────────────────────────────────

print("=" * 60)
print("BASE (math-imp-bench8)")
print("=" * 60)
mc, ok, ik, bp = load_and_process("run notebooks/results/frontier_models/")
make_plots(mc, ok, ik, bp, "Math-IMP Bench", "base")

print()
print("=" * 60)
print("AIME 2026")
print("=" * 60)
mc, ok, ik, bp = load_and_process("results/frontier_aime2026/")
make_plots(mc, ok, ik, bp, "AIME 2026", "aime2026")
