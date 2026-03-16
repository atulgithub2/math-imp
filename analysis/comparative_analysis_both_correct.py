#!/usr/bin/env python3
"""
Comparative Analysis for Cases Where Both Base and Variation Are Correct

This script filters and analyzes only the cases where the model got BOTH
the base problem AND the variation problem correct. Shows 3 examples.
"""

import csv
import json
import os
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

BASE_DIR = Path(__file__).parent
BASE_CSV = BASE_DIR / "all_results.csv"
VAR_CSV = BASE_DIR / "all_results_var.csv"

MAX_EXAMPLES = 3  # Only show 3 examples

# =============================================================================
# CLIENT & PROMPTS (from original)
# =============================================================================

def create_client():
    """Create AnthropicBedrock client with AWS credentials."""
    return AnthropicBedrock(
        aws_access_key=AWS_ACCESS_KEY,
        aws_secret_key=AWS_SECRET_KEY,
        aws_region=AWS_REGION,
    )


def call_claude(client, prompt: str, system_prompt: str = "") -> str:
    """Send a prompt to Claude Opus via AWS Bedrock."""
    kwargs = {
        "model": MODEL_NAME,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    message = client.messages.create(**kwargs)
    return message.content[0].text


def parse_json_response(response: str) -> dict:
    """Extract JSON from a Claude response."""
    text = response.strip()

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
    """Load CSVs and HuggingFace dataset."""
    print("Loading HuggingFace dataset...")
    hf_dataset = load_dataset("thulthula/math-bench", token=HF_TOKEN)

    solutions = {}
    for split_name in ["AIME24", "AIME25"]:
        if split_name not in hf_dataset:
            continue
        for row in hf_dataset[split_name]:
            problem_num = int(row["id"]) + 1
            solutions[(split_name, problem_num)] = {
                "problem": row["problem"],
                "solution": row["solution"],
                "answer": row["answer"],
            }
    print(f"  Loaded {len(solutions)} solutions")

    print("Loading all_results.csv...")
    base_data = {}
    with open(BASE_CSV, "r", encoding="utf-8") as f:
        clean = (line.replace("\x00", "") for line in f)
        reader = csv.DictReader(clean)
        for row in reader:
            key = (row["model"], row["split"], int(row["problem_num"]))
            base_data[key] = row
    print(f"  Loaded {len(base_data)} results")

    print("Loading variation results CSV...")
    var_data = {}
    with open(VAR_CSV, "r", encoding="utf-8") as f:
        clean = (line.replace("\x00", "") for line in f)
        reader = csv.DictReader(clean)
        for row in reader:
            key = (row["model"], row["split"], int(row["problem_num"]), row["variation"])
            var_data[key] = row
    print(f"  Loaded {len(var_data)} variation results")

    return solutions, base_data, var_data


def get_best_rollout(row: dict) -> str:
    """Pick the best rollout response."""
    correct = str(row.get("correct_answer", "")).strip()

    for i in range(1, 11):
        pred_key = f"rollout_{i}_prediction"
        resp_key = f"rollout_{i}_response"
        pred = str(row.get(pred_key, "")).strip()
        resp = row.get(resp_key, "")

        if not pred or not resp or pred.lower() in ['null', 'none', '']:
            continue

        if pred == correct and resp:
            return resp

    for i in range(1, 11):
        resp_key = f"rollout_{i}_response"
        resp = row.get(resp_key, "")
        if resp and resp.strip() and str(resp).lower() not in ['null', 'none']:
            return resp

    return ""


# =============================================================================
# FIND BOTH-CORRECT CASES
# =============================================================================

def find_both_correct_cases(base_data, var_data):
    """Find cases where base is correct and at least one variation is correct."""
    from collections import defaultdict

    # Group variations by (model, split, problem_num)
    var_grouped = defaultdict(list)
    for (model, split, problem_num, variation), var_row in var_data.items():
        key = (model, split, problem_num)
        var_grouped[key].append((variation, var_row))

    both_correct = []

    # For each base case, check if it's correct and has any correct variation
    for base_key, base_row in base_data.items():
        base_correct = str(base_row.get("is_correct", "")).strip().lower() == "true"

        if base_correct and base_key in var_grouped:
            # Check each variation for this problem
            for variation, var_row in var_grouped[base_key]:
                var_correct = str(var_row.get("is_correct", "")).strip().lower() == "true"

                if var_correct:
                    model, split, problem_num = base_key
                    both_correct.append({
                        "model": model,
                        "split": split,
                        "problem_num": problem_num,
                        "variation": variation,
                        "base_row": base_row,
                        "var_row": var_row,
                    })

    return both_correct


# =============================================================================
# ANALYSIS STAGES (all 4 stages from original)
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


def analyze_example(client, case, solutions):
    """Run all 4 stages of analysis on a single both-correct case."""
    model = case["model"]
    split = case["split"]
    problem_num = case["problem_num"]
    variation = case["variation"]

    base_row = case["base_row"]
    var_row = case["var_row"]

    sol_key = (split, problem_num)
    if sol_key not in solutions:
        return None

    sol = solutions[sol_key]
    original_question = sol["problem"]
    ground_truth_solution = sol["solution"]
    var_question = var_row["problem"]

    base_response = get_best_rollout(base_row)
    var_response = get_best_rollout(var_row)

    if not base_response or not var_response:
        return None

    print(f"\n{'='*80}")
    print(f"MODEL: {model}")
    print(f"PROBLEM: {split} #{problem_num}")
    print(f"VARIATION: {variation}")
    print(f"{'='*80}")

    print("\n--- ORIGINAL PROBLEM ---")
    print(original_question)
    print(f"\nCorrect Answer: {sol['answer']}")
    print(f"Base Prediction: {base_row.get('predicted_answer', '')} ✓")

    print("\n--- VARIATION PROBLEM ---")
    print(var_question)
    print(f"Variation Prediction: {var_row.get('predicted_answer', '')} ✓")

    # Stage 1: Base reasoning analysis
    print("\n--- STAGE 1: BASE REASONING ANALYSIS ---")
    s1_prompt = STAGE1_PROMPT.format(
        question=original_question,
        solution=ground_truth_solution,
        response=base_response,
    )
    s1_raw = call_claude(client, s1_prompt, STAGE1_SYSTEM)
    s1 = parse_json_response(s1_raw)
    print(json.dumps(s1, indent=2))

    # Stage 2: Variation reasoning analysis
    print("\n--- STAGE 2: VARIATION REASONING ANALYSIS ---")
    s2_prompt = STAGE2_PROMPT.format(
        var_question=var_question,
        solution=ground_truth_solution,
        response=var_response,
    )
    s2_raw = call_claude(client, s2_prompt, STAGE2_SYSTEM)
    s2 = parse_json_response(s2_raw)
    print(json.dumps(s2, indent=2))

    # Stage 3: Question difference analysis
    print("\n--- STAGE 3: QUESTION DIFFERENCE ANALYSIS ---")
    s3_prompt = STAGE3_PROMPT.format(
        original_question=original_question,
        var_question=var_question,
    )
    s3_raw = call_claude(client, s3_prompt, STAGE3_SYSTEM)
    s3 = parse_json_response(s3_raw)
    print(json.dumps(s3, indent=2))

    # Stage 4: Propagation analysis
    print("\n--- STAGE 4: PROPAGATION ANALYSIS ---")
    s4_prompt = STAGE4_PROMPT.format(
        question_diff=json.dumps(s3, indent=2),
        base_analysis=json.dumps(s1, indent=2),
        var_analysis=json.dumps(s2, indent=2),
    )
    s4_raw = call_claude(client, s4_prompt, STAGE4_SYSTEM)
    s4 = parse_json_response(s4_raw)
    print(json.dumps(s4, indent=2))

    # Calculate propagation score and cutoff
    prop_score = s4.get("propagation_score", None)
    if prop_score is not None:
        try:
            prop_score = float(prop_score)
            prop_score = max(1, min(10, prop_score))  # Clamp to 1-10
        except (ValueError, TypeError):
            prop_score = None

    propagation_cutoff = "yes" if prop_score and prop_score >= 5 else "no"

    return {
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


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 80)
    print("COMPARATIVE ANALYSIS: BOTH BASE AND VARIATION CORRECT")
    print("=" * 80)

    # Load data
    solutions, base_data, var_data = load_data()

    # Find both-correct cases
    print("\nFinding cases where both base and variation are correct...")
    both_correct = find_both_correct_cases(base_data, var_data)
    print(f"Found {len(both_correct)} cases where both are correct")

    if len(both_correct) == 0:
        print("\nNo cases found where both base and variation are correct!")
        return

    # Take only first MAX_EXAMPLES
    examples = both_correct[:MAX_EXAMPLES]
    print(f"\nAnalyzing first {len(examples)} examples...\n")

    # Create client
    client = create_client()

    # Analyze each example
    results = []
    for i, case in enumerate(examples, 1):
        print(f"\n{'#'*80}")
        print(f"# EXAMPLE {i}/{len(examples)}")
        print(f"{'#'*80}")

        result = analyze_example(client, case, solutions)
        if result:
            results.append(result)

    # Save results
    output_file = BASE_DIR / "both_correct_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_both_correct": len(both_correct),
            "analyzed_examples": len(results),
            "examples": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"Total cases where both correct: {len(both_correct)}")
    print(f"Analyzed examples: {len(results)}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
