import pandas as pd

df = pd.read_csv('all_models_impossible_corrected.csv')
hits = df[df['is_correct']]

print(f"Total impossible hits: {len(hits)} / {len(df)}")
print(f"Unique (problem_idx, variant) pairs hit: {len(hits.groupby(['problem_idx','variant']))}")
print()

print("Hits per (problem_idx, variant):")
for (pi, v), g in hits.groupby(['problem_idx', 'variant']):
    models = sorted(g['model'].unique())
    answer = g['original_answer'].iloc[0]
    preds = g['predicted_answer'].unique()
    print(f"  Problem {pi:2d} {v:20s} | answer={str(answer):>8s} | {len(g)} hits from {len(models)} models: {models}")

print()
print("Most common original answers among hits:")
print(hits['original_answer'].value_counts().head(15))

print()
print("Are answers small/common numbers?")
for ans, cnt in hits['original_answer'].value_counts().head(10).items():
    print(f"  answer={ans} -> {cnt} hits")

print()
print("Check a few hit responses - are models actually solving or guessing?")
for _, r in hits.head(5).iterrows():
    resp = str(r['full_response'])[:300]
    print(f"\n--- {r['model']} | Problem {r['problem_idx']} | {r['variant']} ---")
    print(f"Original answer: {r['original_answer']}, Predicted: {r['predicted_answer']}")
    print(f"Response preview: {resp}")

print()
print("Compare: how many unique predicted_answer values exist for impossible variants?")
imp_preds = df['predicted_answer'].dropna()
print(f"  Unique predictions: {imp_preds.nunique()}")
print(f"  NaN predictions: {df['predicted_answer'].isna().sum()}")
print(f"  Total impossible rows: {len(df)}")

print()
print("Sanity check: are the 'problems' actually modified (impossible)?")
for pi in hits['problem_idx'].unique()[:3]:
    orig_text = df[(df['problem_idx'] == pi)]['problem_text'].iloc[0]
    print(f"\nProblem {pi} text (first 200 chars): {orig_text[:200]}")
