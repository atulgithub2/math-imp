#!/usr/bin/env python3
"""
Regenerate impossible question variants that were solved by frontier models.

Seeds failure_history with specific feedback about WHY each variant was solvable,
then uses dag.py's pipeline to generate better variants.

Usage:
    python remake_impossible.py                    # Regenerate all affected variants
    python remake_impossible.py --model sonnet     # Use Sonnet (cheaper)
    python remake_impossible.py --problems 1,5     # Only specific problems
    python remake_impossible.py --dry-run          # Preview without running
    python remake_impossible.py --update-hf        # Update HF dataset after regeneration
"""

import json
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# AWS credentials loaded from .env via load_dotenv() above

# Import from dag.py
import dag
from dag import modify_to_unsolvable, verify_impossible_question, run_code

# Reinitialize bedrock_client with correct credentials (in case env vars were
# read before we set them above)
import boto3
from botocore.config import Config as BotoConfig

dag.bedrock_client = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1',
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    config=BotoConfig(
        read_timeout=300,
        connect_timeout=60,
        retries={'max_attempts': 3, 'mode': 'adaptive'}
    )
)


# =============================================================================
# FEEDBACK MAPPING: problem_idx → { method → feedback }
# =============================================================================

REMAKE_TARGETS = {
    1: {
        "variation_1_node_deletion": (
            "Deleted target sum but left example 42124. Model deduced sum=13 by "
            "adding digits of example. Remove the numerical example entirely, or "
            "replace with a generic placeholder that gives no information about the "
            "target sum."
        ),
    },
    5: {
        "variation_1_node_deletion": (
            "Wrote 'for some base b'. Model algebraically determined that the product "
            "was independent of b. Must remove more structural information — not just "
            "the base, but also enough algebraic structure that the answer can't be "
            "derived."
        ),
    },
    7: {
        "variation_1_node_deletion": (
            "Wrote 'leave a certain remainder upon division by 12'. Model guessed "
            "remainder=5 mod 12 from AIME knowledge/common patterns. Must remove or "
            "obscure the divisor (12) as well, or remove enough context that the "
            "remainder and divisor both become unknown."
        ),
    },
    8: {
        "variation_1_node_deletion": (
            "Model was able to solve this. The deletion did not remove enough critical "
            "information. Make the problem TRULY impossible by removing more key values "
            "or relationships that cannot be deduced from context."
        ),
    },
    9: {
        "variation_1_node_deletion": (
            "Wrote 'BC having some unspecified length'. Model inferred BC=14 because "
            "13-14-15 is a classic triangle in competition math. Must either remove "
            "additional side lengths or explicitly state a non-standard configuration "
            "that breaks the standard assumption."
        ),
    },
    10: {
        "variation_1_node_deletion": (
            "64 cells heavily implies 8x8 grid. Left exact LaTeX summation formula "
            "intact. Must remove grid size hints entirely (both 64 and 8x8 references) "
            "and obscure the summation bounds."
        ),
        "variation_2_edge_deletion": (
            "64 cells heavily implies 8x8 grid. Left exact LaTeX summation formula "
            "intact. Must remove grid size hints entirely (both 64 and 8x8 references) "
            "and obscure the summation bounds."
        ),
    },
    18: {
        "variation_1_node_deletion": (
            "Deleted base rule but left example f(72)=58. Model reverse-engineered "
            "base=8 from the example. Must delete the example equation f(72)=58 as "
            "well, or replace it with a generic statement."
        ),
        "variation_2_edge_deletion": (
            "Deleted base rule but left example f(72)=58. Model reverse-engineered "
            "base=8 from the example. Must delete the example equation f(72)=58 as "
            "well, or replace it with a generic statement."
        ),
    },
    21: {
        "variation_1_node_deletion": (
            "Model was able to solve this. The deletion did not remove enough critical "
            "information. Make the problem TRULY impossible by removing more key values "
            "or relationships that cannot be deduced from context."
        ),
        "variation_2_edge_deletion": (
            "Model was able to solve this. The deletion did not remove enough critical "
            "information. Make the problem TRULY impossible by removing more key values "
            "or relationships that cannot be deduced from context."
        ),
    },
    23: {
        "variation_1_node_deletion": (
            "Model was able to solve this. The deletion did not remove enough critical "
            "information. Make the problem TRULY impossible by removing more key values "
            "or relationships that cannot be deduced from context."
        ),
        "variation_2_edge_deletion": (
            "Model was able to solve this. The deletion did not remove enough critical "
            "information. Make the problem TRULY impossible by removing more key values "
            "or relationships that cannot be deduced from context."
        ),
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_failure_history(feedback: str) -> list:
    """Create a failure_history list seeded with user feedback.

    Formatted as a Phase 3 failure so modify_to_unsolvable() includes it
    in the prompt for the LLM to learn from.
    """
    return [{
        "attempt": 0,
        "failure_type": "phase3_llm_check",
        "similarity_score": 8,
        "target_similarity_score": 5,
        "impossibility_score": 3,
        "target_impossibility_score": 7,
        "failure_reason": "Impossibility too low: frontier model solved the problem",
        "similarity_explanation": "Problem was similar enough to original.",
        "impossibility_explanation": feedback,
        "solve_attempt": f"A frontier model solved this variant. Reason: {feedback}",
    }]


def regenerate_variant(problem_data: dict, method: str, feedback: str,
                       max_retries: int = 5) -> dict:
    """Regenerate a single variant for a problem with seeded feedback.

    Returns a dict with the same structure as dag.py's variation results.
    """
    question = problem_data["original_question"]
    solution = problem_data["original_solution"]
    code = problem_data["generated_code"]
    dag_data = problem_data["dag"]
    answer = problem_data["original_answer"]

    # Seed failure history with user feedback
    failure_history = make_failure_history(feedback)

    result = {
        "success": False,
        "attempts": 0,
        "all_attempts": [],
        "failure_history": list(failure_history),
    }

    for attempt in range(max_retries):
        result["attempts"] = attempt + 1
        print(f"      Attempt {attempt + 1}/{max_retries}...")

        # Generate modification
        modified = modify_to_unsolvable(
            question, solution, code, dag_data, method, result["failure_history"]
        )

        if "error" in modified:
            print(f"      Generation error: {modified.get('error', 'unknown')}")
            result["all_attempts"].append({
                "attempt": attempt + 1,
                "error": modified.get("error", "unknown")
            })
            continue

        # PHASE 2: Verify code errors
        modified_code = modified.get("modified_code", "")
        success, output = run_code(modified_code)

        modified["code_verification"] = {
            "code_errored": not success,
            "output": output[:500] if output else ""
        }

        if success:
            print(f"      ✗ Code ran without error (output: {output[:50]}), retrying...")
            result["all_attempts"].append({
                "attempt": attempt + 1,
                "phase": "code_verification",
                "code_ran_successfully": True,
                "output": output[:200]
            })
            result["failure_history"].append({
                "attempt": attempt + 1,
                "failure_type": "phase2_code_didnt_error",
                "failure_reason": "Code did not error when it should have",
                "output": output[:200],
            })
            continue

        # Code errored - good!
        print(f"      ✓ Code errored: {output[:80]}...")
        print(f"      Running Phase 3: Similarity + Impossibility check...")

        # PHASE 3: Verify similarity and impossibility
        modified_question = modified.get("modified_problem", "")
        verification = verify_impossible_question(
            question, modified_question, answer, result["failure_history"]
        )

        modified["phase3_verification"] = verification

        similarity_score = verification.get("similarity_score", 0)
        impossibility_score = verification.get("impossibility_score", 0)
        passes = verification.get("passes", False)

        print(f"        Similarity: {similarity_score}/10 (need >= 5)")
        print(f"        Impossibility: {impossibility_score}/10 (need >= 7)")

        if passes:
            print(f"      ✓✓ SUCCESS! Both checks passed!")
            result["success"] = True
            result["result"] = modified
            break
        else:
            failure_reason = []
            if similarity_score < 5:
                failure_reason.append(f"Similarity too low: {similarity_score}/10")
            if impossibility_score < 7:
                failure_reason.append(f"Impossibility too low: {impossibility_score}/10")

            print(f"      ✗ Phase 3 failed: {'; '.join(failure_reason)}")

            result["all_attempts"].append({
                "attempt": attempt + 1,
                "phase": "phase3_verification",
                "similarity_score": similarity_score,
                "impossibility_score": impossibility_score,
                "failure_reason": failure_reason
            })

            result["failure_history"].append({
                "attempt": attempt + 1,
                "failure_type": "phase3_llm_check",
                "similarity_score": similarity_score,
                "target_similarity_score": 5,
                "impossibility_score": impossibility_score,
                "target_impossibility_score": 7,
                "failure_reason": "; ".join(failure_reason),
                "similarity_explanation": verification.get("similarity_explanation", ""),
                "impossibility_explanation": verification.get("impossibility_explanation", ""),
                "solve_attempt": verification.get("solve_attempt", ""),
            })

    if not result["success"]:
        print(f"      ✗ Failed after {max_retries} attempts")

    return result


# =============================================================================
# HF DATASET UPDATE
# =============================================================================

def update_hf_dataset(output_dir: str, repo_id: str = "thulthula/AIME2026-imp"):
    """Update the existing HF dataset with regenerated variants.

    Only overwrites ques_node/dag_node/ques_edge/dag_edge for affected problems.
    """
    from datasets import load_dataset, Dataset

    print(f"\n{'='*70}")
    print(f"UPDATING HF DATASET: {repo_id}")
    print(f"{'='*70}")

    # Load existing dataset
    ds = load_dataset(repo_id, split="train")
    data = {col: list(ds[col]) for col in ds.column_names}
    print(f"Loaded {len(ds)} rows from {repo_id}")

    updated_count = 0

    for idx, variants_to_fix in sorted(REMAKE_TARGETS.items()):
        output_file = os.path.join(output_dir, f"problem_{idx}.json")
        if not os.path.exists(output_file):
            print(f"  ✗ Problem {idx}: no regenerated file found")
            continue

        with open(output_file, 'r') as f:
            regen_data = json.load(f)

        variations = regen_data.get("variations", {})

        for method in variants_to_fix:
            var_data = variations.get(method, {})
            if not var_data.get("success"):
                print(f"  ✗ Problem {idx} {method}: regeneration not successful")
                continue

            result = var_data.get("result", {})
            modified_question = result.get("modified_problem", "")
            modified_dag = result.get("modified_dag", None)
            dag_str = json.dumps(modified_dag) if modified_dag else ""

            if "node" in method:
                data["ques_node"][idx] = modified_question
                data["dag_node"][idx] = dag_str
                print(f"  ✓ Problem {idx}: updated ques_node + dag_node")
            elif "edge" in method:
                data["ques_edge"][idx] = modified_question
                data["dag_edge"][idx] = dag_str
                print(f"  ✓ Problem {idx}: updated ques_edge + dag_edge")

            updated_count += 1

    print(f"\nUpdated {updated_count} variant(s)")

    # Push updated dataset
    updated_ds = Dataset.from_dict(data)
    updated_ds.push_to_hub(repo_id, split="train", token=os.environ.get("HF_TOKEN"))
    print(f"✓ Pushed updated dataset to {repo_id}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Regenerate impossible question variants that were solved by frontier models"
    )
    parser.add_argument("--model", type=str, default="sonnet", choices=["sonnet", "opus"],
                        help="Model to use for regeneration (default: sonnet)")
    parser.add_argument("--input-dir", type=str, default="results_aime2026_sonnet",
                        help="Directory with original problem JSONs")
    parser.add_argument("--output-dir", type=str, default="results_aime2026_v2",
                        help="Output directory for regenerated variants")
    parser.add_argument("--max-retries", type=int, default=5,
                        help="Max retries per variant (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview targets without regenerating")
    parser.add_argument("--problems", type=str, default=None,
                        help="Comma-separated problem indices to process (default: all affected)")
    parser.add_argument("--update-hf", action="store_true",
                        help="Update HF dataset with regenerated variants (run after regeneration)")
    parser.add_argument("--hf-repo", type=str, default="thulthula/AIME2026-imp",
                        help="HF dataset repo ID (default: thulthula/AIME2026-imp)")
    parser.add_argument("--force", action="store_true",
                        help="Re-process even if variant already succeeded in output dir")
    args = parser.parse_args()

    # Handle --update-hf mode
    if args.update_hf:
        update_hf_dataset(args.output_dir, args.hf_repo)
        return

    # Set model
    MODEL_NAMES = {
        "sonnet": "us.anthropic.claude-sonnet-4-6",
        "opus": "us.anthropic.claude-opus-4-6-v1",
    }
    dag.MODEL_NAME = MODEL_NAMES[args.model]
    print(f"Using model: {args.model} ({dag.MODEL_NAME})")

    # Parse problem filter
    if args.problems:
        target_indices = [int(x) for x in args.problems.split(",")]
        targets = {idx: REMAKE_TARGETS[idx] for idx in target_indices
                   if idx in REMAKE_TARGETS}
    else:
        targets = REMAKE_TARGETS

    # Preview
    total_variants = sum(len(v) for v in targets.values())
    print(f"\n{'='*70}")
    print(f"REMAKE IMPOSSIBLE VARIANTS")
    print(f"{'='*70}")
    print(f"Input:   {args.input_dir}/")
    print(f"Output:  {args.output_dir}/")
    print(f"Targets: {len(targets)} problems, {total_variants} variants")
    print()

    for idx, variants in sorted(targets.items()):
        for method in variants:
            short = "node" if "node" in method else "edge"
            print(f"  Problem {idx} ({short}): {variants[method][:80]}...")

    if args.dry_run:
        print("\nDRY RUN - exiting")
        return

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Process each problem
    total_success = 0
    total_attempts = 0

    for idx, variants_to_fix in sorted(targets.items()):
        print(f"\n{'─'*70}")
        print(f"PROBLEM {idx}")
        print(f"{'─'*70}")

        # Load problem data
        input_file = os.path.join(args.input_dir, f"problem_{idx}.json")
        if not os.path.exists(input_file):
            print(f"  ✗ File not found: {input_file}")
            continue

        with open(input_file, 'r') as f:
            problem_data = json.load(f)

        print(f"  Question: {problem_data['original_question'][:80]}...")
        print(f"  Answer: {problem_data['original_answer']}")

        # Load existing output if resuming
        output_file = os.path.join(args.output_dir, f"problem_{idx}.json")
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                output_data = json.load(f)
        else:
            # Start with relevant fields from original
            output_data = {
                "original_question": problem_data["original_question"],
                "original_solution": problem_data["original_solution"],
                "original_answer": problem_data["original_answer"],
                "generated_code": problem_data["generated_code"],
                "dag": problem_data["dag"],
                "index": idx,
                "variations": {},
            }
            # Copy over existing successful variations that don't need fixing
            for method in ["variation_1_node_deletion", "variation_2_edge_deletion"]:
                if method not in variants_to_fix:
                    original_var = problem_data.get("variations", {}).get(method, {})
                    if original_var.get("success"):
                        output_data["variations"][method] = original_var

        # Regenerate each variant that needs fixing
        for method, feedback in variants_to_fix.items():
            short = "node" if "node" in method else "edge"

            # Skip if already succeeded (unless --force)
            existing_var = output_data.get("variations", {}).get(method, {})
            if existing_var.get("success") and not args.force:
                print(f"\n    Skipping {short} variant (already succeeded)")
                continue

            print(f"\n    Regenerating {short} variant...")
            print(f"    Feedback: {feedback[:100]}...")

            total_attempts += 1
            result = regenerate_variant(problem_data, method, feedback, args.max_retries)
            output_data["variations"][method] = result

            if result["success"]:
                total_success += 1

        # Save
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n  Saved: {output_file}")

    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total variants attempted: {total_attempts}")
    print(f"Successful: {total_success}")
    print(f"Failed: {total_attempts - total_success}")
    print(f"Results saved to: {args.output_dir}/")
    if total_success > 0:
        print(f"\nTo update HF dataset:")
        print(f"  python remake_impossible.py --update-hf --output-dir {args.output_dir}")


if __name__ == "__main__":
    main()
