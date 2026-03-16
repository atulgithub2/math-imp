#!/usr/bin/env python3
"""
Build and upload thulthula/math-imp-bench9

Splits: AIME24, AIME25, AIME2026, MATH

Schema (unified):
  problem_number, original_problem, original_answer, original_dag,
  node_deletion_problem, node_deletion_dag,
  edge_deletion_problem, edge_deletion_dag

Sources:
- Problem texts: model_responses CSVs
- DAGs (AIME24/25): thulthula/math-imp-bench8
- DAGs (AIME2026): empty (not generated)
- DAGs (MATH): thulthula/math-examples
- Regen texts (15 AIME variants): regen_flagged/ JSONs
- Regen texts (27 MATH variants): results_math_rerun/ JSONs
"""

import json
import os
from pathlib import Path
import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset

REGEN_DIR = Path("checklist/question_quality/regen_flagged")
MATH_RERUN_DIR = Path("results_math_rerun")

# ── AIME REGEN MAP ──────────────────────────────────────────────────────────
# Maps (split, problem_idx, variant) -> (file, field_path)
# Only STRONG regen variants are listed here. Others are DROPPED (empty).

def load_regen_text(fname, *keys):
    """Load text from regen_flagged JSON, navigating nested keys."""
    d = json.load(open(REGEN_DIR / fname))
    for k in keys:
        d = d[k]
    return d

# STRONG regen variants to use instead of CSV text
AIME_REGEN_STRONG = {
    ("AIME25", 0,  "edge"): lambda: load_regen_text("AIME2025_p0_edge_deletion.json",  "new_modified_problem"),
    ("AIME25", 28, "edge"): lambda: load_regen_text("AIME2025_p28_edge_deletion.json", "new_modified_problem"),
    ("AIME25", 29, "edge"): lambda: load_regen_text("AIME2025_p29_both.json",          "edge_deletion", "new_modified_problem"),
    ("AIME25", 29, "node"): lambda: load_regen_text("AIME2025_p29_node_v3.json",       "new_modified_problem"),
    ("AIME26", 7,  "node"): lambda: load_regen_text("AIME2026_p7_node_deletion.json",  "new_modified_problem"),
    ("AIME26", 11, "edge"): lambda: load_regen_text("AIME2026_p11_v3.json",            "new_modified_problem"),
    ("AIME26", 18, "node"): lambda: load_regen_text("AIME2026_p18_node_deletion.json", "new_modified_problem"),
    ("AIME26", 21, "edge"): lambda: load_regen_text("AIME2026_p21_v3.json",            "new_modified_problem"),
    ("AIME26", 24, "node"): lambda: load_regen_text("AIME2026_p24_node_deletion.json", "modified_problem"),
    ("AIME26", 26, "node"): lambda: load_regen_text("AIME2026_p26_node_deletion.json", "modified_problem"),
    ("AIME26", 29, "edge"): lambda: load_regen_text("AIME2026_p29_edge_deletion.json", "modified_problem"),
}

# Non-STRONG variants (DROPPED = empty string)
AIME_DROPPED = {
    # AIME25 p5 edge is STRONG per checklist_analysis (CSV text is valid) — NOT dropped
    ("AIME26", 24, "edge"),  # regen BORDERLINE
    ("AIME26", 25, "node"),  # original SOLVABLE, no regen
    ("AIME26", 26, "edge"),  # regen SOLVABLE
    ("AIME26", 29, "node"),  # regen BORDERLINE
}
# NOTE: AIME25 p5 edge is STRONG per current checklist_analysis (CSV text is good) — NOT dropped

# ── MATH REGEN MAP ──────────────────────────────────────────────────────────
# 13 STRONG rerun variants (replace CSV/HF text with results_math_rerun/)
MATH_STRONG_RERUN = {
    (6,  "node"), (6,  "edge"),
    (11, "node"), (11, "edge"),
    (21, "node"),
    (22, "node"),
    (26, "node"),
    (28, "edge"),
    (30, "edge"),
    (35, "node"),
    (38, "node"), (38, "edge"),
    (40, "node"),
}

# 14 DROPPED variants
MATH_DROPPED = {
    (5,  "edge"),
    (14, "edge"),
    (15, "node"), (15, "edge"),
    (21, "edge"),
    (22, "edge"),
    (25, "node"), (25, "edge"),
    (35, "edge"),
    (39, "node"), (39, "edge"),
    (45, "edge"),
    (47, "node"), (47, "edge"),
}


def build_aime_split(split_label, csv_df, bench8_split=None, aime26_df=None, aime26_dag=None):
    """
    Build one AIME split.
    split_label: 'AIME24', 'AIME25', 'AIME26'
    csv_df: full model_responses CSV (filtered to right split)
    bench8_split: HF dataset split for DAGs (AIME24/25 only)
    aime26_df: AIME2026 CSV
    """
    rows = []
    n_problems = 30

    for pidx in range(n_problems):
        # Get original problem text + answer
        if split_label == "AIME26":
            df = aime26_df
            orig_rows = df[(df.problem_idx == pidx) & (df.variant == "original")]
        else:
            orig_rows = csv_df[(csv_df.problem_idx == pidx) & (csv_df.variant == "original")]

        if len(orig_rows) == 0:
            print(f"  WARNING: {split_label} p{pidx} original not found in CSV")
            continue

        orig_row = orig_rows.iloc[0]
        original_problem = orig_row["problem_text"]
        original_answer  = str(orig_row["original_answer"])

        # DAG sources
        if bench8_split is not None:
            original_dag = bench8_split[pidx]["original_dag"] or ""
        elif aime26_dag is not None and pidx in aime26_dag:
            original_dag = aime26_dag[pidx]["dag"] or ""
        else:
            original_dag = ""

        # ── Node deletion ──
        key_node = (split_label, pidx, "node")
        if key_node in AIME_DROPPED:
            node_problem = ""
            node_dag     = ""
        elif key_node in AIME_REGEN_STRONG:
            node_problem = AIME_REGEN_STRONG[key_node]()
            node_dag     = ""  # DAG not regenerated
        else:
            # Use CSV text
            if split_label == "AIME26":
                node_rows = aime26_df[(aime26_df.problem_idx == pidx) & (aime26_df.variant == "node_deletion")]
            else:
                node_rows = csv_df[(csv_df.problem_idx == pidx) & (csv_df.variant == "node_deletion")]

            if len(node_rows) == 0:
                node_problem = ""
                node_dag     = ""
            else:
                node_problem = node_rows.iloc[0]["problem_text"]
                if bench8_split:
                    node_dag = bench8_split[pidx]["variation_1_node_deletion_dag"] or ""
                elif aime26_dag and pidx in aime26_dag:
                    node_dag = aime26_dag[pidx]["dag_node"] or ""
                else:
                    node_dag = ""

        # ── Edge deletion ──
        key_edge = (split_label, pidx, "edge")
        if key_edge in AIME_DROPPED:
            edge_problem = ""
            edge_dag     = ""
        elif key_edge in AIME_REGEN_STRONG:
            edge_problem = AIME_REGEN_STRONG[key_edge]()
            edge_dag     = ""
        else:
            if split_label == "AIME26":
                edge_rows = aime26_df[(aime26_df.problem_idx == pidx) & (aime26_df.variant == "edge_deletion")]
            else:
                edge_rows = csv_df[(csv_df.problem_idx == pidx) & (csv_df.variant == "edge_deletion")]

            if len(edge_rows) == 0:
                edge_problem = ""
                edge_dag     = ""
            else:
                edge_problem = edge_rows.iloc[0]["problem_text"]
                if bench8_split:
                    edge_dag = bench8_split[pidx]["variation_2_edge_deletion_dag"] or ""
                elif aime26_dag and pidx in aime26_dag:
                    edge_dag = aime26_dag[pidx]["dag_edge"] or ""
                else:
                    edge_dag = ""

        rows.append({
            "problem_number":       pidx,
            "original_problem":     original_problem,
            "original_answer":      original_answer,
            "original_dag":         original_dag,
            "node_deletion_problem": node_problem,
            "node_deletion_dag":    node_dag,
            "edge_deletion_problem": edge_problem,
            "edge_deletion_dag":    edge_dag,
        })

    ds = Dataset.from_list(rows)
    node_count = sum(1 for r in rows if r["node_deletion_problem"])
    edge_count = sum(1 for r in rows if r["edge_deletion_problem"])
    print(f"  {split_label}: {len(rows)} problems, {node_count} node variants, {edge_count} edge variants")
    return ds


def build_math_split():
    """Build MATH split — only include problems with BOTH variants."""
    hf = load_dataset("thulthula/math-examples")["train"]
    print(f"Loaded math-examples: {len(hf)} rows")

    rows = []
    for idx in range(len(hf)):
        row = hf[idx]
        node_q   = row["node_deletion_question"] or ""
        node_dag = row["node_deletion_dag"] or ""
        edge_q   = row["edge_deletion_question"] or ""
        edge_dag = row["edge_deletion_dag"] or ""

        # Apply MATH rerun updates
        if (idx, "node") in MATH_STRONG_RERUN:
            d = json.load(open(MATH_RERUN_DIR / f"p{idx}_node_deletion.json"))
            node_q   = d["modified_problem"]
            node_dag = ""
        elif (idx, "node") in MATH_DROPPED:
            node_q   = ""
            node_dag = ""

        if (idx, "edge") in MATH_STRONG_RERUN:
            d = json.load(open(MATH_RERUN_DIR / f"p{idx}_edge_deletion.json"))
            edge_q   = d["modified_problem"]
            edge_dag = ""
        elif (idx, "edge") in MATH_DROPPED:
            edge_q   = ""
            edge_dag = ""

        # Only include if BOTH variants present
        if not node_q or not edge_q:
            continue

        rows.append({
            "problem_number":        idx,
            "original_problem":      row["original_question"],
            "original_answer":       str(row["original_answer"]),
            "original_dag":          "",
            "node_deletion_problem": node_q,
            "node_deletion_dag":     node_dag,
            "edge_deletion_problem": edge_q,
            "edge_deletion_dag":     edge_dag,
        })

    ds = Dataset.from_list(rows)
    print(f"  MATH: {len(rows)} problems with both variants (dropped {len(hf) - len(rows)})")
    return ds, rows


def build_rerun_doc(math_rows):
    """Create documentation file for which problems need model re-evaluation."""
    lines = []
    lines.append("# Problems Requiring Model Re-evaluation")
    lines.append("")
    lines.append("These problems had their impossible variants changed (regenerated or dropped)")
    lines.append("compared to the previous dataset. Models need to be re-run on these.")
    lines.append("")

    lines.append("## AIME2025 (4 updated + 1 dropped = 5 affected variants)")
    lines.append("")
    lines.append("| Problem | Variant | Change |")
    lines.append("|---------|---------|--------|")
    aime25_changes = [
        (0,  "edge", "REGENERATED (was WEAK_FILLABLE)"),
        (5,  "edge", "UPDATED (new STRONG deletion in checklist_analysis)"),
        (28, "edge", "REGENERATED (was BORDERLINE)"),
        (29, "edge", "REGENERATED (was BORDERLINE)"),
        (29, "node", "REGENERATED (was BORDERLINE)"),
    ]
    for pidx, var, change in aime25_changes:
        lines.append(f"| p{pidx} | {var}_deletion | {change} |")
    lines.append("")
    lines.append(f"Problem indices: {sorted(set(p for p,_,_ in aime25_changes))}")
    lines.append("")

    lines.append("## AIME2026 (7 updated + 4 dropped = 11 affected variants)")
    lines.append("")
    lines.append("| Problem | Variant | Change |")
    lines.append("|---------|---------|--------|")
    aime26_changes = [
        (7,  "node", "REGENERATED (was WEAK_FILLABLE)"),
        (11, "edge", "REGENERATED v3 (was BORDERLINE)"),
        (18, "node", "REGENERATED (was WEAK_FILLABLE)"),
        (21, "edge", "REGENERATED v3 (was BORDERLINE)"),
        (24, "node", "NEW (first generation, STRONG)"),
        (24, "edge", "DROPPED (regen BORDERLINE)"),
        (25, "node", "DROPPED (original SOLVABLE, no regen)"),
        (26, "node", "NEW (first generation, STRONG)"),
        (26, "edge", "DROPPED (regen SOLVABLE)"),
        (29, "edge", "NEW (first generation, STRONG)"),
        (29, "node", "DROPPED (regen BORDERLINE)"),
    ]
    for pidx, var, change in aime26_changes:
        lines.append(f"| p{pidx} | {var}_deletion | {change} |")
    lines.append("")
    lines.append(f"Problem indices: {sorted(set(p for p,_,_ in aime26_changes))}")
    lines.append("")

    lines.append("## MATH Level 5 (13 updated + 14 dropped = 27 affected variants)")
    lines.append("")
    lines.append("### Updated (REGENERATED — STRONG new deletion):")
    updated = sorted(MATH_STRONG_RERUN)
    lines.append(f"{updated}")
    lines.append("")
    lines.append("### Dropped (no STRONG deletion found):")
    dropped = sorted(MATH_DROPPED)
    lines.append(f"{dropped}")
    lines.append("")
    math_affected_idxs = sorted(set(p for p,_ in MATH_STRONG_RERUN | MATH_DROPPED))
    lines.append(f"Affected problem indices (in math-examples positional order): {math_affected_idxs}")
    lines.append("")
    math_problem_numbers = sorted(set(r["problem_number"] for r in math_rows
                                       if r["problem_number"] in math_affected_idxs))
    lines.append(f"Of these, still present in bench9 MATH split: {math_problem_numbers}")
    lines.append("")
    lines.append("## Summary")
    lines.append("- AIME24: no changes")
    lines.append("- AIME25: 5 variants changed (problems 0, 5, 28, 29)")
    lines.append("- AIME2026: 11 variants changed (problems 7, 11, 18, 21, 24, 25, 26, 29)")
    lines.append("- MATH: 27 variants changed (13 updated, 14 dropped)")

    return "\n".join(lines)


def main():
    token = os.getenv("HF_TOKEN")

    # ── Load CSVs ──
    print("Loading model response CSVs...")
    csv_aime = pd.read_csv("checklist/question_quality/model_responses/results_sonnet-4.6.csv")
    csv_aime24 = csv_aime[csv_aime.split == "AIME24"]
    csv_aime25 = csv_aime[csv_aime.split == "AIME25"]
    csv_aime26 = pd.read_csv("checklist/question_quality/model_responses/aime2026/results_sonnet-4.6.csv")

    # ── Load bench8 for DAGs ──
    print("Loading bench8 DAGs...")
    bench8 = load_dataset("thulthula/math-imp-bench8")
    aime2026_imp = load_dataset("thulthula/AIME2026-imp")["train"]
    # Build lookup: problem_idx (0-based) -> row
    aime2026_dag_lookup = {row["number"] - 1: row for row in aime2026_imp}

    # ── Build splits ──
    print("\nBuilding AIME24...")
    ds_aime24 = build_aime_split("AIME24", csv_aime24, bench8["AIME24"])

    print("Building AIME25...")
    ds_aime25 = build_aime_split("AIME25", csv_aime25, bench8["AIME25"])

    print("Building AIME2026...")
    ds_aime26 = build_aime_split("AIME26", None, None, csv_aime26, aime2026_dag_lookup)

    print("Building MATH...")
    ds_math, math_rows = build_math_split()

    # ── Build DatasetDict ──
    ds_dict = DatasetDict({
        "AIME24":  ds_aime24,
        "AIME25":  ds_aime25,
        "AIME2026": ds_aime26,
        "MATH":    ds_math,
    })

    print("\n=== Final dataset ===")
    for name, ds in ds_dict.items():
        print(f"  {name}: {len(ds)} problems, cols: {ds.column_names}")

    # ── Write rerun doc ──
    doc = build_rerun_doc(math_rows)
    with open("rerun_needed.md", "w") as f:
        f.write(doc)
    print("\nWrote rerun_needed.md")

    # ── Upload ──
    repo_id = "thulthula/math-imp-bench9"
    print(f"\nUploading to {repo_id}...")
    ds_dict.push_to_hub(repo_id, token=token, private=False)
    print(f"Done: https://huggingface.co/datasets/{repo_id}")


if __name__ == "__main__":
    main()
