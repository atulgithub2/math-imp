import pandas as pd

df = pd.read_csv('all_models_merged.csv')

# Recompute is_correct: predicted_answer == original_answer for ALL variants
df['is_correct'] = df.apply(
    lambda r: str(r['predicted_answer']).strip() == str(r['original_answer']).strip()
    if pd.notna(r['predicted_answer']) else False,
    axis=1
)

# Select desired columns
out = df[['task_id', 'model', 'model_id', 'split', 'problem_idx', 'variant',
          'run_idx', 'problem_text', 'original_answer', 'predicted_answer',
          'is_correct', 'full_response']].copy()

out.to_csv('all_models_corrected.csv', index=False)

# Summary
print(f"Saved all_models_corrected.csv ({len(out)} rows)")
print(f"\nChanges from original is_correct_exact:")
changed = (df['is_correct'] != df['is_correct_exact'])
print(f"  Rows where correctness changed: {changed.sum()}")
print(f"\nPer-variant accuracy:")
for v in sorted(out['variant'].unique()):
    sub = out[out['variant'] == v]
    acc = sub['is_correct'].mean() * 100
    print(f"  {v}: {sub['is_correct'].sum()}/{len(sub)} ({acc:.1f}%)")

print(f"\nPer-model summary:")
for m in sorted(out['model'].unique()):
    sub = out[out['model'] == m]
    for v in ['original', 'node_deletion', 'edge_deletion']:
        sv = sub[sub['variant'] == v]
        if len(sv) > 0:
            print(f"  {m:20s} {v:20s}: {sv['is_correct'].sum():3d}/{len(sv)} ({sv['is_correct'].mean()*100:5.1f}%)")
