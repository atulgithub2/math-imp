from datasets import load_dataset  # type: ignore
import os
import json
import re
import subprocess
import tempfile
import argparse
import boto3  # type: ignore

# =============================================================================
# CONFIGURATION
# =============================================================================

AWS_REGION = "us-east-1"
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "YOUR_AWS_ACCESS_KEY_HERE")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "YOUR_AWS_SECRET_KEY_HERE")
MODEL_NAME = "us.anthropic.claude-opus-4-6-v1"  # overridden by --model arg
ANSWER_COL = "answer"  # overridden by --answer-col arg

# =============================================================================
# LOAD DATASET (configured via command-line args in main)
# =============================================================================

# Dataset will be loaded in main() based on --split and --level arguments
dataset = None

# =============================================================================
# AWS BEDROCK CLIENT SETUP
# =============================================================================

from botocore.config import Config  # type: ignore

config = Config(
    read_timeout=300,  # 5 minutes
    connect_timeout=60,
    retries={'max_attempts': 3, 'mode': 'adaptive'}
)

bedrock_client = boto3.client(
    service_name='bedrock-runtime',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    config=config
)


def call_claude(prompt: str, system_prompt: str = "", max_retries: int = 3) -> str:
    """Send a prompt to Claude Opus 4.5 via AWS Bedrock with retry logic."""
    import time
    from botocore.exceptions import ReadTimeoutError, ClientError  # type: ignore

    messages = [{"role": "user", "content": prompt}]

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": messages
    }

    if system_prompt:
        request_body["system"] = system_prompt

    for attempt in range(max_retries):
        try:
            response = bedrock_client.invoke_model(
                modelId=MODEL_NAME,
                body=json.dumps(request_body)
            )
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        except ReadTimeoutError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"    ⚠ Timeout error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise
        except ClientError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"    ⚠ Client error: {e}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                raise


# =============================================================================
# PIPELINE OVERVIEW (Based on Flowchart)
# =============================================================================
#
# PHASE 1: CODE GENERATION
#   - Call 1: Generate code + DAG from problem (not hardcoded!)
#   - Code Verified? → If No, retry up to 5x with errors
#
# PHASE 2: IMPOSSIBILITY
#   - Call 2: Generate 2 variations (Node Deletion, Edge Deletion)
#   - Receive Structured Feedback
#   - Run Modified Code
#   - Code Errors? → If No, regenerate (up to max_retries)
#
# PHASE 3: FINAL VERIFICATION
#   - Call 3: Solvability + Similarity
#   - Check 1: Obviousness/Impossibility >= 7 (scale 1-10)
#   - Check 2: Similarity >= 7 (scale 1-10)
#   - If either check fails → Append to Failure History, Regenerate (up to 5 attempts)
#   - Success if both checks >= 7
#
# =============================================================================
# STEP 1: PHASE 1 - GENERATE CODE FROM QUESTION + SOLUTION
# =============================================================================

def generate_code(question: str, solution: str, final_answer: str) -> str:
    """Generate Python code that computes the answer from question + solution.

    IMPORTANT: The code should NOT be hardcoded - it should algorithmically solve the problem.
    """

    system_prompt = """You are an expert mathematician and programmer.
Given a math olympiad problem and its solution, write Python code that computes the final answer.

CRITICAL REQUIREMENTS - NEVER HARDCODE:
1. NEVER hardcode the answer - the code must SOLVE the problem through computation
2. PREFER computational approaches: loops, iterations, functions, algorithms
3. If full computation isn't possible, algebraic manipulation is acceptable (e.g., sympy equations)
4. The code should derive the answer step-by-step, not just assign and print a constant
5. Print ONLY the final answer at the end (no extra text, no labels)
6. Be self-contained (no external dependencies except math, numpy, sympy if needed)
7. Use print() to output the final answer
8. Output should match the expected format - if answer is "2", print 2. If answer is "$\\frac{1}{2}$", print "1/2" or 0.5

APPROACH HIERARCHY (best to acceptable):
1. BEST - Computational/Iterative: Use loops, searches, algorithms to compute the answer
   Example: Finding values through iteration, counting, simulation
2. GOOD - Functional: Use functions to break down the problem and compute results
   Example: Define helper functions, recursion, mathematical computations
3. ACCEPTABLE - Algebraic: Use symbolic math libraries when direct computation isn't feasible
   Example: Using sympy to solve equations symbolically
4. NEVER ACCEPTABLE - Hardcoded: Directly assigning the answer value

BAD EXAMPLES (NEVER do these):
```python
# WRONG - Direct hardcoding:
answer = 42
print(answer)

# WRONG - Hardcoding disguised as code:
result = 306  # This is the answer
print(result)

# WRONG - Trivial computation that's really hardcoding:
x = 10
y = 20
print(x + y)  # When the problem asks for sum of specific numbers
```

GOOD EXAMPLES (Do these):
```python
# BEST - Iterative/computational approach:
def find_smallest_n(max_threshold, consecutive_count):
    n = 1
    while True:
        product = 1
        for i in range(consecutive_count):
            product *= (n + i)
        if product > max_threshold:
            return n
        n += 1

N_max = 5000
count = 17
result = find_smallest_n(N_max, count)
print(result)

# GOOD - Using sympy for algebraic problems:
from sympy import symbols, solve, sqrt
r, theta = symbols('r theta', real=True, positive=True)
x, y = 0, 3
equations = [r * cos(theta) - x, r * sin(theta) - y]
solution = solve(equations, [r, theta])
print(f"({solution[r]}, {solution[theta]})")

# ACCEPTABLE - Algebraic manipulation when direct computation is hard:
import math
# Given point in rectangular coordinates
x, y = 0, 3
# Compute r and theta from first principles
r = math.sqrt(x**2 + y**2)
if x == 0:
    theta = math.pi/2 if y > 0 else 3*math.pi/2
else:
    theta = math.atan2(y, x)
print(f"({r}, {theta})")
```

Return ONLY the Python code wrapped in ```python ... ``` tags."""

    prompt = f"""## Problem:
{question}

## Solution:
{solution}

## Expected Answer Format:
{final_answer}

Generate Python code that ALGORITHMICALLY solves this problem (not hardcoded). The code should implement the solution step-by-step and compute the answer."""

    response = call_claude(prompt, system_prompt)

    # Extract code from response
    code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return response.strip()


# =============================================================================
# STEP 2: PHASE 1 - VERIFY CODE (RUN AND CHECK AGAINST GROUND TRUTH)
# =============================================================================

def run_code(code: str, timeout: int = 30) -> tuple[bool, str]:
    """Run Python code and return (success, output)."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        result = subprocess.run(
            ['python3', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        os.unlink(temp_file)

        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()

    except subprocess.TimeoutExpired:
        os.unlink(temp_file)
        return False, "TIMEOUT"
    except Exception as e:
        return False, str(e)


def normalize_expression(expr: str) -> str:
    """Normalize a mathematical expression for comparison."""
    # Remove whitespace
    expr = re.sub(r'\s+', '', expr)
    # Remove LaTeX delimiters
    expr = expr.replace('$', '').replace('\\(', '').replace('\\)', '')
    # Convert LaTeX to Python-like syntax
    expr = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', expr)
    expr = re.sub(r'\^{([^}]+)}', r'^\1', expr)  # x^{2} -> x^2
    expr = re.sub(r'\^(\d+)', r'^\1', expr)  # already x^2
    expr = re.sub(r'\\cdot', '*', expr)
    expr = re.sub(r'\\times', '*', expr)
    expr = re.sub(r'\\sqrt\{([^}]+)\}', r'sqrt(\1)', expr)
    # Remove remaining backslashes (LaTeX commands)
    expr = re.sub(r'\\[a-zA-Z]+', '', expr)
    # Normalize common variations
    expr = expr.replace('**', '^')
    expr = expr.replace(' ', '')
    expr = expr.lower()
    return expr


def llm_verify_equivalence(output: str, expected: str) -> bool:
    """Use LLM to verify if two mathematical expressions are equivalent."""
    try:
        prompt = f"""Are these two mathematical expressions equivalent? Answer ONLY "yes" or "no".

Expression 1: {output}
Expression 2: {expected}

Consider:
- LaTeX formatting vs plain text (e.g., $\\frac{{1}}{{2}}$ = 1/2)
- Different notations (e.g., 2^1009 = $2^{{1009}}$)
- Algebraically equivalent forms

Answer (yes/no):"""

        response = call_claude(prompt, "You are a math expert. Answer only 'yes' or 'no'.")
        return response.strip().lower().startswith('yes')
    except Exception:
        return False


def verify_code(code: str, expected_answer: str) -> tuple[bool, str]:
    """Run code and check if output matches expected answer."""
    success, output = run_code(code)

    if not success:
        return False, f"Code failed: {output}"

    # Get the last line of output (in case there's debug output)
    output_lines = output.strip().split('\n')
    output_last = output_lines[-1].strip() if output_lines else ""
    output_normalized = output_last

    expected_normalized = expected_answer.strip()

    # Direct string match
    if output_normalized == expected_normalized:
        return True, output

    # Try numeric comparison
    try:
        if abs(float(output_normalized) - float(expected_normalized)) < 1e-6:
            return True, output
    except ValueError:
        pass

    # Try expression normalization
    norm_output = normalize_expression(output_normalized)
    norm_expected = normalize_expression(expected_normalized)
    if norm_output == norm_expected:
        return True, output

    # Try symbolic comparison using sympy (if available)
    try:
        from sympy import simplify, sympify  # type: ignore
        out_expr = sympify(output_normalized)
        exp_expr = sympify(expected_normalized)
        if simplify(out_expr - exp_expr) == 0:
            return True, output
    except Exception:
        pass

    # Last resort: use LLM to verify equivalence
    print(f"    Using LLM to verify: '{output_normalized}' vs '{expected_normalized}'")
    if llm_verify_equivalence(output_normalized, expected_normalized):
        print(f"    LLM confirmed equivalence!")
        return True, output

    return False, f"Mismatch: got '{output_normalized}', expected '{expected_normalized}'"


# =============================================================================
# STEP 3: PHASE 1 - CREATE DAG FROM QUESTION (NOT SOLUTION!)
# =============================================================================

def create_dag(question: str, solution: str, code: str) -> dict:
    """Create a DAG representation of the QUESTION (not the solution) as a computational graph.

    IMPORTANT: The DAG should represent the structure of the QUESTION/PROBLEM itself,
    including the given values, constraints, and relationships described in the problem.
    """

    system_prompt = """You are an expert at analyzing mathematical problems and representing them as computational DAGs (Directed Acyclic Graphs).

IMPORTANT: Create a DAG that represents the QUESTION/PROBLEM STRUCTURE, not the solution.
The DAG should capture:
- Given values and constraints from the problem statement
- Relationships and operations described in the problem
- The computational structure needed to solve it

Return the DAG in the format of this example:
{
    "nodes": [
        {"id": "n1", "type": "given", "value": 5000, "label": "N_max",
         "description": "Maximum threshold value 5000"},
        {"id": "n2", "type": "given", "value": 17, "label": "consecutive_count",
         "description": "Number of consecutive integers"},
        {"id": "n3", "type": "unknown", "value": null, "label": "N",
         "description": "Smallest positive integer to find"},
        {"id": "n4", "type": "derived_info", "value": null, "label": "product",
         "description": "Product of consecutive integers"},
        {"id": "n5", "type": "relationship", "value": null, "label": "product_exceeds",
         "description": "Constraint: product > N_max"},
        ...
    ],
    "edges": [
        {"from": "n2", "to": "n4", "relationship": "determines",
         "description": "Consecutive count determines product calculation"},
        {"from": "n3", "to": "n4", "relationship": "determines",
         "description": "Starting value determines which integers to multiply"},
        {"from": "n4", "to": "n5", "relationship": "relates_to",
         "description": "Product is compared against threshold"},
        ...
    ],
    "unknowns": ["n3"],
    "givens": ["n1", "n2"],
    "constraints": ["n5"]
}

Node types:
- "given": Values explicitly given in the problem (known values)
- "unknown": Variables to be found/computed (what we're solving for)
- "derived_info": Computed intermediate values
- "relationship": Mathematical rules/formulas/relationships
- "constraint": Problem restrictions and conditions

Node fields (ALL REQUIRED):
- "id": Unique identifier (e.g., "n1", "n2")
- "type": One of the node types above
- "value": Concrete value if known, null otherwise
- "label": Short machine-readable label
- "description": Human-readable description of the node

Edge relationship types:
- "determines": Source directly computes or defines target
- "constrains": Source limits possible values of target
- "relates_to": Source is involved in computing target
- "defines_domain": Source specifies valid range for target
- "references": Target depends on source's value

Edge fields (ALL REQUIRED):
- "from": Source node ID
- "to": Target node ID
- "relationship": Type of relationship (from list above)
- "description": Explanation of the connection

Metadata fields (REQUIRED):
- "unknowns": List of node IDs representing unknowns to solve for
- "givens": List of node IDs with known values from problem
- "constraints": List of node IDs representing constraints/relationships

Return ONLY the JSON wrapped in ```json ... ``` tags."""

    prompt = f"""## Problem:
{question}

## Solution (for reference):
{solution}

## Code Implementation (for reference):
```python
{code}
```

Create a computational DAG that represents the PROBLEM STRUCTURE (not the solution).
Focus on the given values, constraints, and relationships described in the problem statement itself.
The DAG should show what needs to be computed to solve the problem."""

    response = call_claude(prompt, system_prompt)

    # Extract JSON from response
    json_match = re.search(r'```json\n(.*?)```', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse DAG JSON", "raw": json_match.group(1).strip()}
    return {"error": "No JSON found in response", "raw": response.strip()}


# =============================================================================
# STEP 4: PHASE 2 - MODIFY DAG, CODE, AND PROBLEM TO MAKE IT UNSOLVABLE
# =============================================================================

MODIFICATION_METHODS = {
    "variation_1_node_deletion": {
        "name": "Node Deletion (Variation 1)",
        "description": """Delete a critical numerical value (given node) that CANNOT be deduced from remaining information.

CRITICAL: The deleted information must NOT be reasonably deducible. It should BREAK the question's solvability.

Real examples from dataset:
✓ GOOD: "Total time is 4 hours" → "Total time is some amount" (cannot deduce 4)
✓ GOOD: "17_b divides 97_b" → "17_b divides a certain number" (cannot deduce 97_b)
✗ BAD: Remove a value that can be computed from other givens

Remove the node and its connecting edges from DAG.""",
        "code_behavior": "The code should NATURALLY error (NameError for undefined variable) when it tries to use the deleted value. Do NOT artificially make it error."
    },
    "variation_2_edge_deletion": {
        "name": "Edge Deletion (Variation 2)",
        "description": """Remove or make ambiguous a critical relationship/constraint that CANNOT be reconstructed.

CRITICAL: Change given nodes to unknown nodes when their constraint edges are removed.

Real examples from dataset:
✓ GOOD: Remove edges connecting time values to speed constraints → times become unknowns
✓ GOOD: Remove divisibility constraint edge → relationship becomes unspecified
✗ BAD: Remove an edge where the relationship is obvious from context

Change node types from 'given' to 'unknown' when appropriate.""",
        "code_behavior": "The code should NATURALLY error when it tries to use values that are now unknown. Do NOT artificially make it error."
    }
}


def modify_to_unsolvable(question: str, solution: str, code: str, dag: dict, method: str, failure_history: list = None) -> dict:
    """Modify the DAG, code, and problem statement using a specific impossibility method.

    Args:
        failure_history: List of previous failed attempts with scores and feedback
    """

    if method not in MODIFICATION_METHODS:
        raise ValueError(f"Unknown method: {method}. Must be one of {list(MODIFICATION_METHODS.keys())}")

    method_info = MODIFICATION_METHODS[method]

    # Build feedback from previous failures
    feedback_section = ""
    if failure_history:
        feedback_section = f"""
## CRITICAL: LEARN FROM PREVIOUS FAILURES

You have made {len(failure_history)} previous attempt(s) that FAILED Phase 3 verification.
Each attempt is scored on TWO criteria (both must pass):

REQUIRED SCORES:
- Similarity Score: >= 5/10 (how similar to original problem)
- Impossibility Score: >= 7/10 (how impossible to solve)

PREVIOUS FAILED ATTEMPTS:
"""
        for i, failure in enumerate(failure_history, 1):
            if failure.get("failure_type") == "phase3_llm_check":
                sim_score = failure.get("similarity_score", 0)
                imp_score = failure.get("impossibility_score", 0)
                sim_target = failure.get("target_similarity_score", 5)
                imp_target = failure.get("target_impossibility_score", 7)

                feedback_section += f"""
Attempt {failure.get('attempt', i)}:
  ✗ Similarity: {sim_score}/10 (needed >= {sim_target}/10) {"✓ PASS" if sim_score >= sim_target else "✗ FAIL"}
  ✗ Impossibility: {imp_score}/10 (needed >= {imp_target}/10) {"✓ PASS" if imp_score >= imp_target else "✗ FAIL"}

  Why Similarity Failed: {failure.get('similarity_explanation', 'N/A')}

  Why Impossibility Failed: {failure.get('impossibility_explanation', 'N/A')}

  What you need to fix:
  - If Similarity too LOW: Make the problem MORE similar to the original (same structure, just missing key info)
  - If Similarity too HIGH: This is usually NOT the problem
  - If Impossibility too LOW: Make it MORE impossible - specifically:
      * Remove MORE critical information so NO unique solution exists
      * Make it more ambiguous so INFINITE solutions are possible
      * Ensure missing info CANNOT be deduced from context
  - If Impossibility too HIGH: Make it LESS impossible (remove less info, keep more structure)
"""

        feedback_section += f"""
IMPORTANT: Adjust your approach based on the feedback above.
Our goal is to create problems that are IMPOSSIBLE to solve, meaning:
- Either NO solution exists (contradictory or insufficient information)
- Or INFINITE solutions exist (too many unknowns, infinite valid answers)
- The key is that the missing information CANNOT be reasonably deduced

If impossibility score is too LOW (< 7):
  → Remove MORE critical information
  → Make the problem have either NO solution or INFINITE solutions
  → Ensure any attempt to solve requires arbitrary guesses

If similarity score is too LOW (< 5):
  → Keep the problem MORE similar to the original structure
  → Only remove/change the minimum needed to make it impossible
"""

    system_prompt = f"""You are an expert at creating mathematically impossible problems.
{feedback_section}

Given a solvable math problem with its solution, code, and computational DAG, your task is to modify all three to create an UNSOLVABLE version using the "{method_info['name']}" method.

The DAG uses:
- Nodes = values (numerical values, givens, constants, variables)
- Edges = operations/functions/relationships between values

## MODIFICATION METHOD: {method_info['name']}

{method_info['description']}

Expected code behavior: {method_info['code_behavior']}

CRITICAL REQUIREMENTS:
1. The deletion MUST make the question TRULY IMPOSSIBLE - not just harder
2. The deleted information CANNOT be reasonably deducible from remaining information
3. Analyze the DAG to find nodes/edges whose deletion BREAKS solvability
4. The modified problem should look valid at first glance but be fundamentally unsolvable

CODE GENERATION:
- Do NOT purposefully make the code error
- The code should simply reflect the modified problem faithfully
- If you removed "N_max = 5000", just reference N_max without defining it
- If the question is truly impossible, the code will NATURALLY error (NameError, undefined variable)
- Example: Original code `N_max = 5000` → Modified code uses `N_max` directly → Natural NameError
- DO NOT write artificial errors like `raise NameError("M not defined")`

Return your response in this exact JSON format:
{{
    "method_used": "{method}",
    "targeted_nodes": ["list of node IDs that were modified"],
    "targeted_edges": ["list of edge descriptions that were modified"],
    "modified_problem": "The new problem statement",
    "modified_dag": {{
        "nodes": [{{"id": "...", "type": "...", "value": ..., "label": "...", "description": "..."}}],
        "edges": [{{"from": "...", "to": "...", "relationship": "...", "description": "..."}}],
        "unknowns": ["..."],
        "givens": ["..."],
        "constraints": ["..."]
    }},
    "modified_code": "Python code that will error when run",
    "expected_error": "The type of error expected (e.g., NameError, AssertionError)",
    "modification_summary": "What was changed and why it makes the problem unsolvable"
}}

Return ONLY the JSON wrapped in ```json ... ``` tags."""

    # Convert dag dict to JSON string for the prompt
    dag_str = json.dumps(dag, indent=2)

    prompt = f"""## Original Problem:
{question}

## Original Solution:
{solution}

## Original Code:
```python
{code}
```

## Original DAG:
```json
{dag_str}
```

Apply the "{method_info['name']}" method to make this problem unsolvable.
Analyze the DAG to find the best target for this modification method.
The modified code must ERROR OUT when run."""

    response = call_claude(prompt, system_prompt)

    # Extract JSON from response
    json_match = re.search(r'```json\n(.*?)```', response, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1).strip())
            result["raw_llm_response"] = response  # Store raw response
            return result
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": response, "raw_llm_response": response}
    return {"error": "No JSON found", "raw": response, "raw_llm_response": response}


def generate_all_variations(question: str, solution: str, answer: str, code: str, dag: dict, max_retries: int = 5, stop_on_first: bool = False) -> dict:
    """Generate 2 variations of the impossible problem with retries.

    Phase 2: A modification is successful if the modified code ERRORS OUT.
    Phase 3: The modified question must pass similarity (>=7) and impossibility (>=7) checks.

    If stop_on_first=True, stops after first successful variation.
    If stop_on_first=False (default), tries both variations.
    """
    variations = {}
    first_success_method = None

    for method in MODIFICATION_METHODS.keys():
        print(f"    Generating {method} variation...")

        method_result = {
            "success": False,
            "attempts": 0,
            "all_attempts": [],
            "failure_history": []
        }

        for attempt in range(max_retries):
            method_result["attempts"] = attempt + 1
            print(f"      Attempt {attempt + 1}/{max_retries}...")

            modified = modify_to_unsolvable(question, solution, code, dag, method, method_result["failure_history"])

            if "error" in modified:
                print(f"      Generation error: {modified.get('error', 'unknown')}")
                method_result["all_attempts"].append({
                    "attempt": attempt + 1,
                    "error": modified.get("error", "unknown")
                })
                continue

            # PHASE 2: Verify the modified code ERRORS OUT (impossible problems must error)
            modified_code = modified.get("modified_code", "")
            success, output = run_code(modified_code)

            modified["code_verification"] = {
                "code_errored": not success,
                "output": output[:500] if output else ""
            }

            if success:
                # Code didn't error - retry
                print(f"      ✗ Code ran without error (output: {output[:50]}), retrying...")
                method_result["all_attempts"].append({
                    "attempt": attempt + 1,
                    "phase": "code_verification",
                    "code_ran_successfully": True,
                    "output": output[:200]
                })
                method_result["failure_history"].append({
                    "attempt": attempt + 1,
                    "failure_type": "phase2_code_didnt_error",
                    "failure_reason": "Code did not error when it should have",
                    "output": output[:200],
                    "raw_llm_response": modified.get("raw_llm_response", "")
                })
                continue

            # Code errored - good! Now do Phase 3 verification
            print(f"      ✓ Code errored: {output[:80]}...")
            print(f"      Running Phase 3: Similarity + Impossibility check...")

            # PHASE 3: Final verification with LLM check
            modified_question = modified.get("modified_problem", "")
            verification = verify_impossible_question(
                question,
                modified_question,
                answer,
                method_result["failure_history"]
            )

            modified["phase3_verification"] = verification

            similarity_score = verification.get("similarity_score", 0)
            impossibility_score = verification.get("impossibility_score", 0)
            passes = verification.get("passes", False)

            print(f"        Similarity: {similarity_score}/10 (need >= 5)")
            print(f"        Impossibility: {impossibility_score}/10 (need >= 7)")

            if passes:
                # Both checks passed!
                print(f"      ✓✓ SUCCESS! Both checks passed!")
                method_result["success"] = True
                method_result["result"] = modified
                break
            else:
                # Failed Phase 3 - add to failure history and retry
                failure_reason = []
                if similarity_score < 5:
                    failure_reason.append(f"Similarity too low: {similarity_score}/10")
                if impossibility_score < 7:
                    failure_reason.append(f"Impossibility too low: {impossibility_score}/10")

                print(f"      ✗ Phase 3 failed: {'; '.join(failure_reason)}")

                method_result["all_attempts"].append({
                    "attempt": attempt + 1,
                    "phase": "phase3_verification",
                    "similarity_score": similarity_score,
                    "impossibility_score": impossibility_score,
                    "failure_reason": failure_reason
                })

                method_result["failure_history"].append({
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
                    "raw_llm_response": verification.get("raw_llm_response", "")
                })

        if not method_result["success"]:
            print(f"      ✗ Failed after {max_retries} attempts")
            # Save the last attempt result if we have one
            if method_result["all_attempts"]:
                method_result["result"] = {"error": "All attempts failed", "last_attempt": method_result["all_attempts"][-1]}
            else:
                method_result["result"] = {"error": "No attempts made"}

        variations[method] = method_result

        # Stop after first success if requested
        if stop_on_first and method_result["success"]:
            first_success_method = method
            print(f"    ✓ Got first successful variation ({method}), moving to next problem...")
            break

    return variations


# =============================================================================
# STEP 5: PHASE 3 - FINAL VERIFICATION (SIMILARITY + IMPOSSIBILITY CHECK)
# =============================================================================

def verify_impossible_question(original_question: str, modified_question: str, original_answer: str, failure_history: list = None) -> dict:
    """Phase 3: Verify the modified question with similarity and impossibility checks.

    Returns a dict with:
    - similarity_score: 1-10 (accept if >= 7)
    - impossibility_score: 1-10 (accept if >= 7, meaning obviously impossible)
    - passes: True if both scores >= 7
    - explanation: Reasoning for the scores
    """

    if failure_history is None:
        failure_history = []

    failure_context = ""
    if failure_history:
        failure_context = f"""
## Previous Failed Attempts:
{json.dumps(failure_history, indent=2)}

Learn from these failures to provide accurate scores.
"""

    system_prompt = """You are an expert at evaluating mathematical problems for similarity and solvability.

Your task is to evaluate a modified (impossible) math problem against the original problem.
You must provide TWO scores:

1. **Similarity Score (1-10)**: How similar is the modified problem to the original?
   - 10 = Nearly identical problem structure, just missing one key piece
   - 7-9 = Very similar, same type of problem, same mathematical concepts
   - 5-6 = Somewhat similar, same general approach
   - 3-4 = Somewhat different approach or concepts
   - 1-2 = Completely different problem
   - ACCEPT if score >= 5

2. **Impossibility Score (1-10)**: How impossible/unsolvable is the modified problem?

   CRITICAL EVALUATION PROCESS:
   a) First, ATTEMPT TO SOLVE the modified question yourself
   b) Try making ALL assumptions needed to get to the correct answer
   c) Compare your attempt with the original problem and answer
   d) Track what assumptions you had to make
   e) Determine if those assumptions are reasonable/deducible or arbitrary/impossible

   SCORING:
   - 10 = Completely impossible, no answer can be made (no assumptions help)
   - 8-9 = Completely impossible, infinite answers possible (each assumption gives different answer)
   - 7 = Completely impossible, many hard/arbitrary assumptions required (no basis in problem)
   - 4-6 = Impossible but small/reasonable assumptions can solve (educated guesses possible)
   - 1-3 = Solvable by making deducible/reasonable assumptions (assumptions follow logically)
   - ACCEPT if score >= 7 (we aim to create truly impossible questions)

   Example: If original says "time is 4 hours" and modified says "time is some amount",
   trying to solve requires guessing 3h? 5h? 2.5h? Each gives different answer. Score: 9

Return your evaluation in this exact JSON format:
{
    "solve_attempt": "Your attempt to solve the modified problem, showing all assumptions you had to make",
    "similarity_score": <1-10>,
    "impossibility_score": <1-10>,
    "similarity_explanation": "Why you gave this similarity score",
    "impossibility_explanation": "Why you gave this impossibility score (based on your solve attempt)",
    "passes": <true if both scores >= 7, false otherwise>
}

Return ONLY the JSON wrapped in ```json ... ``` tags."""

    prompt = f"""## Original Problem:
{original_question}

## Original Answer:
{original_answer}

## Modified (Impossible) Problem:
{modified_question}

{failure_context}

Evaluate the modified problem:

STEP 1 - ATTEMPT TO SOLVE THE MODIFIED PROBLEM:
- Try to solve the modified problem yourself
- Make any assumptions you need to get to an answer
- Compare your answer(s) with the original answer: {original_answer}
- Note what assumptions you had to make

STEP 2 - SCORE THE PROBLEM:
1. Similarity Score (1-10): How similar to the original? Accept if >= 5
2. Impossibility Score (1-10): Based on your solving attempt, how impossible is it? Accept if >= 7
   - Did you need to make arbitrary assumptions?
   - Could you get to the correct answer {original_answer} without guessing?
   - Are there infinite possible answers or no answer at all?

Provide both scores and determine if it passes (both scores >= 7)."""

    response = call_claude(prompt, system_prompt)

    # Extract JSON from response
    json_match = re.search(r'```json\n(.*?)```', response, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1).strip())
            # Ensure passes is correctly computed
            result["passes"] = (
                result.get("similarity_score", 0) >= 5 and
                result.get("impossibility_score", 0) >= 7
            )
            result["raw_llm_response"] = response  # Store raw response
            return result
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse JSON",
                "raw": response,
                "raw_llm_response": response,
                "passes": False,
                "similarity_score": 0,
                "impossibility_score": 0,
                "similarity_explanation": "Failed to parse response",
                "impossibility_explanation": "Failed to parse response",
                "solve_attempt": ""
            }

    return {
        "error": "No JSON found in response",
        "raw": response,
        "raw_llm_response": response,
        "passes": False,
        "similarity_score": 0,
        "impossibility_score": 0,
        "similarity_explanation": "Failed to parse response",
        "impossibility_explanation": "Failed to parse response",
        "solve_attempt": ""
    }


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def process_problem(problem_data: dict, max_retries: int = 5, stop_on_first: bool = False) -> dict:
    """Process a single problem through the entire pipeline with 2 variation methods.

    Args:
        problem_data: Dataset row with problem, answer fields
        max_retries: Max retries per modification method
        stop_on_first: If True, stop after first successful variation
    """

    # Dataset fields (answer column configurable via --answer-col)
    question = problem_data['problem']
    solution = problem_data.get('solution', "")  # AIME may not have solutions
    if isinstance(solution, list):
        solution = solution[0] if solution else ""
    final_answer = str(problem_data[ANSWER_COL])  # column name set by --answer-col

    # OlympiadBench dataset fields (for reference)
    # question = problem_data['question']
    # solution = problem_data['solution'][0] if problem_data['solution'] else ""
    # final_answer = problem_data['final_answer'][0] if problem_data['final_answer'] else ""

    result = {
        "original_question": question,
        "original_solution": solution,
        "original_answer": final_answer,
        "success": False,
        "variations": {}
    }

    # PHASE 1: Generate code and verify (with retries)
    print("  [PHASE 1] Generating and verifying code (not hardcoded!)...")
    code = None
    is_valid = False
    code_attempts = []

    for attempt in range(max_retries):
        print(f"    Attempt {attempt + 1}/{max_retries}...")
        generated_code = generate_code(question, solution, final_answer)
        is_valid, verify_output = verify_code(generated_code, final_answer)

        code_attempts.append({
            "attempt": attempt + 1,
            "valid": is_valid,
            "output": verify_output[:200] if verify_output else ""
        })

        if is_valid:
            code = generated_code
            print(f"    ✓ Code verified successfully on attempt {attempt + 1}")
            break
        else:
            print(f"    ✗ Verification failed: {verify_output[:80]}...")

    result["code_generation_attempts"] = code_attempts
    result["generated_code"] = code if code else generated_code  # Save last attempt even if failed
    result["code_verification"] = {"valid": is_valid, "attempts": len(code_attempts)}

    if not is_valid:
        print(f"  ✗ Phase 1 failed: Code generation failed after {max_retries} attempts")
        result["error"] = "Phase 1: Code generation failed"
        return result

    # PHASE 1 (continued): Create DAG from question
    print("  [PHASE 1] Creating DAG from question structure...")
    dag = create_dag(question, solution, code)
    result["dag"] = dag

    # PHASE 2 & 3: Generate 2 variations with full verification pipeline
    print("  [PHASE 2 & 3] Generating 2 impossible variations...")
    print("    - Variation 1: Node deletion")
    print("    - Variation 2: Edge deletion")
    print("    - Phase 2: Modified code must error")
    print("    - Phase 3: Similarity >= 7 AND Impossibility >= 7")
    variations = generate_all_variations(question, solution, final_answer, code, dag, max_retries, stop_on_first)
    result["variations"] = variations

    # Count successes (variations that passed both Phase 2 and Phase 3)
    successful_methods = []
    total_modification_attempts = 0
    total_phase3_checks = 0
    phase3_stats = []

    for method, variation in variations.items():
        attempts = variation.get("attempts", 0)
        total_modification_attempts += attempts

        # Count Phase 3 checks: successful attempt (1) + failed Phase 3 attempts
        if variation.get("success", False):
            # Success means we did at least one Phase 3 check (the successful one)
            total_phase3_checks += 1
            # Plus any previous Phase 3 failures for this method
            phase3_failures = sum(1 for a in variation.get("all_attempts", [])
                                if a.get("phase") == "phase3_verification")
            total_phase3_checks += phase3_failures

            # Extract Phase 3 scores from successful result
            phase3_data = variation.get("result", {}).get("phase3_verification", {})
            sim_score = phase3_data.get("similarity_score", 0)
            imp_score = phase3_data.get("impossibility_score", 0)
            successful_methods.append(method)
            print(f"    ✓ {method}: Success (attempt {attempts}) - Sim: {sim_score}/10, Imp: {imp_score}/10")
            phase3_stats.append({
                "method": method,
                "similarity_score": sim_score,
                "impossibility_score": imp_score
            })
        else:
            # Count any Phase 3 checks that were done before failing
            phase3_count = sum(1 for a in variation.get("all_attempts", [])
                             if a.get("phase") == "phase3_verification")
            total_phase3_checks += phase3_count
            print(f"    ✗ {method}: Failed after {attempts} attempts")

    # Total API calls: code gen (1) + DAG (1) + modification attempts + Phase 3 verification checks
    result["total_api_calls"] = 2 + total_modification_attempts + total_phase3_checks
    result["successful_methods"] = successful_methods
    result["success"] = len(successful_methods) == 2  # Both variations must work
    result["success_count"] = len(successful_methods)
    result["phase3_stats"] = phase3_stats

    return result


# =============================================================================
# EXTRACT CLEAN RESULTS
# =============================================================================

def extract_clean_results_from_dir(results_dir: str = "results", clean_dir: str = "clean_results") -> dict:
    """Extract clean results from full results directory.

    Creates simplified JSON files containing only:
    - original_question
    - original_answer
    - node_variation (modified problem from variation 1)
    - edge_variation (modified problem from variation 2)
    - success
    - index

    Returns summary statistics.
    """
    import glob

    # Create clean results directory
    os.makedirs(clean_dir, exist_ok=True)

    # Find all problem files
    problem_files = sorted(glob.glob(os.path.join(results_dir, "problem_*.json")))

    if not problem_files:
        print(f"No problem files found in {results_dir}/")
        return {"total": 0, "successful": 0, "partial": 0, "failed": 0}

    print(f"Found {len(problem_files)} problem files")
    print(f"Extracting clean results to {clean_dir}/\n")

    successful_count = 0
    partial_count = 0
    failed_count = 0

    for problem_file in problem_files:
        # Read full result
        with open(problem_file, 'r') as f:
            full_result = json.load(f)

        # Extract clean data
        clean_result = {
            "original_question": full_result.get("original_question", ""),
            "original_answer": full_result.get("original_answer", ""),
            "node_variation": None,
            "edge_variation": None,
            "success": full_result.get("success", False),
            "index": full_result.get("index", -1)
        }

        # Extract node variation (variation_1_node_deletion)
        variations = full_result.get("variations", {})
        node_var = variations.get("variation_1_node_deletion", {})
        if node_var.get("success"):
            clean_result["node_variation"] = node_var.get("result", {}).get("modified_problem", "")

        # Extract edge variation (variation_2_edge_deletion)
        edge_var = variations.get("variation_2_edge_deletion", {})
        if edge_var.get("success"):
            clean_result["edge_variation"] = edge_var.get("result", {}).get("modified_problem", "")

        # Count successes
        if clean_result["node_variation"] and clean_result["edge_variation"]:
            successful_count += 1
            status = "✓✓"
        elif clean_result["node_variation"] or clean_result["edge_variation"]:
            partial_count += 1
            status = "✓ "
        else:
            failed_count += 1
            status = "✗ "

        # Save clean result
        basename = os.path.basename(problem_file)
        clean_file = os.path.join(clean_dir, basename)
        with open(clean_file, 'w') as f:
            json.dump(clean_result, f, indent=2, ensure_ascii=False)

        print(f"{status} {basename} -> {clean_file}")

    print(f"\n{'='*60}")
    print("CLEAN RESULTS EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total problems: {len(problem_files)}")
    print(f"  Both variations successful: {successful_count}")
    print(f"  Partial success (1 variation): {partial_count}")
    print(f"  Failed (0 variations): {failed_count}")
    print(f"\nClean results saved to: {clean_dir}/")

    return {
        "total": len(problem_files),
        "successful": successful_count,
        "partial": partial_count,
        "failed": failed_count
    }


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate unsolvable math problems")
    parser.add_argument("--samples", type=int, default=1, help="Number of problems to process")
    parser.add_argument("--start", type=int, default=0, help="Starting index in dataset")
    parser.add_argument("--split", type=str, default="MATH", choices=["MATH", "AIME24", "AIME25"],
                        help="Dataset split to use from thulthula/math-bench (default: MATH)")
    parser.add_argument("--level", type=str, default="5",
                        help="Level to filter (e.g., '5' for Level 5, 'all' for all levels)")
    parser.add_argument("--output-dir", type=str, default="results", help="Output directory for individual result files")
    parser.add_argument("--max-retries", type=int, default=5, help="Max retries per modification method")
    parser.add_argument("--stop-on-first", action="store_true", help="Stop after first successful variation (default: try both variations)")
    parser.add_argument("--force", action="store_true", help="Re-process even if result file exists")
    parser.add_argument("--extract-clean", action="store_true", help="Extract clean results from existing results folder and exit")
    parser.add_argument("--clean-dir", type=str, default="clean_results", help="Output directory for clean results")
    parser.add_argument("--model", type=str, default="opus", choices=["sonnet", "opus"],
                        help="Model to use: sonnet or opus (default: opus)")
    parser.add_argument("--dataset", type=str, default=None,
                        help="Custom HuggingFace dataset (e.g., thulthula/AIME2026). Overrides --split/--level.")
    parser.add_argument("--answer-col", type=str, default="answer",
                        help="Column name for the answer field (default: answer)")
    args = parser.parse_args()

    # Set model name based on --model arg
    MODEL_NAMES = {
        "sonnet": "us.anthropic.claude-sonnet-4-6",
        "opus": "us.anthropic.claude-opus-4-6-v1",
    }
    MODEL_NAME = MODEL_NAMES[args.model]
    ANSWER_COL = args.answer_col
    print(f"Using model: {args.model} ({MODEL_NAME})")

    # Handle extract-clean mode
    if args.extract_clean:
        extract_clean_results_from_dir(args.output_dir, args.clean_dir)
        exit(0)

    # Load dataset based on arguments
    if args.dataset:
        print(f"Loading custom dataset: {args.dataset}")
        dataset_to_use = load_dataset(args.dataset, split="train")
        print(f"Total problems: {len(dataset_to_use)}")
    else:
        print(f"Loading dataset: thulthula/math-bench (split={args.split})")
        full_dataset = load_dataset("thulthula/math-bench", split=args.split)
        print(f"Total problems in {args.split}: {len(full_dataset)}")

        # Filter by level if specified
        if args.level.lower() == 'all':
            dataset_to_use = full_dataset
            print(f"Using all levels: {len(dataset_to_use)} problems")
        else:
            level_str = f"Level {args.level}"
            dataset_to_use = full_dataset.filter(lambda x: x.get('level') == level_str)
            print(f"Filtered to {level_str}: {len(dataset_to_use)} problems")

    print(f"Columns: {dataset_to_use.column_names}")
    print()

    # Create output directories if they don't exist
    os.makedirs(args.output_dir, exist_ok=True)
    clean_output_dir = os.path.join(os.path.dirname(args.output_dir) if args.output_dir != "results" else ".", "clean_results")
    os.makedirs(clean_output_dir, exist_ok=True)

    all_results = []
    skipped_count = 0
    processed_count = 0

    for i in range(args.start, args.start + args.samples):
        if i >= len(dataset_to_use):
            print(f"Index {i} out of range (dataset has {len(dataset_to_use)} items)")
            break

        # Check if already processed (for resume capability)
        output_file = os.path.join(args.output_dir, f"problem_{i}.json")
        if os.path.exists(output_file) and not args.force:
            print(f"\n[Skipping] Problem {i} - already processed ({output_file})")
            # Load existing result for summary
            with open(output_file, 'r') as f:
                existing_result = json.load(f)
                all_results.append(existing_result)
            skipped_count += 1
            continue

        print("\n" + "=" * 60)
        print(f"Processing problem {i} ({i - args.start + 1}/{args.samples})...")
        print("=" * 60)

        result = process_problem(dataset_to_use[i], max_retries=args.max_retries, stop_on_first=args.stop_on_first)
        result["index"] = i

        # Save immediately to individual file (full result)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"  Saved to: {output_file}")

        # Save clean result (just essential fields)
        clean_result = {
            "original_question": result.get("original_question", ""),
            "original_answer": result.get("original_answer", ""),
            "node_variation": None,
            "edge_variation": None,
            "success": result.get("success", False),
            "index": i
        }

        # Extract node variation (variation_1_node_deletion)
        variations = result.get("variations", {})
        node_var = variations.get("variation_1_node_deletion", {})
        if node_var.get("success"):
            clean_result["node_variation"] = node_var.get("result", {}).get("modified_problem", "")

        # Extract edge variation (variation_2_edge_deletion)
        edge_var = variations.get("variation_2_edge_deletion", {})
        if edge_var.get("success"):
            clean_result["edge_variation"] = edge_var.get("result", {}).get("modified_problem", "")

        clean_output_file = os.path.join(clean_output_dir, f"problem_{i}.json")
        with open(clean_output_file, 'w') as f:
            json.dump(clean_result, f, indent=2, ensure_ascii=False)
        print(f"  Clean result saved to: {clean_output_file}")

        all_results.append(result)
        processed_count += 1

        if 'success_count' in result:
            print(f"\n  Results: {result['success_count']}/2 variations successful")
            print(f"  Successful methods: {result.get('successful_methods', [])}")
        else:
            print(f"\n  Skipped variations (code verification failed)")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Count problems where both variations worked
    all_2_success = sum(1 for r in all_results if r.get('success_count', 0) == 2)
    at_least_1_success = sum(1 for r in all_results if r.get('success_count', 0) >= 1)

    # Count per-method success
    method_counts = {method: 0 for method in MODIFICATION_METHODS.keys()}
    for r in all_results:
        for method in r.get('successful_methods', []):
            method_counts[method] += 1

    print(f"Total problems: {len(all_results)}")
    print(f"  - Newly processed: {processed_count}")
    print(f"  - Skipped (already done): {skipped_count}")
    print(f"\nBoth variations successful: {all_2_success}")
    print(f"At least 1 variation successful: {at_least_1_success}")
    print(f"\nPer-variation success rates:")
    for method, count in method_counts.items():
        print(f"  {method}: {count}/{len(all_results)}")
    print(f"\nResults saved to: {args.output_dir}/problem_*.json")

    # Also save a combined summary file
    summary_file = os.path.join(args.output_dir, "summary.json")
    summary = {
        "total_problems": len(all_results),
        "newly_processed": processed_count,
        "skipped": skipped_count,
        "all_2_success": all_2_success,
        "at_least_1_success": at_least_1_success,
        "method_success_counts": method_counts,
        "problem_indices": [r.get("index") for r in all_results]
    }
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved to: {summary_file}")
