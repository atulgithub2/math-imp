#!/usr/bin/env python3
"""
Robust programmatic answer verification for MATH dataset results.

Uses multiple strategies:
1. Exact string match (after normalization)
2. Numeric equivalence (float comparison)
3. SymPy symbolic equivalence (parse LaTeX → compare symbolically)
4. Fraction/radical normalization
5. Matrix/tuple comparison

Usage:
    python3 verify_math_answers.py all_results_math_52examples.csv
"""

import pandas as pd
import re
import sys
from fractions import Fraction
from pathlib import Path

try:
    import sympy
    from sympy.parsing.latex import parse_latex
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False
    print("Warning: sympy not available, symbolic verification disabled")


# ============================================================================
# NORMALIZATION HELPERS
# ============================================================================

def strip_latex(s):
    """Remove LaTeX wrappers and normalize whitespace."""
    if s is None:
        return None
    s = str(s).strip()
    # Remove $ wrappers
    s = s.strip('$')
    # Remove \text{}, \mathrm{}, etc.
    s = re.sub(r'\\(?:text|mathrm|mathbf|mathit|operatorname)\{([^}]*)\}', r'\1', s)
    # Remove \left and \right
    s = re.sub(r'\\(?:left|right)', '', s)
    # Normalize whitespace
    s = ' '.join(s.split())
    return s


def latex_to_fraction(s):
    """Try to parse LaTeX fraction to Python Fraction."""
    s = strip_latex(s)
    if s is None:
        return None

    # Match \frac{num}{den}
    m = re.match(r'^\\frac\{([^}]+)\}\{([^}]+)\}$', s)
    if m:
        try:
            num = m.group(1).strip()
            den = m.group(2).strip()
            # Handle nested expressions like \sqrt{3}
            num_val = float(sympy_eval(num)) if SYMPY_AVAILABLE else float(num)
            den_val = float(sympy_eval(den)) if SYMPY_AVAILABLE else float(den)
            return num_val / den_val
        except:
            pass

    # Match a/b plain fraction
    m = re.match(r'^(-?\d+)\s*/\s*(\d+)$', s)
    if m:
        try:
            return Fraction(int(m.group(1)), int(m.group(2)))
        except:
            pass

    return None


def sympy_eval(expr_str):
    """Try to evaluate a LaTeX expression using sympy."""
    if not SYMPY_AVAILABLE:
        return None
    try:
        return parse_latex(expr_str)
    except:
        return None


def try_float(s):
    """Try to convert string to float, handling common patterns."""
    if s is None:
        return None
    s = str(s).strip()

    # Remove LaTeX wrappers
    s = strip_latex(s)

    # Handle \frac{a}{b}
    m = re.match(r'^\\frac\{(-?\d+)\}\{(-?\d+)\}$', s)
    if m:
        try:
            return float(int(m.group(1))) / float(int(m.group(2)))
        except:
            pass

    # Handle a/b
    m = re.match(r'^(-?\d+)\s*/\s*(-?\d+)$', s)
    if m:
        try:
            return float(int(m.group(1))) / float(int(m.group(2)))
        except:
            pass

    # Handle pi expressions like "10 \pi - 29"
    # Just try direct float
    try:
        return float(s)
    except:
        pass

    return None


def normalize_for_comparison(s):
    """Deep normalization for string comparison."""
    if s is None:
        return None
    s = str(s).strip()

    # Remove all LaTeX commands that are just formatting
    s = strip_latex(s)

    # Remove backslashes
    s = s.replace('\\', '')
    # Remove braces
    s = s.replace('{', '').replace('}', '')
    # Remove $
    s = s.replace('$', '')
    # Normalize whitespace
    s = ' '.join(s.split())
    # Lowercase
    s = s.lower()
    # Remove trailing periods/commas
    s = s.rstrip('.,;')

    return s


def extract_matrix_entries(s):
    """Extract matrix entries from pmatrix/bmatrix LaTeX."""
    if s is None:
        return None
    s = str(s).strip()

    # Try to find pmatrix/bmatrix content
    m = re.search(r'\\begin\{[pb]matrix\}(.*?)\\end\{[pb]matrix\}', s, re.DOTALL)
    if m:
        content = m.group(1)
    else:
        # Try inline format like \begin{pmatrix} a \\ b \end{pmatrix}
        content = s

    # Split by \\ for rows
    rows = re.split(r'\\\\', content)
    entries = []
    for row in rows:
        # Split by & for columns
        cols = re.split(r'&', row)
        for col in cols:
            col = col.strip()
            if col:
                entries.append(col)

    return entries if entries else None


def normalize_matrix_entry(entry):
    """Normalize a single matrix entry (could be fraction, number, etc.)."""
    entry = entry.strip()

    # Try as fraction: \frac{a}{b}
    m = re.match(r'\\frac\{(-?\d+)\}\{(-?\d+)\}', entry)
    if m:
        return f"{m.group(1)}/{m.group(2)}"

    # Try as plain fraction: a/b
    m = re.match(r'(-?\d+)/(-?\d+)', entry)
    if m:
        return f"{m.group(1)}/{m.group(2)}"

    # Return cleaned
    return normalize_for_comparison(entry)


def extract_tuple_entries(s):
    """Extract entries from tuple-like answers: (a, b, c)."""
    if s is None:
        return None
    s = str(s).strip()

    # Match \left( ... \right) or just ( ... )
    m = re.match(r'^\\?(?:left)?\((.+?)\\?(?:right)?\)$', s.strip())
    if m:
        content = m.group(1)
        entries = [e.strip() for e in content.split(',')]
        return entries

    # Match plain (a,b) or (a, b)
    m = re.match(r'^\((.+?)\)$', s.strip())
    if m:
        content = m.group(1)
        entries = [e.strip() for e in content.split(',')]
        return entries

    return None


# ============================================================================
# COMPARISON STRATEGIES
# ============================================================================

def compare_answers(correct, predicted):
    """
    Compare two mathematical answers using multiple strategies.

    Returns: (is_match: bool, method: str, confidence: str)
    """
    if predicted is None or correct is None:
        return False, 'null', 'high'

    correct_str = str(correct).strip()
    predicted_str = str(predicted).strip()

    if not predicted_str or predicted_str.lower() in ('none', 'nan', 'answer'):
        return False, 'empty_or_garbage', 'high'

    # Strategy 1: Exact string match
    if correct_str == predicted_str:
        return True, 'exact', 'high'

    # Strategy 2: Normalized string match
    c_norm = normalize_for_comparison(correct_str)
    p_norm = normalize_for_comparison(predicted_str)
    if c_norm and p_norm and c_norm == p_norm:
        return True, 'normalized_string', 'high'

    # Strategy 3: Numeric equivalence
    c_float = try_float(correct_str)
    p_float = try_float(predicted_str)
    if c_float is not None and p_float is not None:
        if abs(c_float - p_float) < 1e-6:
            return True, 'numeric', 'high'
        else:
            return False, 'numeric_mismatch', 'high'

    # Strategy 4: Matrix comparison
    c_matrix = extract_matrix_entries(correct_str)
    p_matrix = extract_matrix_entries(predicted_str)
    if c_matrix and p_matrix:
        if len(c_matrix) == len(p_matrix):
            all_match = True
            for ce, pe in zip(c_matrix, p_matrix):
                ce_norm = normalize_matrix_entry(ce)
                pe_norm = normalize_matrix_entry(pe)
                if ce_norm != pe_norm:
                    # Try numeric comparison of entries
                    ce_f = try_float(ce)
                    pe_f = try_float(pe)
                    if ce_f is not None and pe_f is not None:
                        if abs(ce_f - pe_f) > 1e-6:
                            all_match = False
                            break
                    else:
                        all_match = False
                        break
            if all_match:
                return True, 'matrix_match', 'high'
            else:
                return False, 'matrix_mismatch', 'high'
        else:
            return False, 'matrix_size_mismatch', 'high'

    # Strategy 5: Tuple comparison
    c_tuple = extract_tuple_entries(correct_str)
    p_tuple = extract_tuple_entries(predicted_str)
    if c_tuple and p_tuple:
        if len(c_tuple) == len(p_tuple):
            all_match = True
            for ce, pe in zip(c_tuple, p_tuple):
                if normalize_for_comparison(ce) != normalize_for_comparison(pe):
                    ce_f = try_float(ce)
                    pe_f = try_float(pe)
                    if ce_f is not None and pe_f is not None:
                        if abs(ce_f - pe_f) > 1e-6:
                            all_match = False
                            break
                    else:
                        all_match = False
                        break
            if all_match:
                return True, 'tuple_match', 'high'

    # Strategy 6: SymPy symbolic equivalence
    if SYMPY_AVAILABLE:
        try:
            c_sym = parse_latex(correct_str)
            p_sym = parse_latex(predicted_str)
            if c_sym is not None and p_sym is not None:
                diff = sympy.simplify(c_sym - p_sym)
                if diff == 0:
                    return True, 'sympy_symbolic', 'high'
                # Try numerical evaluation
                try:
                    diff_val = complex(diff.evalf())
                    if abs(diff_val) < 1e-6:
                        return True, 'sympy_numeric', 'medium'
                except:
                    pass
        except:
            pass

    # Strategy 7: Degree comparison (30^\circ vs 30)
    c_deg = re.match(r'^(\d+)\s*\\?(?:\^\\circ|°|degrees?)$', correct_str)
    p_deg = re.match(r'^(\d+)\s*\\?(?:\^\\circ|°|degrees?)$', predicted_str)
    if c_deg and p_deg:
        if c_deg.group(1) == p_deg.group(1):
            return True, 'degree_match', 'high'
    # One has degree symbol, other doesn't
    if c_deg:
        p_plain = re.match(r'^(\d+)$', predicted_str)
        if p_plain and c_deg.group(1) == p_plain.group(1):
            return True, 'degree_implicit', 'medium'
    if p_deg:
        c_plain = re.match(r'^(\d+)$', correct_str)
        if c_plain and p_deg.group(1) == c_plain.group(1):
            return True, 'degree_implicit', 'medium'

    # If we got here, answers don't match by any strategy
    # Check if prediction looks like garbage (not a real answer)
    if len(predicted_str) > 100 or re.search(r'\\(text|begin|end|section|item)', predicted_str):
        return False, 'garbage_prediction', 'high'

    return False, 'no_match', 'medium'


# ============================================================================
# MAIN VERIFICATION
# ============================================================================

def verify_csv(input_path, output_path=None):
    """Run verification on a results CSV file."""
    print(f"Loading: {input_path}")
    df = pd.read_csv(input_path)
    print(f"Total rows: {len(df)}")
    print(f"Models: {df['model'].unique().tolist()}")
    print(f"Variations: {df['variation'].unique().tolist()}")

    # Run verification
    results = []
    methods = []
    confidences = []

    for idx, row in df.iterrows():
        correct = row['correct_answer']
        predicted = row['predicted_answer']

        is_match, method, confidence = compare_answers(correct, predicted)
        results.append('correct' if is_match else 'incorrect')
        methods.append(method)
        confidences.append(confidence)

    df['llm_verified'] = results
    df['verify_method'] = methods
    df['verify_confidence'] = confidences

    # ========================================================================
    # PRINT RESULTS
    # ========================================================================
    print(f"\n{'='*80}")
    print("VERIFICATION RESULTS")
    print(f"{'='*80}")

    total = len(df)
    verified_correct = (df['llm_verified'] == 'correct').sum()
    verified_incorrect = (df['llm_verified'] == 'incorrect').sum()

    print(f"\nOverall:")
    print(f"  Correct (verified):   {verified_correct}/{total} ({verified_correct/total*100:.1f}%)")
    print(f"  Incorrect (verified): {verified_incorrect}/{total} ({verified_incorrect/total*100:.1f}%)")

    # Compare with original exact match
    exact_correct = df['is_correct_exact'].sum()
    print(f"\n  Original exact match: {exact_correct}/{total} ({exact_correct/total*100:.1f}%)")
    print(f"  After verification:   {verified_correct}/{total} ({verified_correct/total*100:.1f}%)")
    new_correct = verified_correct - exact_correct
    print(f"  Newly found correct:  {new_correct}")

    # Show verification methods used
    print(f"\nVerification methods used:")
    for method, count in df['verify_method'].value_counts().items():
        print(f"  {method}: {count}")

    # Per-model results
    print(f"\n{'='*80}")
    print("PER-MODEL RESULTS")
    print(f"{'='*80}")

    summary_rows = []
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        m_total = len(model_df)
        m_exact = model_df['is_correct_exact'].sum()
        m_verified = (model_df['llm_verified'] == 'correct').sum()

        print(f"\n{model}:")
        print(f"  Exact match:  {m_exact}/{m_total} ({m_exact/m_total*100:.1f}%)")
        print(f"  Verified:     {m_verified}/{m_total} ({m_verified/m_total*100:.1f}%)")
        print(f"  New correct:  {m_verified - m_exact}")

        # By variation
        for var in ['node_deletion', 'edge_deletion']:
            var_df = model_df[model_df['variation'] == var]
            v_total = len(var_df)
            v_exact = var_df['is_correct_exact'].sum()
            v_verified = (var_df['llm_verified'] == 'correct').sum()
            print(f"    {var}: exact={v_exact}/{v_total}, verified={v_verified}/{v_total}")

            summary_rows.append({
                'model': model,
                'variation': var,
                'total': v_total,
                'exact_correct': int(v_exact),
                'verified_correct': int(v_verified),
                'exact_accuracy': round(v_exact/v_total*100, 1) if v_total > 0 else 0,
                'verified_accuracy': round(v_verified/v_total*100, 1) if v_total > 0 else 0,
            })

    # Show newly found correct answers
    newly_correct = df[(df['llm_verified'] == 'correct') & (df['is_correct_exact'] == False)]
    if len(newly_correct) > 0:
        print(f"\n{'='*80}")
        print(f"NEWLY FOUND CORRECT ANSWERS ({len(newly_correct)})")
        print(f"(Missed by exact match, caught by verification)")
        print(f"{'='*80}")
        for _, row in newly_correct.iterrows():
            print(f"  {row['model']} | Ex {row['example_id']} | {row['variation']}")
            print(f"    Correct:   {row['correct_answer']}")
            print(f"    Predicted: {row['predicted_answer']}")
            print(f"    Method:    {row['verify_method']}")
            print()

    # Save results
    if output_path is None:
        input_p = Path(input_path)
        output_path = input_p.parent / f"{input_p.stem}_verified.csv"

    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved verified results: {output_path}")

    # Save summary
    summary_df = pd.DataFrame(summary_rows)
    summary_path = Path(output_path).parent / f"{Path(output_path).stem}_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"✓ Saved summary: {summary_path}")

    return df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify_math_answers.py <input_csv> [output_csv]")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = sys.argv[2] if len(sys.argv) > 2 else None
    verify_csv(input_csv, output_csv)
