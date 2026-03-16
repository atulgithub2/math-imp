#!/usr/bin/env python3
"""
Fix truncated questions in all_results_base.csv and all_results_var.csv
by fetching complete questions from the original datasets.
"""

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm

print("Loading datasets from Hugging Face...")
base_dataset = load_dataset('thulthula/math-bench')
var_dataset = load_dataset('thulthula/math-imp-bench8')

print("\n=== Fixing all_results_base.csv ===")
print("Loading CSV...")
df_base = pd.read_csv('all_results_base.csv')
print(f"Loaded {len(df_base)} rows")

# Create a mapping from (split, problem_idx) to full problem text
base_problem_map = {}
for split_name in ['AIME24', 'AIME25', 'MATH']:
    if split_name in base_dataset:
        split_data = base_dataset[split_name]
        for idx, item in enumerate(split_data):
            key = (split_name, idx)
            base_problem_map[key] = item['problem']

print(f"Created mapping with {len(base_problem_map)} base problems")

# Update the problem column with complete questions
updated_count = 0
for idx, row in tqdm(df_base.iterrows(), total=len(df_base), desc="Updating base problems"):
    split = row['split']
    problem_idx = row['problem_idx']
    key = (split, problem_idx)

    if key in base_problem_map:
        full_problem = base_problem_map[key]
        if df_base.at[idx, 'problem'] != full_problem:
            df_base.at[idx, 'problem'] = full_problem
            updated_count += 1

print(f"Updated {updated_count} truncated problems in base CSV")

# Save the updated CSV
print("Saving updated all_results_base.csv...")
df_base.to_csv('all_results_base.csv', index=False)
print("✓ Base CSV updated successfully!")

print("\n=== Fixing all_results_var.csv ===")
print("Loading CSV...")
df_var = pd.read_csv('all_results_var.csv')
print(f"Loaded {len(df_var)} rows")

# Create a mapping from (split, problem_idx, variation) to full problem text
var_problem_map = {}
for split_name in ['AIME24', 'AIME25']:
    if split_name in var_dataset:
        split_data = var_dataset[split_name]
        for idx, item in enumerate(split_data):
            # Map each variation type
            if 'variation_1_node_deletion_problem' in item:
                key = (split_name, idx, 'node_deletion_problem')
                var_problem_map[key] = item['variation_1_node_deletion_problem']

            if 'variation_2_edge_deletion_problem' in item:
                key = (split_name, idx, 'edge_deletion_problem')
                var_problem_map[key] = item['variation_2_edge_deletion_problem']

print(f"Created mapping with {len(var_problem_map)} variation problems")

# Update the problem column with complete questions
updated_count = 0
for idx, row in tqdm(df_var.iterrows(), total=len(df_var), desc="Updating variation problems"):
    split = row['split']
    problem_idx = row['problem_idx']
    variation = row['variation']
    key = (split, problem_idx, variation)

    if key in var_problem_map:
        full_problem = var_problem_map[key]
        if df_var.at[idx, 'problem'] != full_problem:
            df_var.at[idx, 'problem'] = full_problem
            updated_count += 1

print(f"Updated {updated_count} truncated problems in variation CSV")

# Save the updated CSV
print("Saving updated all_results_var.csv...")
df_var.to_csv('all_results_var.csv', index=False)
print("✓ Variation CSV updated successfully!")

print("\n=== Summary ===")
print("Both CSV files have been updated with complete questions.")
print("You can verify by checking the 'problem' column in each file.")
