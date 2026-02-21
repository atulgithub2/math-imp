# DAG Pipeline Documentation

## Overview

This pipeline generates **impossible math problems** from solvable ones by creating a computational DAG (Directed Acyclic Graph) representation and systematically removing critical information to make the problem unsolvable.

The pipeline follows a 3-phase approach with rigorous verification at each step.

**Reference Dataset**: For examples of DAG structure, see HuggingFace dataset `thulthula/math-imp-bench7` (AIME DAG examples). This shows how nodes, edges, and variations are structured.

---

## Pipeline Flowchart

```
┌─────────────────────────────────────────────────────────────────┐
│                    Problem + Solution + Answer                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PHASE 1                                  │
│                     CODE GENERATION                              │
├─────────────────────────────────────────────────────────────────┤
│  • Call 1: Generate code + DAG from problem                      │
│  • Code MUST be algorithmic (not hardcoded)                      │
│  • DAG represents QUESTION structure (not solution)              │
│  • Code Verified? → If No, retry up to 5x                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │ yes
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PHASE 2                                  │
│                      IMPOSSIBILITY                               │
├─────────────────────────────────────────────────────────────────┤
│  • Call 2: Node/Edge Deletion                                    │
│  • Receive Structured Feedback                                   │
│  • Run Modified Code                                             │
│  • Code Errors? → If No, regenerate (3x or full)                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │ yes
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         PHASE 3                                  │
│                   FINAL VERIFICATION                             │
├─────────────────────────────────────────────────────────────────┤
│  • Call 3: Solvability + Similarity                              │
│  • Check 1: Impossibility Score >= 7 (scale 1-10)                │
│  • Check 2: Similarity Score >= 5 (scale 1-10)                   │
│  • Both pass? → SUCCESS                                          │
│  • Either fails? → Append to Failure History, Regenerate (5x)    │
└───────────────────────────────┬─────────────────────────────────┘
                                │ yes
                                ▼
                            SUCCESS ✓
```

---

## Phase Breakdown

### **PHASE 1: Code Generation & DAG Creation**

#### Goals:
1. Generate **algorithmic code** that solves the problem (no hardcoding!)
2. Create a **DAG** representing the **question structure** (not the solution)
3. Verify the code produces the correct answer

#### Key Requirements:
- **Code must be algorithmic**: The code should compute the answer through logical steps, not just `print(answer)`
- **DAG of question**: The DAG represents the problem's given values, constraints, and relationships described in the problem statement

#### Functions:
- `generate_code(question, solution, final_answer)` → Returns Python code
- `verify_code(code, expected_answer)` → Returns (is_valid, output)
- `create_dag(question, solution, code)` → Returns DAG dict

#### DAG Structure:

**Reference**: See HuggingFace dataset `thulthula/math-imp-bench7` (AIME DAG examples) for structure. Analyzed from actual examples in the dataset.

**Example 1: Aya's Walk Problem**
```json
{
    "nodes": [
        {"id": "n1", "type": "given", "value": 9, "label": "walk_distance",
         "description": "The distance Aya walks each morning is 9 kilometers"},
        {"id": "n2", "type": "given", "value": 4, "label": "total_time_slow",
         "description": "Total time at speed s is 4 hours (including coffee shop time)"},
        {"id": "n6", "type": "unknown", "value": null, "label": "base_speed_s",
         "description": "Aya's base walking speed s in km/h"},
        {"id": "n7", "type": "unknown", "value": null, "label": "coffee_time_t",
         "description": "Time t spent in coffee shop"},
        {"id": "n9", "type": "relationship", "value": null, "label": "time_distance_speed",
         "description": "Walking time = distance / speed"},
        {"id": "n10", "type": "constraint", "value": null, "label": "total_time_formula",
         "description": "Total time = walking time + coffee shop time t"}
    ],
    "edges": [
        {"from": "n1", "to": "n6", "relationship": "determines",
         "description": "Distance is used to calculate time given speed"},
        {"from": "n2", "to": "n6", "relationship": "constrains",
         "description": "Total time at speed s provides equation for s and t"},
        {"from": "n9", "to": "n10", "relationship": "defines_domain",
         "description": "Time-distance-speed relationship feeds into total time"}
    ],
    "unknowns": ["n6", "n7"],
    "givens": ["n1", "n2"],
    "constraints": ["n10"]
}
```

**Example 2: Base Divisibility Problem**
- Problem: "Find sum of all bases b>9 where 17_b divides 97_b"
- DAG has 8 nodes: base constraint (b>9), representations (17_b, 97_b), divisibility constraint
- Variation 1 removes 97_b node → "17_b divides a certain number"
- Variation 2 changes 97_b from given to unknown → cannot determine divisibility

**Node Types:**
- `given`: Values explicitly given in the problem (known values)
- `unknown`: Variables to be found/computed (what we're solving for)
- `derived_info`: Computed intermediate values
- `relationship`: Mathematical rules/formulas/relationships
- `constraint`: Problem restrictions and conditions

**Node Fields:**
- `id`: Unique node identifier (e.g., "n1", "n2")
- `type`: One of the node types above
- `value`: Concrete value if known, null otherwise
- `label`: Short machine-readable label
- `description`: Human-readable description of the node

**Edge Relationship Types:**
- `determines`: Source directly computes or defines target
- `constrains`: Source limits possible values of target
- `relates_to`: Source is involved in computing target
- `defines_domain`: Source specifies valid range for target
- `references`: Target depends on source's value

**Edge Fields:**
- `from`: Source node ID
- `to`: Target node ID
- `relationship`: Type of relationship (from list above)
- `description`: Explanation of the connection

**Metadata Fields:**
- `unknowns`: List of node IDs representing unknowns to solve for
- `givens`: List of node IDs with known values from problem
- `constraints`: List of node IDs representing constraints/relationships

---

### **PHASE 2: Impossibility Generation**

#### Goal:
Modify the problem, DAG, and code to make it **unsolvable** using one of two methods (generate 2 variations).

#### Modification Methods:

**CRITICAL REQUIREMENT**: The deletion MUST make the question truly impossible to solve. The deleted information should NOT be reasonably deducible from remaining information. The deletion should BREAK the question's solvability.

**Examples from actual dataset:**
- ✓ GOOD: Remove "4 hours" from time constraint → Cannot deduce this specific value
- ✓ GOOD: Remove "97_b" from divisibility → Cannot determine what number to divide
- ✗ BAD: Remove "sum of two numbers is 10" when you also give "the numbers are 3 and 7" → Sum is deducible
- ✗ BAD: Remove a value that can be computed from other givens

1. **Node Deletion (Variation 1)**
   - Delete a critical numerical value (given node) that CANNOT be deduced from remaining information
   - Replace with undefined variable or vague description
   - **Real example**: "Total time is 4 hours" → "Total time is some amount" (4 cannot be deduced)
   - **Real example**: "Find where 17_b divides 97_b" → "Find where 17_b divides a certain number"
   - Remove the node and its connecting edges from DAG
   - Expected: Problem becomes unsolvable, code naturally errors

2. **Edge Deletion (Variation 2)**
   - Remove or make ambiguous a critical relationship/constraint that CANNOT be reconstructed
   - Change given nodes to unknown nodes when edges are removed
   - **Real example**: Remove edges connecting time values to speed constraints → Times become unknowns
   - **Real example**: Remove divisibility constraint edge → Relationship becomes unspecified
   - Expected: Problem becomes underdetermined, code naturally errors

#### Modified Code Generation:

**CRITICAL**: Do NOT purposefully make the code error. The code should simply reflect the changes made to the problem.

**Correct approach:**
- If you removed "N_max = 5000", the code should reference N_max without defining it
- If you removed a time value, the code should try to use that variable
- The code should be a faithful translation of the modified (impossible) problem
- If the question is truly impossible, the code will NATURALLY error when it tries to use undefined variables or missing values

**Example:**
- Original code: `N_max = 5000; product = 1; ...`
- Modified problem: "N exceeds M" (M undefined)
- Modified code: `product = 1; ... if product > M:` ← Will naturally error with NameError
- DON'T write: `raise NameError("M not defined")` ← This is artificial!

#### Verification:
- **Modified code MUST error** when run (not just produce wrong answer)
- The error should be NATURAL (NameError, undefined variable) not artificial
- If code runs successfully → The modification didn't truly break the problem, retry

#### Functions:
- `modify_to_unsolvable(question, solution, code, dag, method)` → Returns modification dict
- `generate_all_variations(question, solution, code, dag, max_retries)` → Returns variations dict

---

### **PHASE 3: Final Verification**

#### Goal:
Ensure the modified problem is both **impossible** and **similar** to the original.

#### Two-Score System:

**1. Similarity Score (1-10)**
- How similar is the modified problem to the original?
- **10**: Nearly identical structure, just missing one key piece
- **7-9**: Very similar, same type of problem, same mathematical concepts
- **5-6**: Somewhat similar, same general approach
- **3-4**: Somewhat different approach or concepts
- **1-2**: Completely different problem
- **Threshold**: Must be >= 5

**2. Impossibility Score (1-10)**

**CRITICAL EVALUATION PROCESS**:
1. First, ATTEMPT TO SOLVE the modified question yourself
2. Try making ALL assumptions you need to get to the correct answer (compare with original answer)
3. Track what assumptions you had to make
4. Determine if those assumptions are reasonable/deducible or arbitrary/impossible

**Scoring:**
- **10**: Completely impossible, no answer can be made of this question (no amount of assumptions helps)
- **8-9**: Completely impossible, infinite answers possible (any assumption leads to different valid answer)
- **7**: Completely impossible, many hard/arbitrary assumptions are required (assumptions have no basis in the problem)
- **4-6**: Impossible but small/reasonable assumptions can solve this question (could make educated guesses)
- **1-3**: Solvable by making deducible/reasonable assumptions (assumptions follow logically from context)
- **Threshold**: Must be >= 7 (we aim to create truly impossible questions)

**Example Evaluation:**
- Original: "Time is 4 hours" → Answer: 17
- Modified: "Time is some amount"
- Attempt: "Let me assume time is 3 hours... no wait, 5 hours... or 2.5 hours..."
- Result: Each assumption gives completely different answer, NO way to deduce the correct value of 4
- Score: 9 (completely impossible, infinite answers possible)

#### Pass Criteria:
```
SUCCESS = (Similarity >= 5) AND (Impossibility >= 7)
```

If either check fails:
1. Append to **Failure History** with:
   - Attempt number
   - Failure type (e.g., "phase3_llm_check", "phase2_code_didnt_error")
   - For LLM check failures: similarity_score, target_similarity_score (7), impossibility_score, target_impossibility_score (7)
   - Detailed failure reason
   - Raw LLM response
2. Regenerate with failure context
3. Up to **5 total attempts** per method

#### Raw Response Storage:
All LLM responses must be stored:
- Store raw response in `raw_llm_response` field for each successful result
- Store raw response in `raw_llm_response` field for each failure in failure_history
- This allows for debugging and analysis of LLM behavior

#### Functions:
- `verify_impossible_question(original_question, modified_question, original_answer, failure_history=None)` → Returns verification dict

---

## Usage

### Command Line

```bash
# Process 1 problem from index 0
python dag.py --samples 1 --start 0

# Process 10 problems starting from index 5
python dag.py --samples 10 --start 5

# Use higher retry limit
python dag.py --samples 5 --max-retries 10

# Stop after first successful variation (faster)
python dag.py --samples 100 --stop-on-first

# Force re-processing even if results exist
python dag.py --samples 5 --force

# Custom output directory
python dag.py --samples 10 --output-dir my_results
```

### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--samples` | int | 1 | Number of problems to process |
| `--start` | int | 0 | Starting index in dataset |
| `--split` | str | "MATH" | Dataset split: `MATH`, `AIME24`, or `AIME25` |
| `--level` | str | "5" | Level filter (e.g., `"5"` for Level 5, `"all"` for all levels) |
| `--output-dir` | str | "results" | Output directory for results |
| `--max-retries` | int | 5 | Max retries per modification method |
| `--stop-on-first` | bool | False | Stop after first successful variation |
| `--force` | bool | False | Re-process even if result exists |
| `--extract-clean` | flag | False | Extract clean results from existing results folder and exit |
| `--clean-dir` | str | "clean_results" | Output directory for clean results |

---

## Output Format

### Individual Problem Result

Each problem generates a JSON file: `results/problem_{index}.json`

```json
{
  "index": 0,
  "original_question": "...",
  "original_solution": "...",
  "original_answer": "42",

  "generated_code": "# Python code that solves the problem",
  "code_verification": {
    "valid": true,
    "attempts": 1
  },

  "dag": {
    "nodes": [...],
    "edges": [...],
    "final_node": "n5"
  },

  "variations": {
    "variation_1_node_deletion": {
      "success": true,
      "attempts": 2,
      "result": {
        "modified_problem": "...",
        "modified_code": "...",
        "modified_dag": {...},
        "code_verification": {
          "code_errored": true,
          "output": "NameError: name 'M' is not defined"
        },
        "phase3_verification": {
          "similarity_score": 9,
          "impossibility_score": 8,
          "passes": true,
          "similarity_explanation": "...",
          "impossibility_explanation": "..."
        },
        "raw_llm_response": "..."
      },
      "failure_history": [
        {
          "attempt": 1,
          "failure_type": "phase3_llm_check",
          "similarity_score": 6,
          "target_similarity_score": 7,
          "impossibility_score": 5,
          "target_impossibility_score": 7,
          "failure_reason": "Similarity score 6 < 7: Modified problem changed too much from original",
          "raw_llm_response": "..."
        }
      ]
    },
    "variation_2_edge_deletion": {
      "success": true,
      "attempts": 1,
      "result": {...},
      "failure_history": []
    }
  },

  "successful_methods": ["variation_1_node_deletion", "variation_2_edge_deletion"],
  "success": true,
  "success_count": 2,

  "phase3_stats": [
    {"method": "variation_1_node_deletion", "similarity_score": 9, "impossibility_score": 8},
    {"method": "variation_2_edge_deletion", "similarity_score": 8, "impossibility_score": 9}
  ],

  "total_api_calls": 8
}
```

### Failure Tracking Details

Each variation in the output includes comprehensive failure tracking:

**Failure History Structure:**
```json
{
  "attempt": 1,
  "failure_type": "phase3_llm_check" | "phase2_code_didnt_error" | "code_generation_error",

  // For phase3_llm_check failures, include:
  "similarity_score": 6,
  "target_similarity_score": 7,
  "impossibility_score": 5,
  "target_impossibility_score": 7,

  // For all failures:
  "failure_reason": "Detailed explanation of what went wrong",
  "raw_llm_response": "Complete raw response from the LLM for this attempt"
}
```

**Failure Types:**
- `phase3_llm_check`: LLM verification failed (similarity < 7 or impossibility < 7)
- `phase2_code_didnt_error`: Modified code ran without errors (should have errored)
- `code_generation_error`: LLM failed to generate valid modification

**Required Fields for LLM Check Failures:**
When `failure_type == "phase3_llm_check"`, you MUST include:
- `similarity_score`: Actual score returned by LLM
- `target_similarity_score`: 7 (the threshold)
- `impossibility_score`: Actual score returned by LLM
- `target_impossibility_score`: 7 (the threshold)
- `failure_reason`: Clear statement like "Similarity score 6 < 7" or "Impossibility score 5 < 7"

### Summary File

`results/summary.json` contains aggregate statistics:

```json
{
  "total_problems": 100,
  "newly_processed": 100,
  "skipped": 0,
  "all_2_success": 87,
  "at_least_1_success": 95,
  "method_success_counts": {
    "variation_1_node_deletion": 92,
    "variation_2_edge_deletion": 89
  },
  "problem_indices": [0, 1, 2, ..., 99]
}
```

---

## API Calls Tracking

The pipeline tracks total API calls per problem:

```
Total API Calls =
  + 1 (Code generation)
  + 1 (DAG creation)
  + N (Modification attempts across both variations)
  + M (Phase 3 verification checks)
```

Example:
- Code generation: 1 call
- DAG creation: 1 call
- variation_1_node_deletion: 2 attempts (1 failed Phase 3, 1 succeeded)
  - 2 modification calls
  - 2 Phase 3 calls (both attempts)
- variation_2_edge_deletion: 1 attempt (succeeded)
  - 1 modification call
  - 1 Phase 3 call

**Total**: 2 + (2+2) + (1+1) = 2 + 4 + 2 = **8 API calls**

---

## Key Functions Reference

### Phase 1 Functions

#### `generate_code(question, solution, final_answer) -> str`
Generates algorithmic Python code that solves the problem.

**Returns:** Python code as string

**Key behavior:**
- Code must be algorithmic, not hardcoded
- Should follow solution steps
- Must print only the final answer

---

#### `verify_code(code, expected_answer) -> tuple[bool, str]`
Runs code and verifies output matches expected answer.

**Returns:** `(is_valid, output_or_error)`

**Verification methods:**
1. Direct string match
2. Numeric comparison (float tolerance)
3. Expression normalization (LaTeX → Python)
4. Symbolic comparison (sympy)
5. LLM verification (last resort)

---

#### `create_dag(question, solution, code) -> dict`
Creates DAG representing the **question structure**.

**Returns:** DAG dictionary with nodes, edges, final_node

**Focus:** Given values, constraints, relationships from problem statement

---

### Phase 2 Functions

#### `modify_to_unsolvable(question, solution, code, dag, method) -> dict`
Applies one of two modification methods to create an impossible problem.

**Parameters:**
- `method`: "variation_1_node_deletion" | "variation_2_edge_deletion"

**Returns:** Dictionary with:
- `modified_problem`: New problem statement
- `modified_dag`: Modified DAG
- `modified_code`: Code that should error
- `expected_error`: Type of error expected
- `modification_summary`: Explanation

---

#### `generate_all_variations(question, solution, code, dag, max_retries, stop_on_first) -> dict`
Generates 2 modification variations (node deletion, edge deletion) with Phase 2 & 3 verification.

**Returns:** Dictionary with results for each variation

**Each variation result contains:**
- `success`: bool
- `attempts`: int
- `result`: Modification dict (if successful)
  - Must include `raw_llm_response` field
- `failure_history`: List of failed attempts
  - Each failure must include:
    - `attempt`: int
    - `failure_type`: str (e.g., "phase3_llm_check", "phase2_code_didnt_error")
    - For LLM failures: `similarity_score`, `target_similarity_score`, `impossibility_score`, `target_impossibility_score`
    - `failure_reason`: str
    - `raw_llm_response`: str
- `all_attempts`: Detailed attempt log

---

### Phase 3 Functions

#### `verify_impossible_question(original_question, modified_question, original_answer, failure_history=None) -> dict`
Performs similarity and impossibility checks on modified problem.

**Process:**
1. Provides original question, modified question, AND original answer to LLM
2. LLM attempts to solve modified question first
3. LLM compares attempt with original answer
4. LLM scores based on what assumptions were needed

**Returns:** Dictionary with:
- `similarity_score`: 1-10
- `impossibility_score`: 1-10
- `similarity_explanation`: str
- `impossibility_explanation`: str
- `solve_attempt`: str (LLM's attempt to solve the modified question)
- `passes`: bool (True if similarity >= 5 AND impossibility >= 7)
- `raw_llm_response`: str (full raw response from LLM)

**Uses failure history** to improve subsequent attempts.

---

### Utility Functions

#### `extract_clean_results_from_dir(results_dir="results", clean_dir="clean_results") -> dict`
Extracts simplified JSON files from a full results directory. Triggered by `--extract-clean` flag.

**Each clean file contains only:**
- `original_question`: str
- `original_answer`: str
- `node_variation`: str or null (modified problem from variation 1, if successful)
- `edge_variation`: str or null (modified problem from variation 2, if successful)
- `success`: bool
- `index`: int

**Returns:** Summary dict with `total`, `successful`, `partial`, `failed` counts.

---

### Main Pipeline

#### `process_problem(problem_data, max_retries, stop_on_first) -> dict`
Processes a single problem through all 3 phases.

**Returns:** Complete result dictionary with all phases

**Workflow:**
1. Phase 1: Generate & verify code, create DAG
2. Phase 2 & 3: Generate 2 variations with full verification
   - Variation 1: Node deletion
   - Variation 2: Edge deletion
3. Count successes, track API calls
4. Return complete result with raw LLM responses and failure tracking

---

## Configuration

### Dataset Selection

The script loads `thulthula/math-bench` and selects a split via the `--split` argument:

```python
dataset = load_dataset("thulthula/math-bench", split=args.split)
```

Supported splits: `MATH` (default), `AIME24`, `AIME25`. Use `--level` to filter by difficulty level (e.g., `"5"` for Level 5, `"all"` for all levels).

### AWS Bedrock Configuration

```python
AWS_REGION = "us-east-1"
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "YOUR_AWS_ACCESS_KEY_HERE")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "YOUR_AWS_SECRET_KEY_HERE")
MODEL_NAME = "us.anthropic.claude-opus-4-6-v1"
```

The script uses **AWS Bedrock** (via `boto3`) to call Claude. Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as environment variables before running.

---

## Success Criteria

### Problem-Level Success
A problem is considered **fully successful** if:
- ✅ Phase 1: Code generation and verification passes
- ✅ Phase 2 & 3: **Both modification variations** succeed
  - Each variation's modified code must error (Phase 2)
  - Each variation's modified problem must score >= 7 on both checks (Phase 3)

### Method-Level Success
A modification method succeeds if:
- ✅ Phase 2: Modified code errors when run
- ✅ Phase 3: Similarity score >= 7
- ✅ Phase 3: Impossibility score >= 7

---

## Example Workflow

### Input Problem
```
Question: Find the smallest positive integer N such that
the product of 17 consecutive integers starting from N
exceeds 5000.

Solution: We need 17×18×...×33 > 5000. Computing step by step:
17×18 = 306, 306×19 = 5814 > 5000. So N = 17.

Answer: 17
```

### Phase 1 Output
**Generated Code** (algorithmic, not hardcoded):
```python
N_max = 5000
product = 1
N = 1

while True:
    product = 1
    for i in range(N, N + 17):
        product *= i
    if product > N_max:
        print(N)
        break
    N += 1
```

**DAG** (question structure):
```json
{
  "nodes": [
    {"id": "n1", "type": "given", "value": 5000, "label": "N_max",
     "description": "Maximum threshold value 5000"},
    {"id": "n2", "type": "given", "value": 17, "label": "consecutive_count",
     "description": "Number of consecutive integers"},
    {"id": "n3", "type": "unknown", "value": null, "label": "N",
     "description": "Smallest positive integer to find"},
    {"id": "n4", "type": "derived_info", "value": null, "label": "product",
     "description": "Product of 17 consecutive integers starting from N"},
    {"id": "n5", "type": "relationship", "value": null, "label": "product_exceeds",
     "description": "Constraint: product > N_max"}
  ],
  "edges": [
    {"from": "n2", "to": "n4", "relationship": "determines",
     "description": "Consecutive count determines product calculation"},
    {"from": "n3", "to": "n4", "relationship": "determines",
     "description": "Starting value N determines which integers to multiply"},
    {"from": "n4", "to": "n5", "relationship": "relates_to",
     "description": "Product is compared against threshold"},
    {"from": "n1", "to": "n5", "relationship": "constrains",
     "description": "Threshold constrains when product is sufficient"}
  ],
  "unknowns": ["n3"],
  "givens": ["n1", "n2"],
  "constraints": ["n5"]
}
```

### Phase 2 Output (Node Deletion)
**Modified Problem**:
```
Find the smallest positive integer N such that
the product of 17 consecutive integers starting from N
exceeds M.

[Note: M is not defined]
```

**Modified Code**:
```python
# M is not defined - will cause NameError
product = 1
N = 1

while True:
    product = 1
    for i in range(N, N + 17):
        product *= i
    if product > M:  # NameError!
        print(N)
        break
    N += 1
```

**Code Verification**: ✅ Errors with `NameError: name 'M' is not defined`

### Phase 3 Output
**Similarity Check**:
- Score: **9/10**
- Explanation: "Nearly identical problem structure, only the threshold value M is undefined. Same mathematical concept, same operations."

**Impossibility Check**:
- Score: **8/10**
- Explanation: "Clearly impossible - the variable M is referenced but never defined, making it impossible to determine when to stop the search."

**Result**: ✅ **PASS** (both scores >= 7)

---

## Error Handling

### Code Generation Failures
- **Symptom**: Generated code doesn't produce correct answer
- **Action**: Retry up to `max_retries` times
- **Result**: Save last attempt even if all fail

### Modification Generation Failures
- **Symptom**: Modified code runs without errors
- **Action**: Regenerate with feedback
- **Limit**: Up to `max_retries` attempts per method

### Phase 3 Verification Failures
- **Symptom**: Similarity < 7 or Impossibility < 7
- **Action**: Add to failure history, regenerate with context
- **Limit**: Up to `max_retries` attempts per method

### Resume Capability
- Results are saved immediately after each problem
- Skips already-processed problems (unless `--force`)
- Allows resuming interrupted runs

---

## Best Practices

1. **Start small**: Test with `--samples 1` first
2. **Use stop-on-first for exploration**: Faster when testing
3. **Higher retries for production**: `--max-retries 10` for better success rate
4. **Monitor API costs**: Track `total_api_calls` in results
5. **Check failure patterns**: Review `all_attempts` to understand common failures
6. **Validate outputs**: Spot-check that impossible problems are genuinely unsolvable

---

## Troubleshooting

### Low success rates
- Increase `--max-retries`
- Check dataset quality (some problems may be inherently difficult to modify)
- Review failure reasons in `all_attempts`

### High API costs
- Use `--stop-on-first` to reduce attempts
- Reduce `--max-retries`
- Process fewer samples initially

### Code verification failures
- Check that dataset has valid solutions
- Verify model is generating algorithmic code (not hardcoded)
- Review `code_generation_attempts` for error patterns

---

## Future Enhancements

Potential improvements:
- [ ] Add more modification methods (constraint weakening, information overload)
- [ ] Support for non-numerical answers
- [ ] Parallel processing of multiple problems
- [ ] Interactive mode for manual verification
- [ ] Difficulty scoring for impossible problems
- [ ] Validation that DAG actually represents question structure
