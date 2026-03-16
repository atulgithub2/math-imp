"""
Merge v1 (original) and v2 (regenerated) AIME2026 frontier results, then plot.

For the 13 affected (problem_idx, variant) pairs, replaces v1 rows with v2 rows.
Everything else (original variants + unaffected impossible variants) stays from v1.

Outputs:
  - results/frontier_aime2026_merged/results_{model}.csv   (per-model)
  - results/frontier_aime2026_merged/all_models_merged.csv  (combined)
  - images/frontier_5model_grouped_histogram_aime2026_v2.png
  - images/frontier_5model_passk_line_aime2026_v2.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from collections import Counter
from pathlib import Path
import os

# ── Affected (problem_idx, variant) pairs to replace ─────────────────────────
REPLACE_PAIRS = {
    (1, 'node_deletion'), (5, 'node_deletion'), (7, 'node_deletion'),
    (8, 'node_deletion'), (9, 'node_deletion'),
    (10, 'node_deletion'), (10, 'edge_deletion'),
    (18, 'node_deletion'), (18, 'edge_deletion'),
    (21, 'node_deletion'), (21, 'edge_deletion'),
    (23, 'node_deletion'), (23, 'edge_deletion'),
}

V1_DIR = Path("results/frontier_aime2026")
V2_DIR = Path("results/frontier_aime2026_v2")
MERGED_DIR = Path("results/frontier_aime2026_merged")
MERGED_DIR.mkdir(parents=True, exist_ok=True)

os.makedirs('images', exist_ok=True)

# ── Plot models (same 5 as plot_frontier_aime2026.py) ────────────────────────
plot_models = ['kimi-k2.5', 'sonnet-4.6', 'sonnet-3.7', 'deepseek-v3.2', 'mistral-lg3']
model_labels = ['Kimi K2.5', 'Sonnet 4.6', 'Sonnet 3.7', 'DeepSeek V3.2', 'Mistral Large 3']
model_colors = ['#E91E63', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0']
model_markers = ['o', 's', '^', 'D', 'v']

# All 11 models for full merged CSV
all_models = [
    'sonnet-3.7', 'deepseek-r1', 'deepseek-v3.2', 'kimi-k2.5', 'sonnet-4.6',
    'llama4-mav', 'nova-premier', 'mistral-lg3', 'gpt-5.2', 'grok-4.2', 'gemini3',
]


# =============================================================================
# MERGE
# =============================================================================

def merge_model(model_name):
    """Merge v1 and v2 CSVs for a single model.
    Drop v1 rows matching REPLACE_PAIRS, append v2 rows for those pairs.
    """
    v1_path = V1_DIR / f"results_{model_name}.csv"
    v2_path = V2_DIR / f"results_{model_name}.csv"

    if not v1_path.exists():
        print(f"  SKIP {model_name}: no v1 CSV")
        return None

    v1 = pd.read_csv(v1_path)

    # Drop affected rows from v1
    mask = v1.apply(
        lambda r: (r['problem_idx'], r['variant']) in REPLACE_PAIRS, axis=1
    )
    v1_kept = v1[~mask]
    dropped = mask.sum()

    # Append v2 rows
    if v2_path.exists():
        v2 = pd.read_csv(v2_path)
        merged = pd.concat([v1_kept, v2], ignore_index=True)
        added = len(v2)
    else:
        print(f"  WARNING {model_name}: no v2 CSV, keeping v1 only (affected rows dropped)")
        merged = v1_kept
        added = 0

    # Save
    out_path = MERGED_DIR / f"results_{model_name}.csv"
    merged.to_csv(out_path, index=False)
    print(f"  {model_name}: {len(v1)} v1 - {dropped} replaced + {added} v2 = {len(merged)} merged")
    return merged


print("=" * 60)
print("MERGING V1 + V2 RESULTS")
print("=" * 60)
print(f"Replacing {len(REPLACE_PAIRS)} (problem, variant) pairs per model\n")

all_merged = []
for m in all_models:
    df = merge_model(m)
    if df is not None:
        all_merged.append(df)

# Combined CSV
if all_merged:
    combined = pd.concat(all_merged, ignore_index=True)
    combined_path = MERGED_DIR / "all_models_merged.csv"
    combined.to_csv(combined_path, index=False)
    print(f"\nSaved combined: {combined_path} ({len(combined)} rows)")


# =============================================================================
# PLOT HELPERS (same logic as plot_frontier_aime2026.py)
# =============================================================================

def load_and_process(base_dir):
    dfs = {}
    for m in plot_models:
        path = f"{base_dir}/results_{m}.csv"
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
    n_models = len(plot_models)
    bar_width = 0.15
    offsets = np.arange(n_models) - (n_models - 1) / 2

    for ax, (title, mode, keys) in zip(axes, variant_groups):
        for i, (m, label, color) in enumerate(zip(plot_models, model_labels, model_colors)):
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
    threshold_labels = ['>=1/5', '>=2/5', '>=3/5', '>=4/5', '5/5']
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

    for ax, (title, mode, keys) in zip(axes, variant_groups):
        for i, (m, label, color, marker) in enumerate(zip(plot_models, model_labels, model_colors, model_markers)):
            if mode == 'standard':
                curve = compute_passk_curve(mc, m, keys)
            else:
                curve = compute_unique_imp_passk(mc, m, keys)
            ax.plot(range(len(threshold_labels)), curve,
                    color=color, marker=marker, linewidth=2, markersize=7, label=label, zorder=3)

        ax.set_xticks(range(len(threshold_labels)))
        ax.set_xticklabels(threshold_labels, fontsize=10)
        ax.set_xlabel('Threshold (>=x correct out of 5)', fontsize=11)
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


# =============================================================================
# COMPARISON TABLE: before vs after for affected questions
# =============================================================================

def print_comparison():
    """Print before/after solve rates for the 13 affected variants."""
    print(f"\n{'='*70}")
    print("BEFORE vs AFTER: Affected Impossible Variants")
    print(f"{'='*70}")

    for m in plot_models:
        v1_path = V1_DIR / f"results_{m}.csv"
        v2_path = V2_DIR / f"results_{m}.csv"
        if not v1_path.exists():
            continue

        v1 = pd.read_csv(v1_path)
        v1['is_solved'] = v1.apply(
            lambda r: str(r['predicted_answer']).strip() == str(r['original_answer']).strip()
            if r['variant'] != 'original' else r['is_correct_exact'],
            axis=1
        )

        # Filter to affected pairs
        v1_affected = v1[v1.apply(
            lambda r: (r['problem_idx'], r['variant']) in REPLACE_PAIRS, axis=1
        )]
        before_rate = v1_affected['is_solved'].mean() * 100 if len(v1_affected) > 0 else 0
        before_solved = int(v1_affected['is_solved'].sum())
        before_total = len(v1_affected)

        if v2_path.exists():
            v2 = pd.read_csv(v2_path)
            v2['is_solved'] = v2.apply(
                lambda r: str(r['predicted_answer']).strip() == str(r['original_answer']).strip(),
                axis=1
            )
            after_rate = v2['is_solved'].mean() * 100 if len(v2) > 0 else 0
            after_solved = int(v2['is_solved'].sum())
            after_total = len(v2)
        else:
            after_rate, after_solved, after_total = 0, 0, 0

        delta = after_rate - before_rate
        arrow = "v" if delta < 0 else ("^" if delta > 0 else "=")
        print(f"  {m:<18}  Before: {before_solved}/{before_total} ({before_rate:5.1f}%)  "
              f"After: {after_solved}/{after_total} ({after_rate:5.1f}%)  "
              f"[{arrow} {abs(delta):.1f}pp]")


# =============================================================================
# GENERATE PLOTS
# =============================================================================

print()
print("=" * 60)
print("AIME 2026 (v2 — with regenerated impossible variants)")
print("=" * 60)
mc, ok, ik, bp = load_and_process(str(MERGED_DIR))
make_plots(mc, ok, ik, bp, "AIME 2026 (v2)", "aime2026_v2")

print_comparison()
