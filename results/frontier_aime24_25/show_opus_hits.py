import pandas as pd

df = pd.read_csv('all_models_full.csv')
opus = df[df['model'] == 'opus-4.6']
imp = opus[opus['variant'].isin(['edge_deletion', 'node_deletion'])].copy()
imp['match'] = imp.apply(
    lambda r: str(r['predicted_answer']).strip() == str(r['original_answer']).strip(), axis=1
)
hits = imp[imp['match']].sort_values(['split', 'problem_idx', 'variant'])

print(f"Opus 4.6 impossible variant hits: {len(hits)}\n")

lines = []
lines.append("# Opus 4.6 — Impossible Variant Memorization Hits\n")
lines.append(f"**Total hits:** {len(hits)} (unique problems: {hits['problem_idx'].nunique() + hits.groupby('split').ngroups - 1})\n")

for _, r in hits.iterrows():
    lines.append("---\n")
    lines.append(f"### {r['split']} Problem {r['problem_idx']} — {r['variant']}\n")
    lines.append(f"- **Original Answer:** {r['original_answer']}")
    lines.append(f"- **Predicted Answer:** {r['predicted_answer']}\n")
    lines.append(f"**Problem:**\n")
    lines.append(f"> {r['problem_text']}\n")
    lines.append(f"<details>")
    lines.append(f"<summary>Full Model Response</summary>\n")
    lines.append(f"```")
    lines.append(f"{r['full_response']}")
    lines.append(f"```\n")
    lines.append(f"</details>\n")

md = "\n".join(lines)
with open('opus_impossible_hits.md', 'w') as f:
    f.write(md)

print(f"Saved opus_impossible_hits.md")
