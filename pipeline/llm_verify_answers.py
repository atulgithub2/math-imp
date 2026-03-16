#!/usr/bin/env python3
"""
LLM-based answer verification for MATH dataset evaluation results.

This script uses an LLM to verify if predicted answers match correct answers,
accounting for different formatting styles (e.g., "1/2" vs "0.5", spacing differences).

Usage:
    python3 llm_verify_answers.py verification_for_llm.csv --output verified_results.csv
    python3 llm_verify_answers.py verification_for_llm.csv --model gpt-4 --api-key YOUR_KEY
"""

import pandas as pd
import argparse
import re
from pathlib import Path
from tqdm import tqdm
import time

# For local LLM verification using vLLM
try:
    from vllm import LLM, SamplingParams
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    print("Warning: vLLM not available. Only API-based verification supported.")

# For API-based verification
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ============================================================================
# VERIFICATION PROMPT
# ============================================================================

def create_verification_prompt(correct_answer, predicted_answer):
    """Create prompt for LLM to verify if answers match."""
    return f"""You are a mathematics answer verification expert. Your task is to determine if two mathematical answers are equivalent, accounting for different formatting and representation styles.

CORRECT ANSWER: {correct_answer}

PREDICTED ANSWER: {predicted_answer}

Determine if these two answers are mathematically equivalent. Consider:
- Different representations of the same number (e.g., "1/2" = "0.5")
- Spacing differences (e.g., "\\\\frac{{1}}{{2}}" vs "\\\\frac{{ 1 }}{{ 2 }}")
- Equivalent mathematical expressions (e.g., "2+3" = "5")
- LaTeX formatting variations
- Different forms of the same answer (e.g., simplified vs unsimplified fractions)

Respond with EXACTLY ONE WORD:
- "CORRECT" if the answers are mathematically equivalent
- "INCORRECT" if the answers are mathematically different
- "UNCLEAR" if you cannot determine equivalence with high confidence

Your response (one word only):"""

# ============================================================================
# VERIFICATION ENGINES
# ============================================================================

def verify_with_vllm(df, model_path="Qwen/Qwen2.5-Math-7B-Instruct", batch_size=50):
    """Verify answers using local vLLM model."""
    if not VLLM_AVAILABLE:
        raise RuntimeError("vLLM not available. Install with: pip install vllm")

    print(f"\nLoading verification model: {model_path}")
    model = LLM(
        model=model_path,
        dtype="bfloat16",
        max_model_len=2048,
        gpu_memory_utilization=0.8
    )

    sampling_params = SamplingParams(
        temperature=0.0,  # Deterministic
        max_tokens=10,
        top_p=1.0
    )

    results = []
    total = len(df)

    print(f"\nVerifying {total} answer pairs...")

    for batch_start in tqdm(range(0, total, batch_size), desc="Batches"):
        batch_end = min(batch_start + batch_size, total)
        batch_df = df.iloc[batch_start:batch_end]

        # Create prompts
        prompts = []
        for _, row in batch_df.iterrows():
            prompt = create_verification_prompt(row['correct_answer'], row['predicted_answer'])
            prompts.append(prompt)

        # Generate
        outputs = model.generate(prompts, sampling_params)

        # Extract results
        for output in outputs:
            response = output.outputs[0].text.strip().upper()
            # Extract first word
            first_word = response.split()[0] if response else "UNCLEAR"

            if "CORRECT" in first_word:
                results.append("correct")
            elif "INCORRECT" in first_word:
                results.append("incorrect")
            else:
                results.append("unclear")

    return results

def verify_with_anthropic(df, api_key, model="claude-3-5-sonnet-20241022"):
    """Verify answers using Anthropic API."""
    if not ANTHROPIC_AVAILABLE:
        raise RuntimeError("Anthropic SDK not available. Install with: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)
    results = []

    print(f"\nVerifying {len(df)} answer pairs with Claude...")

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Verifying"):
        prompt = create_verification_prompt(row['correct_answer'], row['predicted_answer'])

        try:
            message = client.messages.create(
                model=model,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            response = message.content[0].text.strip().upper()
            first_word = response.split()[0] if response else "UNCLEAR"

            if "CORRECT" in first_word:
                results.append("correct")
            elif "INCORRECT" in first_word:
                results.append("incorrect")
            else:
                results.append("unclear")

        except Exception as e:
            print(f"\nError on row {idx}: {e}")
            results.append("error")

        # Rate limiting
        time.sleep(0.1)

    return results

def verify_with_openai(df, api_key, model="gpt-4"):
    """Verify answers using OpenAI API."""
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI SDK not available. Install with: pip install openai")

    client = openai.OpenAI(api_key=api_key)
    results = []

    print(f"\nVerifying {len(df)} answer pairs with {model}...")

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Verifying"):
        prompt = create_verification_prompt(row['correct_answer'], row['predicted_answer'])

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            text = response.choices[0].message.content.strip().upper()
            first_word = text.split()[0] if text else "UNCLEAR"

            if "CORRECT" in first_word:
                results.append("correct")
            elif "INCORRECT" in first_word:
                results.append("incorrect")
            else:
                results.append("unclear")

        except Exception as e:
            print(f"\nError on row {idx}: {e}")
            results.append("error")

        # Rate limiting
        time.sleep(0.1)

    return results

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="LLM-based answer verification")
    parser.add_argument("input_csv", help="Input CSV file with verification data")
    parser.add_argument("--output", "-o", default=None,
                        help="Output CSV file (default: <input>_verified.csv)")
    parser.add_argument("--method", choices=['vllm', 'anthropic', 'openai'],
                        default='vllm',
                        help="Verification method (default: vllm)")
    parser.add_argument("--model", default=None,
                        help="Model to use (default depends on method)")
    parser.add_argument("--api-key", default=None,
                        help="API key for anthropic/openai methods")
    parser.add_argument("--batch-size", type=int, default=50,
                        help="Batch size for vLLM (default: 50)")
    parser.add_argument("--skip-exact-matches", action='store_true',
                        help="Skip verification for rows already marked as correct")
    args = parser.parse_args()

    # Load data
    print(f"Loading: {args.input_csv}")
    df = pd.read_csv(args.input_csv)

    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    # Ensure required columns exist
    required_cols = ['correct_answer', 'predicted_answer', 'is_correct_exact']
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Required column '{col}' not found in CSV")
            return

    # Add llm_verified column if not exists
    if 'llm_verified' not in df.columns:
        df['llm_verified'] = ''

    # Filter rows to verify
    if args.skip_exact_matches:
        # Only verify rows where exact match failed
        mask = df['is_correct_exact'] == False
        to_verify_df = df[mask].copy()
        print(f"\nSkipping exact matches, verifying {len(to_verify_df)} rows")
    else:
        to_verify_df = df.copy()
        print(f"\nVerifying all {len(to_verify_df)} rows")

    # Skip rows with no predicted answer
    to_verify_df = to_verify_df[to_verify_df['predicted_answer'].notna()].copy()
    print(f"Rows with predicted answers: {len(to_verify_df)}")

    if len(to_verify_df) == 0:
        print("No rows to verify!")
        return

    # Run verification
    if args.method == 'vllm':
        model_path = args.model or "Qwen/Qwen2.5-Math-7B-Instruct"
        verification_results = verify_with_vllm(to_verify_df, model_path, args.batch_size)

    elif args.method == 'anthropic':
        if not args.api_key:
            print("Error: --api-key required for anthropic method")
            return
        model = args.model or "claude-3-5-sonnet-20241022"
        verification_results = verify_with_anthropic(to_verify_df, args.api_key, model)

    elif args.method == 'openai':
        if not args.api_key:
            print("Error: --api-key required for openai method")
            return
        model = args.model or "gpt-4"
        verification_results = verify_with_openai(to_verify_df, args.api_key, model)

    # Update results
    df.loc[to_verify_df.index, 'llm_verified'] = verification_results

    # Calculate final accuracy
    print(f"\n{'='*80}")
    print("VERIFICATION RESULTS")
    print(f"{'='*80}")

    # Count results
    verified_correct = (df['llm_verified'] == 'correct').sum()
    verified_incorrect = (df['llm_verified'] == 'incorrect').sum()
    verified_unclear = (df['llm_verified'] == 'unclear').sum()
    verified_error = (df['llm_verified'] == 'error').sum()
    not_verified = (df['llm_verified'] == '').sum()

    print(f"\nVerification status:")
    print(f"  Correct: {verified_correct}")
    print(f"  Incorrect: {verified_incorrect}")
    print(f"  Unclear: {verified_unclear}")
    print(f"  Error: {verified_error}")
    print(f"  Not verified: {not_verified}")

    # Calculate accuracy
    total_verified = verified_correct + verified_incorrect + verified_unclear
    if total_verified > 0:
        accuracy = (verified_correct / total_verified) * 100
        print(f"\nLLM-verified accuracy: {verified_correct}/{total_verified} ({accuracy:.1f}%)")

    # Compare with exact match
    exact_correct = df['is_correct_exact'].sum()
    print(f"Exact match accuracy: {exact_correct}/{len(df)} ({(exact_correct/len(df)*100):.1f}%)")

    # Save output
    if args.output:
        output_file = args.output
    else:
        input_path = Path(args.input_csv)
        output_file = input_path.parent / f"{input_path.stem}_verified.csv"

    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved: {output_file}")

    # Save summary
    summary_file = output_file.replace('.csv', '_summary.txt')
    with open(summary_file, 'w') as f:
        f.write(f"LLM Verification Summary\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Method: {args.method}\n")
        if args.model:
            f.write(f"Model: {args.model}\n")
        f.write(f"\nTotal rows: {len(df)}\n")
        f.write(f"Verified: {total_verified}\n")
        f.write(f"\nResults:\n")
        f.write(f"  Correct: {verified_correct}\n")
        f.write(f"  Incorrect: {verified_incorrect}\n")
        f.write(f"  Unclear: {verified_unclear}\n")
        f.write(f"  Error: {verified_error}\n")
        if total_verified > 0:
            f.write(f"\nLLM-verified accuracy: {verified_correct}/{total_verified} ({accuracy:.1f}%)\n")
        f.write(f"Exact match accuracy: {exact_correct}/{len(df)} ({(exact_correct/len(df)*100):.1f}%)\n")

    print(f"✓ Saved: {summary_file}")

if __name__ == "__main__":
    main()
