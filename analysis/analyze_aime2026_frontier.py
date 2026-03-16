"""
Comprehensive pass@1 and pass@5 analysis for frontier models on AIME2026.

Data sources:
1. Main CSV: results_AIME2026_pass@5_1st inference/frontier_aime2026_merged/all_models_corrected.csv
   - Skip: gemini3, gpt-5.2, grok-4.2 (failed)
   - Bench8 drops applied for these models
2. GPT-5.4 (bench9, pass@1): MODEL_RUN#3/complete_run/results_gpt-5.4.csv filtered to AIME2026
3. Gemini-3.1-pro (bench9, impossible only): MODEL_RUN#3/scrapper_gemini/data/automate_results_AIME2026.json

Drops (bench8, main CSV):
  Edge: drop p11, p21, p24, p26  → denom = 25
  Node: drop p7, p18, p25, p29   → denom = 24
  Base: denom = 30 (no drops for original)

Wait - check: main CSV already has 27 problems for edge and node (p24,p26 absent for edge; p25,p29 absent for node)
The instruction says "drop p11, p21, p24, p26" for edge (bench8 models), so effective denom = 27 - 2 (already absent p24,p26) - 2 (p11,p21) = 23?
No - re-reading: "Edge: drop p11, p21, p24, p26 (/25)" means the denominator AFTER drops = 25.
Main CSV edge has 27 problems. We need to additionally drop p11 and p21 to get 25.
Similarly node: main CSV has 27 problems, drop p7 and p18 to get 24 (since p25, p29 already absent from bench8).
Wait - the instruction says "drop p7, p18, p25, p29 (/24)". Main CSV node has p25,p29 absent already (27 items).
So additionally drop p7 and p18: 27 - 2 = 25. But instruction says /24...
Let me recount: main CSV node: 27 problems (0-23, 25, 27, 28). Drop p7, p18 → 25 problems. Hmm, /24.
Actually instruction says node: "drop p7, p18, p25, p29 (/24)" from bench8 which had /28 (p25,p29 present).
So bench8 had 28 node problems (p24 absent only from full 30). Drop p7,p18,p25,p29 → 28-4=24.
But in the main CSV we have 27 node problems (p24,p29 absent). So we additionally drop p7,p18,p25 → 27-3=24. ✓

Let me recheck edge: bench8 had 28 edge problems (p11 absent? or all 30?).
Main CSV edge: 27 problems (p24,p26 absent). Instruction: "drop p11, p21, p24, p26 (/25)".
Bench8 had p24,p26 in it (they were dropped before bench9 regen). So bench8 edge = 28 (p11 absent? no...).
Actually bench8 = AIME24+AIME25 only. Wait - this is AIME2026 data.

Let me think clearly:
- Main CSV is bench8 data for AIME2026 (old problems, some absent because they failed generation)
- Main CSV has 27 edge problems: all 30 minus p24, p26 (which weren't generated)
- Additional bench8 drops for edge: p11, p21 (bad quality) → so denom = 27 - 2 = 25 ✓
- Main CSV has 27 node problems: all 30 minus p25, p29 (wait, also p24 absent)
  Actually main CSV node: 0-23, 25, 27, 28 = 27 problems (missing p24, p26? No: missing p24, p29)
  Wait let me check: node has 0-23,25,27,28 → missing p24,p26,p29? That's 27 items from 30.
  No: 0-23 = 24 items, plus 25,27,28 = 3 items = 27 total. Missing: 24,26,29.
  But instruction says node absent: p25,p29. Hmm, let me just recheck from the data.

Main CSV node missing: full set 0-29 (30) minus {24, 26, 29} = 27 problems? Let me verify.

Actually from earlier output: node_deletion: idx=[0..23, 25, 27, 28] - that's missing 24, 26, 29.
But instruction says "Node: drop p7, p18, p25, p29 (/24)". Since p29 is already absent, we drop p7,p18,p25 → 27-3=24. ✓
And for Gemini bench9 node absent: p25,p29. So bench9 node has 28 problems.
GPT-5.4 node: [0..23, 24, 26, 27, 28] = missing p25, p29 → 28 problems. ✓
"""

import pandas as pd
import numpy as np
import json
import re

BASE_DIR = '/home/shivank_g/projects/atul/math-imp'

# ==============================================================================
# Truncation detection
# ==============================================================================
def is_truncated(resp):
    """Response is truncated if it ends mid-word (last char is lowercase letter)
    or ends with an unclosed delimiter."""
    if pd.isna(resp):
        return False
    resp = str(resp).rstrip()
    if not resp:
        return True
    last_char = resp[-1]
    # Ends with lowercase letter = mid-word
    if last_char.islower():
        return True
    # Ends with opening brace/bracket
    if last_char in '{([':
        return True
    return False

def is_valid_run(resp):
    """A valid run has a non-null, non-truncated full_response."""
    if pd.isna(resp):
        return False
    return not is_truncated(resp)

# ==============================================================================
# Correctness: string comparison
# ==============================================================================
def is_correct(predicted, original):
    return str(predicted).strip() == str(original).strip()

# ==============================================================================
# Load main CSV (bench8 models, pass@5)
# ==============================================================================
print("Loading main CSV...")
df = pd.read_csv(f'{BASE_DIR}/results_AIME2026_pass@5_1st inference/frontier_aime2026_merged/all_models_corrected.csv')

# Skip failed models
skip_models = ['gemini3', 'gpt-5.2', 'grok-4.2']
df = df[~df['model'].isin(skip_models)].copy()

# Bench8 drops for AIME2026 (problems to exclude from scoring)
BENCH8_EDGE_DROPS = {11, 21}   # p24, p26 already absent in data
BENCH8_NODE_DROPS = {7, 18, 25}  # p24, p26, p29 already absent; drop p25 too (was p25,p29 in bench8 but p29 absent)

# Wait, let me reconsider the node drops more carefully.
# Instruction: "Node: drop p7, p18, p25, p29 (/24)"
# Main CSV node missing: 24, 26, 29 (already absent)
# So from present 27 node problems, additionally drop p7, p18, p25 → 27-3=24 ✓
BENCH8_NODE_DROPS = {7, 18, 25}

# Apply drops: filter out dropped problems
def apply_bench8_drops(sub_df):
    """Apply bench8 quality drops to the dataframe."""
    mask = pd.Series(True, index=sub_df.index)

    edge = sub_df['variant'] == 'edge_deletion'
    node = sub_df['variant'] == 'node_deletion'

    mask[edge & sub_df['problem_idx'].isin(BENCH8_EDGE_DROPS)] = False
    mask[node & sub_df['problem_idx'].isin(BENCH8_NODE_DROPS)] = False

    return sub_df[mask]

df = apply_bench8_drops(df)

# Expected denominators for bench8 models
BENCH8_DENOMS = {'original': 30, 'edge_deletion': 25, 'node_deletion': 24}

# Verify
for m in df['model'].unique():
    for v in ['original', 'edge_deletion', 'node_deletion']:
        sub = df[(df['model']==m) & (df['variant']==v)]
        n_probs = sub['problem_idx'].nunique()
        if n_probs != BENCH8_DENOMS[v]:
            print(f"WARNING: {m} {v} has {n_probs} problems, expected {BENCH8_DENOMS[v]}")

print(f"Main CSV loaded: {df['model'].unique().tolist()}")
print(f"Shape after drops: {df.shape}")

# Add validity and correctness columns
df['valid'] = df['full_response'].apply(is_valid_run)
df['correct'] = df.apply(lambda r: is_correct(r['predicted_answer'], r['original_answer']), axis=1)
# Only count correct if valid
df['correct_valid'] = df['valid'] & df['correct']

# ==============================================================================
# Load GPT-5.4 (bench9, pass@1, AIME2026 only)
# ==============================================================================
print("\nLoading GPT-5.4...")
df_gpt = pd.read_csv(f'{BASE_DIR}/MODEL_RUN#3/complete_run/results_gpt-5.4.csv')
df_gpt = df_gpt[df_gpt['split'] == 'AIME2026'].copy()

# Bench9 drops: NO regen drops. Only absent: edge p24,p26; node p25,p29
# GPT-5.4 edge has 28 problems (p24,p26 absent) → denom=28
# GPT-5.4 node has 28 problems (p25,p29 absent) → denom=28
# But wait, let me verify from actual data:
# edge: [0..23, 25, 27, 28, 29] = 28 problems (missing p24, p26) ✓
# node: [0..24, 26, 27, 28] = 28 problems (missing p25, p29) ✓
BENCH9_DENOMS = {'original': 30, 'edge_deletion': 28, 'node_deletion': 28}

df_gpt['valid'] = df_gpt['full_response'].apply(is_valid_run)
df_gpt['correct'] = df_gpt.apply(lambda r: is_correct(r['predicted_answer'], r['original_answer']), axis=1)
df_gpt['correct_valid'] = df_gpt['valid'] & df_gpt['correct']

# Verify GPT-5.4 problem counts
for v in ['original', 'edge_deletion', 'node_deletion']:
    sub = df_gpt[df_gpt['variant']==v]
    n_probs = sub['problem_idx'].nunique()
    expected = BENCH9_DENOMS[v]
    if n_probs != expected:
        print(f"GPT-5.4 {v}: {n_probs} problems (expected {expected})")
    else:
        print(f"GPT-5.4 {v}: {n_probs}/{expected} problems ✓")

# ==============================================================================
# Load Gemini-3.1-pro (bench9, impossible only, pass@1)
# ==============================================================================
print("\nLoading Gemini-3.1-pro...")
with open(f'{BASE_DIR}/MODEL_RUN#3/scrapper_gemini/data/automate_results_AIME2026.json') as f:
    gem_raw = json.load(f)

def extract_gemini_answer(content):
    """Extract predicted answer from Gemini clipboard content."""
    # Pattern 1: <answer>NUMBER</answer>
    m = re.findall(r'<answer>(.*?)</answer>', content)
    if m:
        for ans in reversed(m):
            if ans != '...':
                return ans.strip()
    # Pattern 2: </answer>NUMBER</answer> (reversed opening tag)
    m2 = re.findall(r'</answer>(\d+)</answer>', content)
    if m2:
        return m2[-1].strip()
    # Pattern 3: </answer>NUMBER at end
    m3 = re.findall(r'</answer>(\d+)', content)
    if m3:
        return m3[-1].strip()
    return None

# Parse Gemini data into rows
gem_rows = []
for d in gem_raw:
    item_id = d['id']
    # Parse: AIME2026pNedge or AIME2026pNnode
    m = re.match(r'AIME2026p(\d+)(edge|node)', item_id)
    if not m:
        print(f"Cannot parse ID: {item_id}")
        continue
    prob_idx = int(m.group(1))
    var_short = m.group(2)
    variant = 'edge_deletion' if var_short == 'edge' else 'node_deletion'

    original_answer = str(d['original_answer']).strip()
    content = d['clipboard_content']

    # Check if response is valid (not empty/truncated)
    # Gemini: if content is too short or no answer found
    predicted = extract_gemini_answer(content)
    valid = predicted is not None
    correct = valid and (str(predicted).strip() == original_answer)

    gem_rows.append({
        'model': 'gemini-3.1-pro',
        'problem_idx': prob_idx,
        'variant': variant,
        'original_answer': original_answer,
        'predicted_answer': predicted,
        'valid': valid,
        'correct': correct,
        'correct_valid': correct and valid,
        'run_idx': 0,
    })

df_gem = pd.DataFrame(gem_rows)

# Bench9 denoms for Gemini (impossible only)
# From IDs: edge problems present in gem_raw
gem_edge_probs = sorted(df_gem[df_gem['variant']=='edge_deletion']['problem_idx'].unique())
gem_node_probs = sorted(df_gem[df_gem['variant']=='node_deletion']['problem_idx'].unique())
print(f"Gemini edge problems: {gem_edge_probs}")
print(f"Gemini node problems: {gem_node_probs}")
print(f"Gemini edge count: {len(gem_edge_probs)}, node count: {len(gem_node_probs)}")

# ==============================================================================
# Analysis functions
# ==============================================================================

def fmt(correct, total):
    """Format as 'X/Y (Z%)'"""
    if total == 0:
        return "0/0 (N/A)"
    pct = 100.0 * correct / total
    return f"{correct}/{total} ({pct:.1f}%)"

def compute_pass1_stats(df_model, variant, denom, model_name=""):
    """
    Pass@1: first valid (non-null, non-truncated) run per problem.
    Returns: (n_correct, n_denom, n_truncated, n_errored)
    """
    sub = df_model[df_model['variant'] == variant].copy()

    # Count errored (null full_response) and truncated across ALL runs
    n_errored = sub[sub['full_response'].isna()].shape[0] if 'full_response' in sub.columns else 0
    n_truncated = sub[sub['full_response'].notna() & ~sub['valid']].shape[0] if 'full_response' in sub.columns else 0

    # For pass@1: pick first valid run per problem
    # Sort by run_idx, then take first valid for each problem
    sub_sorted = sub.sort_values('run_idx')

    # Get first valid run per problem
    valid_runs = sub_sorted[sub_sorted['valid']]
    first_valid = valid_runs.groupby('problem_idx').first().reset_index()

    n_correct = first_valid['correct_valid'].sum()
    # Denom is fixed (all problems in the variant, including those with no valid run)

    return int(n_correct), denom, int(n_truncated), int(n_errored)

def compute_pass5_stats(df_model, variant, denom):
    """
    Pass@5: any correct across all valid runs.
    Returns: (n_correct, n_denom)
    """
    sub = df_model[df_model['variant'] == variant].copy()
    valid_runs = sub[sub['valid']]

    # Any correct per problem
    correct_any = valid_runs.groupby('problem_idx')['correct_valid'].any()
    n_correct = correct_any.sum()

    return int(n_correct), denom

def compute_pass_k_of_5(df_model, variant, denom):
    """
    For x=1..5: problems correct >= x times out of 5 valid runs.
    Returns: dict {x: (n_correct, denom)}
    """
    sub = df_model[df_model['variant'] == variant].copy()
    valid_runs = sub[sub['valid']]

    correct_counts = valid_runs.groupby('problem_idx')['correct_valid'].sum()

    result = {}
    for x in range(1, 6):
        n_correct = (correct_counts >= x).sum()
        result[x] = (int(n_correct), denom)
    return result

# ==============================================================================
# Process all models
# ==============================================================================
VARIANTS = ['original', 'edge_deletion', 'node_deletion']
VARIANT_LABELS = {'original': 'Base', 'edge_deletion': 'Edge', 'node_deletion': 'Node'}

# Pass@5 models (from main CSV)
pass5_models = sorted(df['model'].unique().tolist())

print("\n" + "="*80)
print("TABLE 1: PASS@1 (first valid run per problem)")
print("="*80)

# Headers
print(f"\n{'Model':<20} {'Base /30':<18} {'Edge /25':<18} {'Node /24':<18} {'Trunc':<8} {'Error':<8}")
print("-"*90)

all_pass1_data = {}

for model in pass5_models:
    sub = df[df['model'] == model]
    row_data = {}
    total_trunc = 0
    total_error = 0

    cells = []
    for variant in VARIANTS:
        denom = BENCH8_DENOMS[variant]

        # Count errored/truncated for this variant
        vsub = sub[sub['variant'] == variant]

        if 'full_response' in vsub.columns:
            n_errored = vsub['full_response'].isna().sum()
            n_truncated = vsub[vsub['full_response'].notna() & ~vsub['valid']].shape[0]
        else:
            n_errored = 0
            n_truncated = 0

        total_trunc += n_truncated
        total_error += n_errored

        n_correct, denom_used, _, _ = compute_pass1_stats(sub, variant, denom)
        cells.append(fmt(n_correct, denom_used))
        row_data[variant] = (n_correct, denom_used)

    all_pass1_data[model] = row_data
    print(f"{model:<20} {cells[0]:<18} {cells[1]:<18} {cells[2]:<18} {total_trunc:<8} {total_error:<8}")

print("-"*90)

# GPT-5.4
print("\nGPT-5.4 (bench9, pass@1):")
gpt_cells = []
gpt_trunc = 0
gpt_error = 0
for variant in VARIANTS:
    denom = BENCH9_DENOMS[variant]
    vsub = df_gpt[df_gpt['variant'] == variant]
    n_errored = vsub['full_response'].isna().sum() if 'full_response' in vsub.columns else 0
    n_trunc = vsub[vsub['full_response'].notna() & ~vsub['valid']].shape[0] if 'full_response' in vsub.columns else 0
    gpt_trunc += n_trunc
    gpt_error += n_errored

    n_correct, _ = compute_pass5_stats(df_gpt, variant, denom)  # only run0 anyway
    # For pass@1 with single run, just count valid+correct
    valid_sub = vsub[vsub['valid']]
    n_correct_p1 = valid_sub['correct_valid'].sum()
    gpt_cells.append(fmt(int(n_correct_p1), denom))

print(f"{'gpt-5.4':<20} {gpt_cells[0]:<18} {gpt_cells[1]:<18} {gpt_cells[2]:<18} {gpt_trunc:<8} {gpt_error:<8}")

# Gemini-3.1-pro (impossible only)
gem_edge_denom = len(gem_edge_probs)
gem_node_denom = len(gem_node_probs)
print("\nGemini-3.1-pro (bench9, impossible only, pass@1):")
gem_edge_correct = df_gem[df_gem['variant']=='edge_deletion']['correct_valid'].sum()
gem_node_correct = df_gem[df_gem['variant']=='node_deletion']['correct_valid'].sum()
gem_no_answer = df_gem[~df_gem['valid']].shape[0]
print(f"{'gemini-3.1-pro':<20} {'N/A (no base)':<18} {fmt(int(gem_edge_correct), gem_edge_denom):<18} {fmt(int(gem_node_correct), gem_node_denom):<18} {gem_no_answer:<8} {'0':<8}")

print("\n" + "="*80)
print("TABLE 2: PASS@5 TOTAL (any correct across all 5 valid runs)")
print("="*80)
print(f"\n{'Model':<20} {'Base /30':<18} {'Edge /25':<18} {'Node /24':<18}")
print("-"*75)

for model in pass5_models:
    sub = df[df['model'] == model]
    cells = []
    for variant in VARIANTS:
        denom = BENCH8_DENOMS[variant]
        n_correct, denom_used = compute_pass5_stats(sub, variant, denom)
        cells.append(fmt(n_correct, denom_used))
    print(f"{model:<20} {cells[0]:<18} {cells[1]:<18} {cells[2]:<18}")

print("-"*75)
print("(GPT-5.4 and Gemini: pass@1 only — see Table 1)")

print("\n" + "="*80)
print("TABLE 3: PASS>=x/5 (problems correct >= x times out of 5 valid runs)")
print("="*80)

for variant in VARIANTS:
    denom = BENCH8_DENOMS[variant]
    label = VARIANT_LABELS[variant]
    print(f"\n--- {label} (denom={denom}) ---")
    print(f"{'Model':<20} {'>=1/5':<14} {'>=2/5':<14} {'>=3/5':<14} {'>=4/5':<14} {'>=5/5':<14}")
    print("-"*90)

    for model in pass5_models:
        sub = df[df['model'] == model]
        result = compute_pass_k_of_5(sub, variant, denom)
        cells = [fmt(result[x][0], result[x][1]) for x in range(1, 6)]
        print(f"{model:<20} {cells[0]:<14} {cells[1]:<14} {cells[2]:<14} {cells[3]:<14} {cells[4]:<14}")
    print("-"*90)

print("\n" + "="*80)
print("SUMMARY: TRUNCATION AND ERROR COUNTS (pass@5 models)")
print("="*80)
print(f"\n{'Model':<20} {'Total Truncated':<20} {'Total Errored':<20}")
print("-"*60)
for model in pass5_models:
    sub = df[df['model'] == model]
    if 'full_response' in sub.columns:
        n_errored = sub['full_response'].isna().sum()
        n_truncated = sub[sub['full_response'].notna() & ~sub['valid']].shape[0]
    else:
        n_errored = 0
        n_truncated = 0
    print(f"{model:<20} {n_truncated:<20} {n_errored:<20}")

print(f"\n{'gpt-5.4':<20} {gpt_trunc:<20} {gpt_error:<20}")
print(f"{'gemini-3.1-pro':<20} {gem_no_answer:<20} {'0':<20}")
