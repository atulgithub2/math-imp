#!/usr/bin/env python3
"""
Comparative Reasoning Analysis Pipeline

Compares LLM reasoning on base AIME problems vs impossible variations.
Uses a 4-stage Claude Opus LLM-as-judge pipeline via AWS Bedrock to determine
whether differences introduced in the variation questions propagate into
the model's reasoning.

Stages:
  1. Base Reasoning Analysis
  2. Variation Reasoning Analysis
  3. Question Difference Analysis
  4. Propagation Analysis
"""

import argparse
import csv
import json
import os
import sys
import time
import traceback
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from anthropic import AnthropicBedrock
from datasets import load_dataset

# =============================================================================
# CONFIGURATION
# =============================================================================

AWS_REGION = "us-east-1"
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
MODEL_NAME = "us.anthropic.claude-opus-4-6-v1"
HF_TOKEN = os.environ.get("HF_TOKEN")

ALL_MODELS = [
    "DeepSeek-LLM-7B-Chat",
    "DeepSeek-Math-7B-Instruct",
    "InternLM2-Math-7B",
    "InternLM2-Chat-7B",
    "Qwen2.5-7B-Instruct",
    "Qwen2.5-Math-7B-Instruct",
]

VARIATIONS = ["node_deletion_problem", "edge_deletion_problem"]

BASE_DIR = Path(__file__).parent
BASE_CSV = BASE_DIR / "all_results_base.csv"
VAR_CSV = BASE_DIR / "all_results_var.csv"

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


# =============================================================================
# AWS BEDROCK CLIENT
# =============================================================================

def create_client():
    """Create AnthropicBedrock client with AWS credentials."""
    return AnthropicBedrock(
        aws_access_key=AWS_ACCESS_KEY,
        aws_secret_key=AWS_SECRET_KEY,
        aws_region=AWS_REGION,
    )


def call_claude(client, prompt: str, system_prompt: str = "") -> str:
    """Send a prompt to Claude Opus via AWS Bedrock with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            kwargs = {
                "model": MODEL_NAME,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            message = client.messages.create(**kwargs)
            return message.content[0].text
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_DELAY * (2 ** attempt)
                print(f"    API error (attempt {attempt + 1}): {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def parse_json_response(response: str) -> dict:
    """Extract JSON from a Claude response, handling markdown code fences."""
    text = response.strip()

    # Try to extract from code fences
    if "```json" in text:
        start = text.index("```json") + len("```json")
        end = text.index("```", start)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.index("```") + len("```")
        end = text.index("```", start)
        text = text[start:end].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Last resort: find the first { and last }
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1:
            try:
                return json.loads(text[first_brace:last_brace + 1])
            except json.JSONDecodeError:
                pass
        return {"raw_response": response, "parse_error": True}


# =============================================================================
# DATA LOADING
# =============================================================================

def load_data():
    """Load CSVs and HuggingFace dataset, build lookup tables."""
    print("Loading HuggingFace dataset (thulthula/math-bench)...")
    hf_dataset = load_dataset("thulthula/math-bench", token=HF_TOKEN)

    # Build solution lookup: (split, problem_num) -> {problem, solution, answer}
    solutions = {}
    for split_name in ["AIME24", "AIME25"]:
        if split_name not in hf_dataset:
            print(f"  Warning: split {split_name} not found in dataset")
            continue
        for row in hf_dataset[split_name]:
            # id is 0-indexed, problem_num is 1-indexed
            problem_num = int(row["id"]) + 1
            solutions[(split_name, problem_num)] = {
                "problem": row["problem"],
                "solution": row["solution"],
                "answer": row["answer"],
            }
    print(f"  Loaded {len(solutions)} solutions")

    print("Loading base results CSV...")
    base_data = {}  # (model, split, problem_num) -> row dict
    with open(BASE_CSV, "r", encoding="utf-8") as f:
        # Strip NUL bytes that appear in some response fields
        clean = (line.replace("\x00", "") for line in f)
        reader = csv.DictReader(clean)
        for row in reader:
            key = (row["model"], row["split"], int(row["problem_num"]))
            base_data[key] = row
    print(f"  Loaded {len(base_data)} base results")

    print("Loading variation results CSV...")
    var_data = {}  # (model, split, problem_num, variation) -> row dict
    with open(VAR_CSV, "r", encoding="utf-8") as f:
        # Strip NUL bytes that appear in some response fields
        clean = (line.replace("\x00", "") for line in f)
        reader = csv.DictReader(clean)
        for row in reader:
            key = (row["model"], row["split"], int(row["problem_num"]), row["variation"])
            var_data[key] = row
    print(f"  Loaded {len(var_data)} variation results")

    return solutions, base_data, var_data


def get_best_rollout(row: dict) -> str:
    """Pick the best rollout response: the one matching correct answer, skipping null entries."""
    correct = str(row.get("correct_answer", "")).strip()

    # Try to find a rollout that matches the correct answer and has a non-empty response
    for i in range(1, 11):
        pred_key = f"rollout_{i}_prediction"
        resp_key = f"rollout_{i}_response"
        pred = str(row.get(pred_key, "")).strip()
        resp = row.get(resp_key, "")

        # Skip null/empty entries
        if not pred or not resp or pred.lower() in ['null', 'none', '']:
            continue

        if pred == correct and resp:
            return resp

    # Fallback: find first non-null rollout
    for i in range(1, 11):
        resp_key = f"rollout_{i}_response"
        resp = row.get(resp_key, "")
        if resp and resp.strip() and str(resp).lower() not in ['null', 'none']:
            return resp

    return ""


# =============================================================================
# STAGE PROMPTS
# =============================================================================

STAGE1_SYSTEM = (
    "You are an expert mathematics reasoning analyst. Your job is to compare "
    "a model's mathematical reasoning against the ground-truth solution and "
    "identify what was correct and what went wrong. Respond ONLY with valid JSON."
)

STAGE1_PROMPT = """Below is an AIME competition problem, its ground-truth solution, and a model's reasoning attempt.

## Problem
{question}

## Ground-Truth Solution
{solution}

## Model's Reasoning
{response}

---

Analyze the model's reasoning step by step. Identify which parts of the reasoning were correct and which were wrong. For each step, explain why it was correct or incorrect.

Respond with JSON in this exact format:
{{
  "correct_steps": [
    {{"step": "description of correct step", "explanation": "why this is correct"}}
  ],
  "wrong_steps": [
    {{"step": "description of wrong step", "explanation": "why this is wrong and what should have been done"}}
  ],
  "summary": "Brief overall assessment of the model's reasoning quality"
}}"""

STAGE2_SYSTEM = STAGE1_SYSTEM

STAGE2_PROMPT = """Below is an AIME competition problem (which has been modified to be potentially impossible), its original ground-truth solution, and a model's reasoning attempt on the modified problem.

## Modified Problem (Variation)
{var_question}

## Original Ground-Truth Solution (for reference)
{solution}

## Model's Reasoning on Modified Problem
{response}

---

Analyze the model's reasoning step by step. Identify which parts of the reasoning were correct (aligned with sound mathematical logic) and which were wrong or confused. Pay special attention to how the model handled any missing or changed information.

Respond with JSON in this exact format:
{{
  "correct_steps": [
    {{"step": "description of correct step", "explanation": "why this is correct"}}
  ],
  "wrong_steps": [
    {{"step": "description of wrong step", "explanation": "why this is wrong and what should have been done"}}
  ],
  "summary": "Brief overall assessment of the model's reasoning quality on the modified problem"
}}"""

STAGE3_SYSTEM = (
    "You are an expert at comparing mathematical problem statements. "
    "Your job is to identify precisely what was changed between an original "
    "and a modified version of a problem. Respond ONLY with valid JSON."
)

STAGE3_PROMPT = """Compare these two versions of an AIME competition problem and identify all differences.

## Original Problem
{original_question}

## Modified Problem (Variation)
{var_question}

---

Identify exactly what information was removed, changed, or added between the original and modified problems. Be precise about specific numbers, constraints, or conditions that differ.

Respond with JSON in this exact format:
{{
  "differences": [
    {{"original": "text from original", "modified": "text from modified (or 'REMOVED')", "type": "removed|changed|added", "description": "what this difference means mathematically"}}
  ],
  "removed_info": "Summary of what key information was removed",
  "changed_constraints": "Summary of what constraints were changed",
  "summary": "Overall description of how the problem was modified"
}}"""

STAGE4_SYSTEM = (
    "You are an expert at analyzing how changes in mathematical problem statements "
    "affect model reasoning. Your job is to determine whether the differences between "
    "the original and modified problems actually propagated into differences in the "
    "model's reasoning. Respond ONLY with valid JSON."
)

STAGE4_PROMPT = """Given the analysis below, determine whether the question changes propagated into reasoning differences.

## Question Differences (from Stage 3)
{question_diff}

## Base Problem Reasoning Analysis (from Stage 1)
{base_analysis}

## Variation Problem Reasoning Analysis (from Stage 2)
{var_analysis}

---

For each question difference identified, determine:
1. Did this change cause a corresponding change in the model's reasoning?
2. Did the model notice the missing/changed information?
3. Did the model's errors on the variation stem from the question changes, or are they the same errors as on the base problem?

Respond with JSON in this exact format:
{{
  "propagated_differences": [
    {{"difference": "description of the question change", "reasoning_impact": "how this change affected the model's reasoning", "detected_by_model": true/false}}
  ],
  "non_propagated": [
    {{"difference": "description of change that did NOT affect reasoning", "explanation": "why the model's reasoning was unaffected"}}
  ],
  "propagation_score": 1-10,
  "summary": "Overall assessment of whether and how question changes propagated into reasoning differences"
}}

The propagation_score should be between 1 (minimal propagation - model reasoning mostly identical regardless of changes) and 10 (maximum propagation - all changes directly and significantly impacted reasoning). Higher scores indicate more propagation of changes into reasoning."""


# =============================================================================
# PIPELINE STAGES
# =============================================================================

def stage1_base_analysis(client, solution: str, base_response: str, question: str) -> dict:
    """Stage 1: Analyze reasoning on base (original) problem."""
    prompt = STAGE1_PROMPT.format(
        question=question,
        solution=solution,
        response=base_response,
    )
    raw = call_claude(client, prompt, STAGE1_SYSTEM)
    return parse_json_response(raw)


def stage2_variation_analysis(client, solution: str, var_response: str, var_question: str) -> dict:
    """Stage 2: Analyze reasoning on variation (modified) problem."""
    prompt = STAGE2_PROMPT.format(
        var_question=var_question,
        solution=solution,
        response=var_response,
    )
    raw = call_claude(client, prompt, STAGE2_SYSTEM)
    return parse_json_response(raw)


def stage3_question_diff(client, original_q: str, variation_q: str) -> dict:
    """Stage 3: Analyze differences between original and variation questions."""
    prompt = STAGE3_PROMPT.format(
        original_question=original_q,
        var_question=variation_q,
    )
    raw = call_claude(client, prompt, STAGE3_SYSTEM)
    return parse_json_response(raw)


def stage4_propagation(client, q_diff: dict, base_analysis: dict, var_analysis: dict) -> dict:
    """Stage 4: Determine if question differences propagated into reasoning."""
    prompt = STAGE4_PROMPT.format(
        question_diff=json.dumps(q_diff, indent=2),
        base_analysis=json.dumps(base_analysis, indent=2),
        var_analysis=json.dumps(var_analysis, indent=2),
    )
    raw = call_claude(client, prompt, STAGE4_SYSTEM)
    return parse_json_response(raw)


# =============================================================================
# PROCESSING
# =============================================================================

def process_single(
    client,
    model: str,
    split: str,
    problem_num: int,
    variation: str,
    solutions: dict,
    base_data: dict,
    var_data: dict,
) -> dict:
    """Run all 4 stages for a single (model, split, problem_num, variation) unit."""
    # Look up data
    sol_key = (split, problem_num)
    base_key = (model, split, problem_num)
    var_key = (model, split, problem_num, variation)

    if sol_key not in solutions:
        return {"error": f"No solution found for {sol_key}", "skipped": True}
    if base_key not in base_data:
        return {"error": f"No base data found for {base_key}", "skipped": True}
    if var_key not in var_data:
        return {"error": f"No variation data found for {var_key}", "skipped": True}

    sol = solutions[sol_key]
    base_row = base_data[base_key]
    var_row = var_data[var_key]

    original_question = sol["problem"]
    ground_truth_solution = sol["solution"]
    var_question = var_row["problem"]

    base_response = get_best_rollout(base_row)
    var_response = get_best_rollout(var_row)

    if not base_response or not base_response.strip():
        return {"error": "Empty base response", "skipped": True}
    if not var_response or not var_response.strip():
        return {"error": "Empty variation response", "skipped": True}

    # Stage 1
    print("    Stage 1: Base reasoning analysis...")
    s1 = stage1_base_analysis(client, ground_truth_solution, base_response, original_question)

    # Stage 2
    print("    Stage 2: Variation reasoning analysis...")
    s2 = stage2_variation_analysis(client, ground_truth_solution, var_response, var_question)

    # Stage 3
    print("    Stage 3: Question difference analysis...")
    s3 = stage3_question_diff(client, original_question, var_question)

    # Stage 4
    print("    Stage 4: Propagation analysis...")
    s4 = stage4_propagation(client, s3, s1, s2)

    # Get propagation score and calculate cutoff (threshold = 5)
    prop_score = s4.get("propagation_score", None)
    if prop_score is not None:
        # Ensure score is numeric and within 1-10 range
        try:
            prop_score = float(prop_score)
            prop_score = max(1, min(10, prop_score))  # Clamp to 1-10
        except (ValueError, TypeError):
            prop_score = None

    propagation_cutoff = "yes" if prop_score and prop_score >= 5 else "no"

    result = {
        "model": model,
        "split": split,
        "problem_num": problem_num,
        "variation": variation,
        "original_question": original_question,
        "variation_question": var_question,
        "correct_answer": sol["answer"],
        "base_predicted": base_row.get("predicted_answer", ""),
        "var_predicted": var_row.get("predicted_answer", ""),
        "base_is_correct": base_row.get("is_correct", ""),
        "var_is_correct": var_row.get("is_correct", ""),
        "stage1_base_analysis": s1,
        "stage2_variation_analysis": s2,
        "stage3_question_diff": s3,
        "stage4_propagation": s4,
        "propagation_score": prop_score,
        "propagation_cutoff": propagation_cutoff,
    }

    return result


def generate_summary(output_dir: Path):
    """Aggregate model JSON results into a summary CSV."""
    summary_path = output_dir / "summary.csv"
    rows = []

    for json_file in sorted(output_dir.glob("*.json")):
        if json_file.name == "errors.json":
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                model_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        # Each JSON file now contains a list of results for a model
        if not isinstance(model_data, dict) or "results" not in model_data:
            continue

        for data in model_data.get("results", []):
            if data.get("skipped") or data.get("error"):
                continue

            s1 = data.get("stage1_base_analysis", {})
            s2 = data.get("stage2_variation_analysis", {})
            s3 = data.get("stage3_question_diff", {})
            s4 = data.get("stage4_propagation", {})

            rows.append({
                "model": data.get("model", ""),
                "split": data.get("split", ""),
                "problem_num": data.get("problem_num", ""),
                "variation": data.get("variation", ""),
                "correct_answer": data.get("correct_answer", ""),
                "base_predicted": data.get("base_predicted", ""),
                "var_predicted": data.get("var_predicted", ""),
                "base_is_correct": data.get("base_is_correct", ""),
                "var_is_correct": data.get("var_is_correct", ""),
                "base_correct_steps": len(s1.get("correct_steps", [])),
                "base_wrong_steps": len(s1.get("wrong_steps", [])),
                "var_correct_steps": len(s2.get("correct_steps", [])),
                "var_wrong_steps": len(s2.get("wrong_steps", [])),
                "num_differences": len(s3.get("differences", [])),
                "num_propagated": len(s4.get("propagated_differences", [])),
                "num_non_propagated": len(s4.get("non_propagated", [])),
                "propagation_score": data.get("propagation_score", ""),
                "propagation_cutoff": data.get("propagation_cutoff", ""),
                "stage1_summary": s1.get("summary", ""),
                "stage2_summary": s2.get("summary", ""),
                "stage3_summary": s3.get("summary", ""),
                "stage4_summary": s4.get("summary", ""),
            })

    if rows:
        fieldnames = list(rows[0].keys())
        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nSummary saved to {summary_path} ({len(rows)} rows)")
    else:
        print("\nNo results to summarize.")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Comparative Reasoning Analysis: base vs variation AIME problems"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=ALL_MODELS,
        help="Models to process (default: all 6)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Starting problem number (default: 1)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=None,
        help="Max number of analysis units to process (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="comparative_results",
        help="Output directory (default: comparative_results)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reprocessing even if output files exist",
    )
    args = parser.parse_args()

    output_dir = BASE_DIR / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    solutions, base_data, var_data = load_data()

    # Create client
    client = create_client()

    # Build work list
    splits = ["AIME24", "AIME25"]
    work = []
    for model in args.models:
        for split in splits:
            # Determine problem range for this split
            problem_nums = sorted(
                pn for (s, pn) in solutions.keys() if s == split
            )
            for pn in problem_nums:
                if pn < args.start:
                    continue
                for var in VARIATIONS:
                    work.append((model, split, pn, var))

    total = len(work)
    if args.samples:
        work = work[: args.samples]
    print(f"\nTotal units to process: {len(work)} (of {total} total)")

    # Process - accumulate results per model
    processed = 0
    skipped = 0
    errors = []
    model_results = {model: [] for model in args.models}  # Accumulate results per model

    for idx, (model, split, pn, var) in enumerate(work, 1):
        safe_model = model.replace("/", "_").replace(" ", "_")
        model_json_path = output_dir / f"{safe_model}.json"

        # Check if this specific analysis unit already exists in the model's JSON
        skip_unit = False
        if model_json_path.exists() and not args.force:
            try:
                with open(model_json_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                existing_results = existing_data.get("results", [])
                # Check if this exact unit exists
                for r in existing_results:
                    if (r.get("split") == split and
                        r.get("problem_num") == pn and
                        r.get("variation") == var and
                        not r.get("skipped")):
                        skip_unit = True
                        break
            except (json.JSONDecodeError, IOError):
                pass

        if skip_unit:
            skipped += 1
            print(f"[{idx}/{len(work)}] SKIP (exists): {model} | {split} P{pn} | {var}")
            continue

        print(f"[{idx}/{len(work)}] Processing: {model} | {split} P{pn} | {var}")
        try:
            result = process_single(
                client, model, split, pn, var,
                solutions, base_data, var_data,
            )
            if result.get("skipped"):
                print(f"    Skipped: {result.get('error', 'unknown')}")
                skipped += 1
            else:
                score = result.get("propagation_score", "N/A")
                cutoff = result.get("propagation_cutoff", "N/A")
                print(f"    Done. Propagation score: {score} (cutoff: {cutoff})")
                processed += 1

            # Add result to model's accumulator
            model_results[model].append(result)
        except Exception as e:
            print(f"    ERROR: {e}")
            traceback.print_exc()
            errors.append({
                "model": model,
                "split": split,
                "problem_num": pn,
                "variation": var,
                "error": str(e),
            })

    # Save results per model (one JSON file per model)
    print("\nSaving model results...")
    for model in args.models:
        safe_model = model.replace("/", "_").replace(" ", "_")
        model_json_path = output_dir / f"{safe_model}.json"

        # Load existing results if file exists and not forcing
        existing_results = []
        if model_json_path.exists() and not args.force:
            try:
                with open(model_json_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                existing_results = existing_data.get("results", [])
            except (json.JSONDecodeError, IOError):
                pass

        # Merge new results with existing, avoiding duplicates
        all_results = existing_results.copy()
        for new_result in model_results[model]:
            # Check if this result already exists
            is_duplicate = False
            for existing in all_results:
                if (existing.get("split") == new_result.get("split") and
                    existing.get("problem_num") == new_result.get("problem_num") and
                    existing.get("variation") == new_result.get("variation")):
                    is_duplicate = True
                    break
            if not is_duplicate:
                all_results.append(new_result)

        # Save model's JSON file
        model_data = {
            "model": model,
            "total_results": len(all_results),
            "results": all_results
        }
        with open(model_json_path, "w", encoding="utf-8") as f:
            json.dump(model_data, f, indent=2, ensure_ascii=False)
        print(f"  Saved {model}: {len(all_results)} results")

    # Save error log
    if errors:
        error_path = output_dir / "errors.json"
        with open(error_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2)
        print(f"\n{len(errors)} errors saved to {error_path}")

    # Generate summary
    generate_summary(output_dir)

    print(f"\nDone. Processed: {processed}, Skipped: {skipped}, Errors: {len(errors)}")


if __name__ == "__main__":
    main()
