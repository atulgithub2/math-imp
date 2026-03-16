"""
Create final HuggingFace dataset with all corrected impossible variants.
Columns: original_problem, original_answer, original_dag,
         variation_1_node_deletion_problem, variation_1_node_deletion_dag,
         variation_2_edge_deletion_problem, variation_2_edge_deletion_dag
Splits: AIME24 (30), AIME25 (30), AIME2026 (30)
"""

import json
import os
from dotenv import load_dotenv
load_dotenv()
from datasets import load_dataset, Dataset, DatasetDict
from pathlib import Path

REGEN = Path("checklist/question_quality/regen_flagged")
AIME2026_DIR = Path("aime2026_sonnet_questions")

# ─── Load existing bench8 (AIME24 + AIME25) ───────────────────────────
print("Loading existing math-imp-bench8...")
bench8 = load_dataset("thulthula/math-imp-bench8")
aime24_rows = [dict(row) for row in bench8["AIME24"]]
aime25_rows = [dict(row) for row in bench8["AIME25"]]

print(f"  AIME24: {len(aime24_rows)} rows")
print(f"  AIME25: {len(aime25_rows)} rows")


# ─── Helper to read regen JSON and extract modified_problem ────────────
def read_regen(filepath):
    with open(filepath) as f:
        d = json.load(f)
    # Different files use different keys
    for key in ["new_modified_problem", "modified_problem"]:
        if key in d:
            return d[key]
    return None


# ─── AIME24: No changes needed (all 60 STRONG) ────────────────────────
print("\nAIME24: No changes needed (all STRONG)")


# ─── AIME25: Replace flagged variants ─────────────────────────────────
# Flagged questions and their STRONG replacements:
# p0 edge: AIME2025_p0_edge_deletion.json (removed tens digit 9 → d)
# p5 edge: DROPPED (inherently BORDERLINE) — keep original as placeholder but note it
# p28 edge: AIME2025_p28_edge_deletion.json (removed constant 9 → k)
# p29 edge: AIME2025_p29_both.json has edge variant (removed grid dimensions)
# p29 node: AIME2025_p29_node_v3.json (removed grid dimensions)

print("\nAIME25: Replacing flagged variants...")

# p0: replace edge_deletion
new_p0_edge = read_regen(REGEN / "AIME2025_p0_edge_deletion.json")
if new_p0_edge:
    aime25_rows[0]["variation_2_edge_deletion_problem"] = new_p0_edge
    aime25_rows[0]["variation_2_edge_deletion_dag"] = ""  # no DAG for regen
    print(f"  p0 edge: replaced")

# p5: DROPPED — mark as dropped but keep original problem text
# We'll set the edge_deletion to a note
print(f"  p5 edge: DROPPED (inherently BORDERLINE, keeping original as-is)")

# p28: replace edge_deletion
new_p28_edge = read_regen(REGEN / "AIME2025_p28_edge_deletion.json")
if new_p28_edge:
    aime25_rows[28]["variation_2_edge_deletion_problem"] = new_p28_edge
    aime25_rows[28]["variation_2_edge_deletion_dag"] = ""
    print(f"  p28 edge: replaced")

# p29 edge: from AIME2025_p29_both.json
with open(REGEN / "AIME2025_p29_both.json") as f:
    p29_both = json.load(f)
new_p29_edge = p29_both.get("edge_deletion", {}).get("modified_problem") or p29_both.get("edge_deletion", {}).get("new_modified_problem")
if new_p29_edge:
    aime25_rows[29]["variation_2_edge_deletion_problem"] = new_p29_edge
    aime25_rows[29]["variation_2_edge_deletion_dag"] = ""
    print(f"  p29 edge: replaced")

# p29 node: from AIME2025_p29_node_v3.json
new_p29_node = read_regen(REGEN / "AIME2025_p29_node_v3.json")
if new_p29_node:
    aime25_rows[29]["variation_1_node_deletion_problem"] = new_p29_node
    aime25_rows[29]["variation_1_node_deletion_dag"] = ""
    print(f"  p29 node: replaced")


# ─── AIME2026: Build from scratch ─────────────────────────────────────
print("\nAIME2026: Building from generation results...")

# Flagged AIME2026 questions and STRONG replacements:
# p7 node: AIME2026_p7_node_deletion.json
# p11 edge: AIME2026_p11_v3.json (removed entire D construction)
# p18 node: AIME2026_p18_node_deletion.json
# p21 edge: AIME2026_p21_v3.json (removed threshold "two")
# p24: entirely new (AIME2026_p24_node_deletion.json + AIME2026_p24_v3.json for edge)
# p26: node from regen, edge from dag.py
# p29: entirely new (AIME2026_p29_node_v2.json + AIME2026_p29_edge_deletion.json)

AIME2026_REGEN_MAP = {
    # (problem_idx, variant): regen_file
    (7, "node"): "AIME2026_p7_node_deletion.json",
    (11, "edge"): "AIME2026_p11_v3.json",
    (18, "node"): "AIME2026_p18_node_deletion.json",
    (21, "edge"): "AIME2026_p21_v3.json",
}

# Load AIME2026 source dataset for original problems
aime2026_src = load_dataset("thulthula/AIME2026", split="train")
print(f"  AIME2026 source: {len(aime2026_src)} problems")

aime2026_rows = []
for i in range(30):
    src = aime2026_src[i]
    original_problem = src["problem"]
    original_answer = str(src["final_answer"])

    # Try to load from generation results
    gen_file = AIME2026_DIR / f"problem_{i}.json"
    node_problem = ""
    edge_problem = ""
    original_dag = ""
    node_dag = ""
    edge_dag = ""

    if gen_file.exists():
        with open(gen_file) as f:
            gen = json.load(f)

        # Original DAG
        if isinstance(gen.get("dag"), dict):
            original_dag = json.dumps(gen["dag"])

        # Node deletion
        v1 = gen.get("variations", {}).get("variation_1_node_deletion", {})
        if v1.get("success"):
            node_problem = v1["result"].get("modified_problem", "")
            if isinstance(v1["result"].get("modified_dag"), dict):
                node_dag = json.dumps(v1["result"]["modified_dag"])

        # Edge deletion
        v2 = gen.get("variations", {}).get("variation_2_edge_deletion", {})
        if v2.get("success"):
            edge_problem = v2["result"].get("modified_problem", "")
            if isinstance(v2["result"].get("modified_dag"), dict):
                edge_dag = json.dumps(v2["result"]["modified_dag"])

    # Override with regen variants for flagged questions
    if (i, "node") in AIME2026_REGEN_MAP:
        regen = read_regen(REGEN / AIME2026_REGEN_MAP[(i, "node")])
        if regen:
            node_problem = regen
            node_dag = ""  # regen doesn't have DAG
            print(f"  p{i} node: replaced with regen")

    if (i, "edge") in AIME2026_REGEN_MAP:
        regen = read_regen(REGEN / AIME2026_REGEN_MAP[(i, "edge")])
        if regen:
            edge_problem = regen
            edge_dag = ""
            print(f"  p{i} edge: replaced with regen")

    # Handle p24, p26, p29 (entirely from regen)
    if i == 24:
        node_problem = read_regen(REGEN / "AIME2026_p24_node_deletion.json") or ""
        edge_problem = read_regen(REGEN / "AIME2026_p24_v3.json") or ""
        node_dag = ""
        edge_dag = ""
        print(f"  p24: both from regen")

    if i == 26:
        # node from regen, edge from dag.py (already loaded above if successful)
        regen_node = read_regen(REGEN / "AIME2026_p26_node_deletion.json")
        if regen_node:
            node_problem = regen_node
            node_dag = ""
        # edge: use dag.py version if it succeeded, otherwise regen
        if not edge_problem:
            edge_problem = read_regen(REGEN / "AIME2026_p26_edge_deletion_v2.json") or ""
            edge_dag = ""
        print(f"  p26: node from regen, edge from {'dag.py' if edge_dag else 'regen'}")

    if i == 29:
        # Use the STRONG variants: node=v2 (remove modulus), edge=remove cubic expression
        node_problem = read_regen(REGEN / "AIME2026_p29_node_v2.json") or ""
        edge_problem = read_regen(REGEN / "AIME2026_p29_edge_deletion.json") or ""
        node_dag = ""
        edge_dag = ""
        print(f"  p29: both from regen")

    row = {
        "original_problem": original_problem,
        "original_answer": original_answer,
        "original_dag": original_dag,
        "variation_1_node_deletion_problem": node_problem,
        "variation_1_node_deletion_dag": node_dag,
        "variation_2_edge_deletion_problem": edge_problem,
        "variation_2_edge_deletion_dag": edge_dag,
    }
    aime2026_rows.append(row)

    if not node_problem or not edge_problem:
        print(f"  WARNING p{i}: node={'OK' if node_problem else 'MISSING'}, edge={'OK' if edge_problem else 'MISSING'}")

# ─── Validate ──────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("VALIDATION")
print(f"{'='*60}")
for name, rows in [("AIME24", aime24_rows), ("AIME25", aime25_rows), ("AIME2026", aime2026_rows)]:
    total = len(rows)
    node_ok = sum(1 for r in rows if r["variation_1_node_deletion_problem"])
    edge_ok = sum(1 for r in rows if r["variation_2_edge_deletion_problem"])
    dag_ok = sum(1 for r in rows if r["original_dag"])
    print(f"  {name}: {total} problems, node={node_ok}/30, edge={edge_ok}/30, dag={dag_ok}/30")


# ─── Create and push dataset ──────────────────────────────────────────
print(f"\nCreating HuggingFace dataset...")

ds_dict = DatasetDict({
    "AIME24": Dataset.from_list(aime24_rows),
    "AIME25": Dataset.from_list(aime25_rows),
    "AIME2026": Dataset.from_list(aime2026_rows),
})

print(f"Dataset: {ds_dict}")
for split in ds_dict:
    print(f"  {split}: {len(ds_dict[split])} rows, columns={ds_dict[split].column_names}")

# Push to HuggingFace
HF_TOKEN = os.environ.get("HF_TOKEN")
REPO_ID = "thulthula/math-imp-bench9"

print(f"\nPushing to {REPO_ID}...")
ds_dict.push_to_hub(REPO_ID, token=HF_TOKEN)
print("Done!")
