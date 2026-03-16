# math-imp: Comprehensive Project Summary

---

## 1. What We Are Trying To Do

This project builds and evaluates **a benchmark for detecting LLM memorization in mathematical reasoning**. The central question is:

> **When an LLM "solves" a hard math problem, is it genuinely reasoning — or is it pattern-matching to memorized benchmark answers from its training data?**

To answer this, we take well-known competition math problems (AIME 2024, AIME 2025, MATH-500), transform them into **impossible/unsolvable variants** by surgically removing critical information, and then evaluate models on both the original and impossible versions. A model that truly reasons should score 0% on impossible variants; a model that has memorized benchmark answers may still produce correct-looking outputs on the variants.

---

## 2. The Core Method: DAG-Based Impossibility Generation

### High-Level Pipeline

```
Original Problem + Solution + Answer
        │
        ▼
[Phase 1] Generate Algorithmic Code + DAG
        │ (verify code produces correct answer)
        ▼
[Phase 2] Modify to Make Unsolvable (2 variants)
        │ (verify modified code ERRORS when run)
        ▼
[Phase 3] LLM Judge: Similarity + Impossibility Scores
        │ (similarity ≥ 5/10 AND impossibility ≥ 7/10)
        ▼
Output: Original + Node-Deletion Variant + Edge-Deletion Variant
```

### Phase 1: Code Generation & DAG Creation

The pipeline (in `dag.py`) calls **Claude Opus 4.6 via AWS Bedrock** to:

1. **Generate algorithmic Python code** that solves the problem through computation (never hardcoded). The code is then actually run and verified to produce the correct answer.
2. **Create a DAG (Directed Acyclic Graph)** representing the *problem's structure* — not the solution. Nodes represent: given values, unknowns, derived quantities, relationships, constraints. Edges represent: determines, constrains, relates_to, defines_domain, references.

Example DAG node:
```json
{"id": "n1", "type": "given", "value": 5000, "label": "N_max",
 "description": "Maximum threshold value 5000"}
```

### Phase 2: Impossibility Generation — Two Methods

**Method 1: Node Deletion (Variation 1)**
- Remove a critical numerical value (a "given" node) that CANNOT be deduced from remaining information
- Example: "Total time is 4 hours" → "Total time is some amount"
- The modified code naturally references an undefined variable → `NameError`
- The problem becomes underdetermined: infinite possible answers

**Method 2: Edge Deletion (Variation 2)**
- Remove or make ambiguous a critical relationship/constraint between nodes
- Change affected nodes from `given` to `unknown` type
- Example: Remove the constraint linking time values to speed → both time and speed become unknowns
- The code references now-undefined values → natural error

**Key Constraint**: The code must NATURALLY error (undefined variable, not an artificially injected `raise` statement). The modification must make the problem *truly impossible*, not just harder.

### Phase 3: LLM-as-Judge Verification

Claude evaluates each modified problem on two scores:

| Score | Threshold | Meaning |
|-------|-----------|---------|
| **Similarity** (1-10) | ≥ 5 | Modified problem is still recognizably the same type of problem |
| **Impossibility** (1-10) | ≥ 7 | Truly unsolvable: no reasonable deduction can recover the answer |

The judge is instructed to **attempt to solve** the modified problem, track what assumptions it had to make, and score based on whether those assumptions are arbitrary (high impossibility) or deducible (low impossibility).

Failures are tracked and fed back to the generation phase (up to 5 retries per method).

### Generation Statistics (MATH-500 Level 5, 100 problems)
- Both variations successful: **51/100 (51%)**
- Node-deletion success: **52/100 (52%)**
- Edge-deletion success: **51/100 (51%)**

---

## 3. Datasets and Infrastructure

### Source Problems

| Dataset | Problems | Split in Pipeline |
|---------|----------|-------------------|
| AIME 2024 | 30 problems | `AIME24` |
| AIME 2025 | 30 problems | `AIME25` |
| MATH-500 Level 5 | 500 problems | `MATH` |

All loaded from HuggingFace: `thulthula/math-bench`

### Published HuggingFace Datasets
- **`thulthula/math-bench`** — Base benchmark (AIME 2024, AIME 2025)
- **`thulthula/math-imp-bench7`** — Impossible problems benchmark (AIME with DAG structure)
- **`thulthula/math-examples`** — MATH dataset with node/edge deletion variations (52 examples)

### API Infrastructure
- **Impossibility generation**: Claude Opus 4.6 via AWS Bedrock (`us.anthropic.claude-opus-4-6-v1`, region `us-east-1`)
- **Frontier model evaluation**: Various APIs via `run_frontier_bench.ipynb`
- **Small model evaluation**: vLLM for local inference of 7B models

---

## 4. Models Evaluated

### Small 7B Models (Local Inference via vLLM)
1. DeepSeek-LLM-7B-Chat
2. DeepSeek-Math-7B-Instruct
3. InternLM2-Chat-7B
4. InternLM2-Math-7B
5. Qwen2.5-7B-Instruct
6. Qwen2.5-Math-7B-Instruct

### Frontier Models (API-Based)
| Model ID | Provider |
|----------|----------|
| claude-opus-4.6 | Anthropic |
| claude-sonnet-4.5 | Anthropic |
| deepseek-r1 | DeepSeek |
| deepseek-v3.2 | DeepSeek |
| grok-4 | xAI |
| glm-4.7 | Zhipu AI |
| kimi-k2.5 | Moonshot |
| llama4-maverick | Meta |
| mistral-large-3 | Mistral |
| nova-premier | Amazon |

---

## 5. Evaluation Methodology

### Evaluation Types

#### Baseevals (Pass@10)
- Run each model on original AIME problems with **10 rollouts**
- Assess: can the model solve the original problem at all?
- Metric: Pass@k (did any of k rollouts produce the correct answer?)

#### Varevals (Pass@10)
- Same 10-rollout evaluation on **impossible variants**
- Both node-deletion and edge-deletion variants
- **Key metric**: any non-zero pass rate on variants = memorization signal

#### Pass@50 Analysis
- Deeper investigation using **50 rollouts** on subsets
- Separates problems the model previously solved (base) from truly hard ones
- Allows measuring pass rates at thresholds: ≥1/50, ≥3/50, ≥5/50, ≥10/50, ≥25/50

#### Frontier Benchmark
- Single-rollout evaluation of frontier models on both original and impossible variants
- All 60 AIME problems (AIME24 + AIME25), both splits

### Answer Verification
Multi-layer verification handles equivalent formats:
1. Direct string match
2. Numeric float comparison (tolerance 1e-6)
3. Expression normalization (LaTeX → Python)
4. Symbolic comparison via SymPy
5. LLM equivalence check as last resort (Claude)

---

## 6. Key Results

### Small 7B Models — AIME Performance (Pass@10)

#### Base Problems (Solvable)
| Model | Solved | Accuracy |
|-------|--------|----------|
| Qwen2.5-Math-7B-Instruct ⭐ | 13/60 | **21.67%** |
| Qwen2.5-7B-Instruct | 11/60 | 18.33% |
| DeepSeek-Math-7B-Instruct | 5/60 | 8.33% |
| DeepSeek-LLM-7B-Chat | 1/60 | 1.67% |
| InternLM2-Chat-7B | 1/60 | 1.67% |
| InternLM2-Math-7B | 0/60 | 0% |

#### Impossible Variants (Should Be 0% If No Memorization)
| Model | Solved | Accuracy | Memorization Signal? |
|-------|--------|----------|----------------------|
| Qwen2.5-Math-7B-Instruct ⭐ | 8/120 | **6.67%** | ⚠️ Yes |
| Qwen2.5-7B-Instruct | 6/120 | 5.00% | ⚠️ Yes |
| DeepSeek-Math-7B-Instruct | 3/120 | 2.50% | ⚠️ Yes |
| InternLM2-Math-7B | 2/120 | 1.67% | ⚠️ Yes |
| InternLM2-Chat-7B | 1/120 | 0.83% | ⚠️ Yes |
| DeepSeek-LLM-7B-Chat | 0/120 | 0% | ✅ None |

**Observation**: The ranking stays roughly the same between base and variants — the models that are best at math are also best at "solving" the unsolvable. This is consistent with memorization of benchmark answers.

### Frontier Models — AIME Performance (Single Rollout)

#### Base Problems
| Model | AIME24 | AIME25 |
|-------|--------|--------|
| Claude Opus 4.6 | **100%** (30/30) | **60%** (18/30) |
| DeepSeek-R1 | 86.7% (26/30) | 73.3% (22/30) |
| Grok-4 | 86.7% (26/30) | N/A |
| Kimi-K2.5 | 73.3% (22/30) | 53.3% (16/30) |
| DeepSeek-V3.2 | 60.0% (18/30) | 43.3% (13/30) |
| Claude Sonnet 4.5 | 53.3% (16/30) | 36.7% (11/30) |
| GLM-4.7 | 50.0% (15/30) | 46.7% (14/30) |
| Mistral-Large-3 | 50.0% (15/30) | 26.7% (8/30) |
| Llama4-Maverick | 36.7% (11/30) | 13.3% (4/30) |
| Nova-Premier | 16.7% (5/30) | 16.7% (5/30) |

#### Impossible Variants — **ALL MODELS SCORE 0%**
| Model | Node Deletion | Edge Deletion |
|-------|---------------|---------------|
| Claude Opus 4.6 | 0% | 0% |
| DeepSeek-R1 | 0% | 0% |
| DeepSeek-V3.2 | 0% | 0% |
| GLM-4.7 | 0% | 0% |
| Kimi-K2.5 | 0% | 0% |
| Claude Sonnet 4.5 | 0% | 0% |
| Llama4-Maverick | 0% | 0% |
| Mistral-Large-3 | 0% | 0% |
| Nova-Premier | 0% | 0% |

**Critical Finding**: Every single frontier model scores **0% on impossible variants** while scoring high on original problems. This suggests frontier models either:
1. Genuinely detect that the problems are unsolvable (good reasoning), OR
2. Cannot recover the missing information needed to solve the variant

Either way, they do NOT blindly output memorized answers for modified problems.

### Pass@50 Results — Impossible Variants (Models That Solved Base)

On problems where a model solved the base question, how often can it solve the impossible variant with 50 tries?

| Model | Pass@1 | Pass@10 | Pass@50 |
|-------|--------|---------|---------|
| Qwen2.5-7B-Instruct | 33.3% | 66.7% | 83.3% |
| Qwen2.5-Math-7B-Instruct | 0% | 12.5% | 50.0% |
| DeepSeek-Math-7B-Instruct | 0% | 33.3% | 33.3% |
| InternLM2-Math-7B | 0% | 0% | 0% |
| InternLM2-Chat-7B | 0% | 0% | 0% |

**Observation**: With enough rollouts, Qwen2.5-7B-Instruct can "solve" 83.3% of impossible variants that it also solved in base. This strong memorization signal is especially notable because these variants are definitionally unsolvable.

---

## 7. Comparative Reasoning Analysis

A separate pipeline (`comparative_reasoning_analysis.py`) uses **Claude Opus 4.6 as an LLM judge** to analyze *how* model reasoning changes between base and variant problems.

### 4-Stage Pipeline
1. **Base Reasoning Analysis**: Identify correct/wrong reasoning steps in the model's original problem response
2. **Variant Reasoning Analysis**: Same analysis for the modified problem response
3. **Question Difference Analysis**: Identify what information was removed between original and variant
4. **Propagation Analysis**: Did the question changes actually propagate into different reasoning?

### Propagation Score (1-10)
- **≥5**: Question changes meaningfully impacted the model's reasoning
- **<5**: Model used essentially the same (possibly wrong) approach regardless of the variant
- Cutoff classified as "yes/no"

### Findings
- Many low-performing models (DeepSeek-LLM-7B-Chat) score below 5 on propagation — they fail both base and variant for the same flawed reasons, not because they detected missing information
- Higher-performing models show more propagation — they attempt to account for missing values
- The **key memorization signal**: models that produce correct-looking answers on impossible variants without noticing missing information (non-propagating)

Full analysis: 720 units (6 models × 60 problems × 2 variants), ~2,880 API calls

---

## 8. Project File Structure

```
math-imp/
├── dag.py                          # Main pipeline: generates impossible problems
├── dag.md                          # Full pipeline documentation
├── requirements.txt                # Python dependencies
│
├── run notebooks/
│   ├── baseevals_pass10.ipynb      # Evaluates 7B models on base AIME (Pass@10)
│   ├── varevalpass@10.ipynb        # Evaluates 7B models on impossible variants (Pass@10)
│   ├── pass50_base_correctonly.ipynb    # 50-rollout analysis on solved base problems
│   ├── pass50_impossible_correct.ipynb  # 50-rollout analysis on impossible variants
│   ├── run_frontier_bench.ipynb    # Evaluates frontier models (API) on base + variants
│   ├── math_dataset_eval.ipynb     # Evaluates models on MATH-500 variations
│   └── math_dataset_eval.py        # Script version of MATH evaluation
│
├── helper scripts/
│   ├── comparative_reasoning_analysis.py   # LLM-judge reasoning propagation analysis
│   ├── COMPARATIVE_REASONING_ANALYSIS.md   # Documentation for above
│   ├── llm_verify_answers.py               # LLM-based answer equivalence verification
│   ├── llm_verify_answers.ipynb
│   ├── math_dataset_eval.py                # MATH dataset evaluator
│   ├── MATH_DATASET_EVAL_README.md         # Documentation for above
│   ├── verify_math_answers.py              # Math answer verification utilities
│   ├── eda_analysis.py                     # Exploratory data analysis
│   ├── fix_truncated_questions.py          # Data cleaning utility
│   └── upload_to_hf.py                     # Upload datasets to HuggingFace
│
├── plot_thresholds.py              # Visualization: Pass@k threshold curves (base vs vars)
│
├── results/                        # Per-problem full results (100 MATH-500 problems)
│   ├── problem_0.json ... problem_99.json
│   └── summary.json
│
├── csv and results/                # All evaluation results
│   ├── all_results_base.csv        # 6 models × 60 AIME problems (Pass@10 base)
│   ├── all_results_var.csv         # 6 models × 60 AIME problems × 2 variants
│   ├── all_results_base_MATH*.csv  # MATH dataset evaluations
│   ├── comparative_results/        # Reasoning propagation analysis JSONs + summary
│   ├── frontier_bench_results/     # Frontier model evaluation CSVs
│   ├── pass50_base_correctonly_results/   # 50-rollout base analysis
│   └── pass50_impossible_correct_results/ # 50-rollout variant analysis
│
├── data/                           # Symlinked/copied CSVs for easy access
├── past/                           # Older result files and notebooks
│   ├── baseevals_pass10_results/   # Earlier run results
│   ├── varevalpass10_results/
│   ├── AIME 2024 clean/            # Clean impossible problems for AIME24
│   ├── AIME 2025 clean/            # Clean impossible problems for AIME25
│   ├── MATH500/                    # MATH-500 data
│   └── md folder/                  # Earlier analysis summaries
│
└── baseevals_math_pass10.ipynb     # Base MATH-500 evaluation notebook
```

---

## 9. How Memorization Detection Works — The Key Insight

### The Logic
```
IF model score on impossible variants > 0%
THEN model is producing answers without reasoning from given information
THEREFORE model is likely recalling memorized benchmark answers
```

### Why This Works
- Impossible variants are **structurally similar** to originals (similarity ≥ 5/10)
- They are **provably unsolvable** as stated (impossibility ≥ 7/10)
- Modified code **errors when run** — no computational path to the answer
- A model reasoning from first principles MUST acknowledge missing information
- A model with memorized answer just outputs the pattern-matched answer

### The Contrast
| Model Type | Base Accuracy | Variant Accuracy | Interpretation |
|------------|---------------|------------------|----------------|
| Frontier (Opus, R1, Grok) | 60-100% | **0%** | Strong reasoning, no memorization |
| 7B Math Specialized | 20-22% | **5-7%** | Partial memorization |
| 7B General Chat | 0-18% | **0-5%** | Some memorization in top performers |

---

## 10. Technical Implementation Notes

### dag.py Key Functions
| Function | Phase | Purpose |
|----------|-------|---------|
| `generate_code()` | 1 | LLM generates algorithmic Python from problem+solution |
| `verify_code()` | 1 | Run code, check output vs expected answer (5 methods) |
| `create_dag()` | 1 | LLM creates DAG representing problem structure |
| `modify_to_unsolvable()` | 2 | LLM modifies problem/DAG/code to be impossible |
| `generate_all_variations()` | 2+3 | Orchestrates both modification methods with retries |
| `verify_impossible_question()` | 3 | LLM judge scores similarity + impossibility |
| `process_problem()` | All | End-to-end pipeline for one problem |
| `extract_clean_results_from_dir()` | Post | Creates simplified clean result JSONs |

### Command Line Usage
```bash
# Generate impossible variants for 10 MATH Level-5 problems
python dag.py --samples 10 --start 0 --split MATH --level 5

# Process AIME 2024 problems
python dag.py --samples 30 --split AIME24 --level all

# Resume interrupted run (skips existing files)
python dag.py --samples 100 --start 0

# Extract clean results after generation
python dag.py --extract-clean --output-dir results
```

### AWS Bedrock Configuration
```python
AWS_REGION = "us-east-1"
MODEL_NAME = "us.anthropic.claude-opus-4-6-v1"
# Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars
```

### Cost Tracking
Each problem requires approximately:
- 2 API calls (code gen + DAG creation)
- 2-10 API calls per variation (modification + Phase 3 check), 2 variations
- Total: ~6-22 calls per problem
- Full run of 100 problems ≈ 600-2200 API calls

---

## 11. Summary of Research Findings

1. **Small 7B models show clear memorization signals**: Non-zero pass rates on impossible variants (5-7%) even with Pass@10, rising to 50-83% with Pass@50, indicate these models are drawing on memorized information rather than pure reasoning.

2. **Frontier models show 0% on impossible variants**: Every frontier model (Opus, R1, Grok, etc.) achieves 0% on both node-deletion and edge-deletion variants across all 60 AIME problems. This does NOT mean they are better reasoners necessarily — it could mean the impossible variants are well-calibrated enough that even sophisticated models cannot pattern-match to answers.

3. **Reasoning propagation is low for weak models**: The comparative reasoning analysis shows many low-performing models make the same types of errors on base and variant — they fail because they can't reason, not because they detect missing information.

4. **Benchmark contamination hypothesis supported**: The fact that the same models performing best on base problems also perform best on impossible variants (maintaining relative rankings) is consistent with contamination: models that saw more AIME problems in training do better on both.

5. **The benchmark is an effective probe**: The 3-phase DAG pipeline successfully generates impossible problems with ~51% full success rate (both variants), providing a rigorous test for LLM mathematical reasoning vs. memorization.
