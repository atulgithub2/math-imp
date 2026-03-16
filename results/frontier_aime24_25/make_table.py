import pandas as pd
import numpy as np

df = pd.read_csv('all_models_full.csv')

# For impossible variants: correct if predicted_answer == original_answer
# For original: use is_correct_exact
df['correct'] = False

orig_mask = df['variant'] == 'original'
df.loc[orig_mask, 'correct'] = df.loc[orig_mask, 'is_correct_exact']

imp_mask = ~orig_mask
df.loc[imp_mask, 'correct'] = df.loc[imp_mask].apply(
    lambda r: str(r['predicted_answer']).strip() == str(r['original_answer']).strip(), axis=1
)

# Aggregate
results = []
for (model, split, variant), g in df.groupby(['model', 'split', 'variant']):
    total = len(g)
    correct = int(g['correct'].sum())
    errors = int(g['error'].notna().sum())
    acc = round(100 * correct / total, 1) if total > 0 else 0
    results.append({'model': model, 'split': split, 'variant': variant,
                    'correct': correct, 'total': total, 'accuracy': acc, 'errors': errors})

res = pd.DataFrame(results)

# Compute unique impossible: for each (model, split, problem_idx), solved if either node or edge is correct
imp_df_all = df[~orig_mask].copy()
unique_imp = imp_df_all.groupby(['model', 'split', 'problem_idx'])['correct'].any().reset_index()
unique_imp.columns = ['model', 'split', 'problem_idx', 'any_correct']

unique_imp_agg = unique_imp.groupby(['model', 'split']).agg(
    correct=('any_correct', 'sum'),
    total=('any_correct', 'count')
).reset_index()
unique_imp_agg['accuracy'] = round(100 * unique_imp_agg['correct'] / unique_imp_agg['total'], 1)

# Build markdown
lines = []
lines.append("# Frontier Model Evaluation Results\n")
lines.append("> Correctness for impossible variants (edge/node deletion) is determined by whether the model's predicted answer matches the **original problem's answer** (i.e., memorization signal).")
lines.append(">")
lines.append("> **Unique Imp.** = a problem is considered solved if *either* the node or edge deletion variant is solved.\n")

for split in ['AIME24', 'AIME25']:
    lines.append(f"## {split}\n")
    lines.append("| Model | Original | Node Deletion | Edge Deletion | Unique Imp. |")
    lines.append("|-------|----------|---------------|---------------|-------------|")

    s = res[res['split'] == split]
    ui_split = unique_imp_agg[unique_imp_agg['split'] == split]
    orig_rows = s[s['variant'] == 'original'].copy()
    orig_rows = orig_rows.merge(ui_split[['model', 'correct']].rename(columns={'correct': 'ui_correct'}), on='model', how='left')
    orig_rows['ui_correct'] = orig_rows['ui_correct'].fillna(0)
    orig_rows = orig_rows.sort_values(['ui_correct', 'accuracy'], ascending=[False, False])

    for _, row in orig_rows.iterrows():
        m = row['model']
        mr = s[s['model'] == m]

        def fmt(variant):
            v = mr[mr['variant'] == variant]
            if len(v) == 0:
                return "—"
            v = v.iloc[0]
            return f"{v['correct']}/{v['total']} ({v['accuracy']}%)"

        # Unique imp for this model+split
        ui = unique_imp_agg[(unique_imp_agg['model'] == m) & (unique_imp_agg['split'] == split)]
        if len(ui) > 0:
            ui = ui.iloc[0]
            ui_str = f"{int(ui['correct'])}/{int(ui['total'])} ({ui['accuracy']}%)"
        else:
            ui_str = "—"

        lines.append(f"| {m} | {fmt('original')} | {fmt('node_deletion')} | {fmt('edge_deletion')} | {ui_str} |")

    lines.append("")

# Combined table
lines.append("## Combined (AIME 2024 + 2025)\n")
lines.append("| Model | Original | Node Deletion | Edge Deletion | Unique Imp. |")
lines.append("|-------|----------|---------------|---------------|-------------|")

combined = res.groupby(['model', 'variant']).agg({'correct': 'sum', 'total': 'sum'}).reset_index()
combined['accuracy'] = round(100 * combined['correct'] / combined['total'], 1)

unique_imp_combined = unique_imp.groupby('model').agg(
    correct=('any_correct', 'sum'),
    total=('any_correct', 'count')
).reset_index()
unique_imp_combined['accuracy'] = round(100 * unique_imp_combined['correct'] / unique_imp_combined['total'], 1)

orig_combined = combined[combined['variant'] == 'original'].copy()
orig_combined = orig_combined.merge(unique_imp_combined[['model', 'correct']].rename(columns={'correct': 'ui_correct'}), on='model', how='left')
orig_combined['ui_correct'] = orig_combined['ui_correct'].fillna(0)
orig_combined = orig_combined.sort_values(['ui_correct', 'accuracy'], ascending=[False, False])
for _, row in orig_combined.iterrows():
    m = row['model']
    mr = combined[combined['model'] == m]

    def fmt(variant):
        v = mr[mr['variant'] == variant]
        if len(v) == 0:
            return "—"
        v = v.iloc[0]
        return f"{v['correct']}/{v['total']} ({v['accuracy']}%)"

    ui = unique_imp_combined[unique_imp_combined['model'] == m]
    if len(ui) > 0:
        ui = ui.iloc[0]
        ui_str = f"{int(ui['correct'])}/{int(ui['total'])} ({ui['accuracy']}%)"
    else:
        ui_str = "—"

    lines.append(f"| {m} | {fmt('original')} | {fmt('node_deletion')} | {fmt('edge_deletion')} | {ui_str} |")

lines.append("")

# List specific memorization hits
imp_df = df[imp_mask & df['correct']]
if len(imp_df) > 0:
    lines.append("## Memorization Hits (Impossible Variant Predicted == Original Answer)\n")
    lines.append("| Model | Split | Variant | Problem Idx | Original Answer | Predicted Answer |")
    lines.append("|-------|-------|---------|-------------|-----------------|------------------|")
    for _, r in imp_df.iterrows():
        lines.append(f"| {r['model']} | {r['split']} | {r['variant']} | {r['problem_idx']} | {r['original_answer']} | {r['predicted_answer']} |")
    lines.append("")
else:
    lines.append("## Memorization Hits\n")
    lines.append("**No memorization signal detected.** No frontier model predicted the original answer on any impossible variant.\n")

md = "\n".join(lines)

with open('summary_table.md', 'w') as f:
    f.write(md)

print("Saved summary_table.md")
print(f"\nTotal impossible variant matches: {len(imp_df)}")
if len(imp_df) > 0:
    print(imp_df[['model', 'split', 'variant', 'problem_idx', 'original_answer', 'predicted_answer']].to_string())
