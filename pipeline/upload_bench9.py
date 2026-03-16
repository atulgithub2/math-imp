#!/usr/bin/env python3
"""
Upload thulthula/math-imp-bench9 with:
- MATH split: 52 problems from math-examples, with checklist-verified updates
- AIME24 split: preserved from math-imp-bench8
- AIME25 split: preserved from math-imp-bench8
"""

import json
import os
from pathlib import Path
from datasets import Dataset, DatasetDict, load_dataset

# === VARIANT STATUS FROM CHECKLIST ===
# 13 STRONG from rerun (use new modified_problem from results_math_rerun/)
STRONG_RERUN = {
    (6, "edge"),  (6, "node"),
    (11, "edge"), (11, "node"),
    (21, "node"),
    (22, "node"),
    (26, "node"),
    (28, "edge"),
    (30, "edge"),
    (35, "node"),
    (38, "edge"), (38, "node"),
    (40, "node"),
}

# 14 to DROP (set to empty)
DROP_VARIANTS = {
    (5, "edge"),
    (14, "edge"),
    (15, "edge"), (15, "node"),
    (21, "edge"),
    (22, "edge"),
    (25, "edge"), (25, "node"),
    (35, "edge"),
    (39, "edge"), (39, "node"),
    (45, "edge"),
    (47, "edge"), (47, "node"),
}

RERUN_DIR = Path("results_math_rerun")


def load_rerun_text(pidx, variant_type):
    """Load the modified_problem text from rerun results."""
    fname = f"p{pidx}_{variant_type}_deletion.json"
    fpath = RERUN_DIR / fname
    if not fpath.exists():
        raise FileNotFoundError(f"Missing rerun result: {fpath}")
    with open(fpath) as f:
        data = json.load(f)
    return data["modified_problem"]


def build_math_split():
    """Build MATH split from math-examples with checklist updates applied."""
    ds = load_dataset("thulthula/math-examples")["train"]
    print(f"Loaded math-examples: {len(ds)} rows")

    rows = []
    changes_log = []

    for idx in range(len(ds)):
        row = dict(ds[idx])

        # Node deletion
        if (idx, "node") in STRONG_RERUN:
            old_q = row["node_deletion_question"][:60]
            row["node_deletion_question"] = load_rerun_text(idx, "node")
            row["node_deletion_dag"] = ""  # DAG changed, clear it
            changes_log.append(f"p{idx} node: UPDATED (rerun STRONG)")
        elif (idx, "node") in DROP_VARIANTS:
            row["node_deletion_question"] = ""
            row["node_deletion_dag"] = ""
            changes_log.append(f"p{idx} node: DROPPED")

        # Edge deletion
        if (idx, "edge") in STRONG_RERUN:
            old_q = row["edge_deletion_question"][:60]
            row["edge_deletion_question"] = load_rerun_text(idx, "edge")
            row["edge_deletion_dag"] = ""
            changes_log.append(f"p{idx} edge: UPDATED (rerun STRONG)")
        elif (idx, "edge") in DROP_VARIANTS:
            row["edge_deletion_question"] = ""
            row["edge_deletion_dag"] = ""
            changes_log.append(f"p{idx} edge: DROPPED")

        # Update success flag: True only if BOTH variants present
        has_node = bool(row["node_deletion_question"])
        has_edge = bool(row["edge_deletion_question"])
        row["success"] = has_node and has_edge

        rows.append(row)

    # Print changes
    print(f"\n=== CHANGES LOG ({len(changes_log)} changes) ===")
    for c in changes_log:
        print(f"  {c}")

    # Stats
    both = sum(1 for r in rows if r["success"])
    node_only = sum(1 for r in rows if r["node_deletion_question"] and not r["edge_deletion_question"])
    edge_only = sum(1 for r in rows if r["edge_deletion_question"] and not r["node_deletion_question"])
    neither = sum(1 for r in rows if not r["node_deletion_question"] and not r["edge_deletion_question"])
    print(f"\nFinal MATH split stats:")
    print(f"  Both variants: {both}")
    print(f"  Node only: {node_only}")
    print(f"  Edge only: {edge_only}")
    print(f"  Neither (keep for original_question): {neither}")
    print(f"  Total node variants: {sum(1 for r in rows if r['node_deletion_question'])}")
    print(f"  Total edge variants: {sum(1 for r in rows if r['edge_deletion_question'])}")

    # Build dataset
    dataset_dict = {k: [] for k in rows[0].keys()}
    for row in rows:
        for k, v in row.items():
            dataset_dict[k].append(v)

    return Dataset.from_dict(dataset_dict), changes_log


def main():
    # Build MATH split
    math_ds, changes_log = build_math_split()

    # Load existing AIME splits from bench8
    print("\nLoading AIME splits from thulthula/math-imp-bench8...")
    bench8 = load_dataset("thulthula/math-imp-bench8")
    aime24 = bench8["AIME24"]
    aime25 = bench8["AIME25"]
    print(f"  AIME24: {len(aime24)} rows")
    print(f"  AIME25: {len(aime25)} rows")

    # Rename MATH columns to match AIME format for unified schema
    math_ds = math_ds.rename_columns({
        "original_question": "original_problem",
        "node_deletion_question": "variation_1_node_deletion_problem",
        "node_deletion_dag": "variation_1_node_deletion_dag",
        "edge_deletion_question": "variation_2_edge_deletion_problem",
        "edge_deletion_dag": "variation_2_edge_deletion_dag",
    })
    # Add original_dag column (empty for MATH) and drop id/success to match AIME schema
    math_ds = math_ds.map(lambda x: {"original_dag": ""})
    # Keep only the columns that match AIME format + extra MATH columns
    # Actually, let's keep id and success as extra columns and see if HF allows it
    # No - HF requires same features. Add id/success to AIME splits instead, or remove from MATH.
    # Simplest: remove id/success from MATH, add original_dag
    math_ds = math_ds.remove_columns(["id", "success"])
    # Reorder to match AIME
    math_ds = math_ds.select_columns([
        "original_problem", "original_answer", "original_dag",
        "variation_1_node_deletion_problem", "variation_1_node_deletion_dag",
        "variation_2_edge_deletion_problem", "variation_2_edge_deletion_dag",
    ])

    repo_id = "thulthula/math-imp-bench9"
    token = os.getenv("HF_TOKEN")

    print(f"\n=== Uploading to {repo_id} ===")
    print(f"  MATH: {len(math_ds)} rows, cols: {math_ds.column_names}")
    print(f"  AIME24: {len(aime24)} rows, cols: {aime24.column_names}")
    print(f"  AIME25: {len(aime25)} rows, cols: {aime25.column_names}")

    from datasets import DatasetDict
    ds_dict = DatasetDict({
        "MATH": math_ds,
        "AIME24": aime24,
        "AIME25": aime25,
    })
    ds_dict.push_to_hub(repo_id, token=token, private=False)
    print(f"\nSuccessfully uploaded to https://huggingface.co/datasets/{repo_id}")

    # Write documentation
    doc = []
    doc.append("# math-imp-bench9 MATH Split Changes")
    doc.append("")
    doc.append("## Overview")
    doc.append("After running the question quality checklist on all 52 MATH Level 5 problems,")
    doc.append("27 variants were flagged as non-STRONG (WEAK_FILLABLE, BORDERLINE, or SOLVABLE).")
    doc.append("These were re-generated with checklist feedback injected into the generation prompt.")
    doc.append("After re-evaluation: 13 became STRONG (updated), 14 remained non-STRONG (dropped).")
    doc.append("")
    doc.append("## Variants Updated (13 - rerun produced STRONG deletion)")
    for c in changes_log:
        if "UPDATED" in c:
            doc.append(f"- {c}")
    doc.append("")
    doc.append("## Variants Dropped (14 - still non-STRONG after rerun)")
    for c in changes_log:
        if "DROPPED" in c:
            doc.append(f"- {c}")
    doc.append("")
    doc.append("## Problems Needing Re-evaluation on Models")
    doc.append("All 27 variants above need model re-evaluation since their text changed or was removed:")
    doc.append("")
    all_affected_problems = sorted(set(p for p, _ in STRONG_RERUN | DROP_VARIANTS))
    doc.append(f"Affected problem indices: {all_affected_problems}")
    doc.append("")
    doc.append("Specifically:")
    doc.append("- **13 updated variants**: Models need re-run since impossible question text changed")
    doc.append("- **14 dropped variants**: Remove these from any accuracy calculations")
    doc.append("")
    doc.append("## AIME24 and AIME25 splits")
    doc.append("Preserved unchanged from thulthula/math-imp-bench8.")
    doc.append("")

    doc_text = "\n".join(doc)
    with open("bench9_changes.md", "w") as f:
        f.write(doc_text)
    print(f"\nDocumentation written to bench9_changes.md")
    print(doc_text)


if __name__ == "__main__":
    main()
