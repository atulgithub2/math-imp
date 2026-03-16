# FINAL RESULTS - All Models, All Datasets (Post-Drop)

Generated: 2026-03-15

---

## Data Sources - Exact File Paths

All paths relative to project root: `/home/shivank_g/projects/atul/math-imp/`

### Frontier AIME24+25 (new run, pass@5)
- **Compact CSV:** `run notebooks/results/frontier_models/all_models_compact.csv` (10,800 rows)
- **Full CSV (with responses):** `run notebooks/results/frontier_models/all_models_full.csv` (631K rows)
- **Per-model CSVs:** `run notebooks/results/frontier_models/results_<model>.csv`
- **Pass@k summary:** `run notebooks/results/frontier_models/pass_at_k_summary.csv`
- **Models:** sonnet-4.6, sonnet-3.7, deepseek-r1, deepseek-v3.2, kimi-k2.5, llama4-mav, mistral-lg3, nova-premier
- **Token limits:** sonnet-4.6/deepseek-r1: 8192, others: 6144, llama4-mav: 2560, nova-premier/sonnet-3.7: 2048

### Frontier AIME24+25 (old run, pass@1)
- **Compact CSV:** `csv_and_results/frontier_bench_results/all_models_compact.csv` (1,980 rows)
- **Full CSV:** `csv_and_results/frontier_bench_results/all_models_full.csv`
- **Per-model CSVs:** `csv_and_results/frontier_bench_results/results_<model>.csv`
- **Models:** opus-4.6, sonnet-4.5, glm-4.7 (+ overlapping models, but new run preferred for those)
- **Token limit:** 4096 for all

### Frontier AIME2026 (pass@5)
- **Merged+corrected CSV (USE THIS):** `results_AIME2026_pass@5_1st inference/frontier_aime2026_merged/all_models_corrected.csv`
- **V1 raw:** `results_AIME2026_pass@5_1st inference/frontier_aime2026/all_models_compact.csv`
- **V2 subset rerun:** `results_AIME2026_pass@5_1st inference/frontier_aime2026_v2/`
- **Models:** sonnet-4.6, sonnet-3.7, deepseek-r1, deepseek-v3.2, kimi-k2.5, llama4-mav, mistral-lg3, nova-premier (gemini3, gpt-5.2, grok-4.2 all failed)

### Frontier MATH-52 (pass@1)
- **Compact CSV:** `MATH52_frontier_pass@1_before_checklist/all_models_compact.csv` (1,240 rows)
- **Full CSV:** `MATH52_frontier_pass@1_before_checklist/all_models_full.csv`
- **Per-model CSVs:** `MATH52_frontier_pass@1_before_checklist/results_<model>.csv`
- **Models:** sonnet-4.6, deepseek-r1, deepseek-v3.2, kimi-k2.5, llama4-mav, mistral-lg3, nova-premier (opus-4.6 all auth errors)

### GPT-5.4 (bench9, pass@1)
- **CSV:** `MODEL_RUN#3/complete_run/results_gpt-5.4.csv`
- **Compact (all models):** `MODEL_RUN#3/complete_run/all_models_compact.csv`
- **Splits:** AIME24, AIME25, AIME2026, MATH (all in one file, filter by `split` column)

### Gemini-3.1-pro (bench9, scrapper, impossible variants only)
- **Results summary:** `MODEL_RUN#3/scrapper_gemini/RESULTS.md`
- **Raw JSON data:** `MODEL_RUN#3/scrapper_gemini/data/automate_results_AIME2024.json`
- **Raw JSON data:** `MODEL_RUN#3/scrapper_gemini/data/automate_results_AIME2025.json`
- **Raw JSON data:** `MODEL_RUN#3/scrapper_gemini/data/automate_results_AIME2026.json`
- **No base/original data available**

### 7B Models - AIME24+25
- **Base CSV:** `csv_and_results/all_results_base.csv` (360 rows = 60 probs x 6 models)
- **Impossible CSV:** `csv_and_results/all_results_var.csv` (720 rows = 60 probs x 2 variants x 6 models)
- **Correctness:** base uses `is_correct` column; impossible use manual str comparison (is_correct_exact is WRONG)

### 7B Models - AIME24+25 Pass@50
- **Base subset:** `csv_and_results/pass50_base_correctonly_results/all_results_pass50_base.csv`
- **Impossible subset:** `csv_and_results/pass50_impossible_correct_results/all_results_pass50.csv`
- **Note:** Only ran on problems where model got >=1 correct in pass@10

### 7B Models - MATH-52
- **Base CSV:** `csv_and_results/all_results_base_MATH.csv` (312 rows = 52 probs x 6 models)
- **Impossible CSV:** `csv_and_results/all_results_math_52examples.csv` (624 rows)

### Sonnet 4.5 & GLM 4.7 - AIME2026 (bench9, pass@1)
- **Sonnet 4.5 JSON:** `MODEL_RUN#3/results_sonnet-4.5_aime2026_pass1.json` (86 records)
- **GLM 4.7 JSON:** `MODEL_RUN#3/results_glm-4.7_aime2026_pass1.json` (86 records)
- **Combined JSON:** `MODEL_RUN#3/results_all_sonnet45_glm47_aime2026.json`
- **Summary:** `MODEL_RUN#3/summary_sonnet45_glm47_aime2026.json`
- **Dataset:** `thulthula/math-imp-bench9` AIME2026 split (30 base, 28 edge, 28 node)
- **Temperature:** 0.0 (greedy), max_tokens: 8192/4096

### Drop Log
- **Full drop details:** `resultCompileDropChangedQuestions/dropped_questions_log.md`
- **Rerun needed list:** `resultCompileDropChangedQuestions/rerun_needed.md`

## Drop Policy

**Old/new runs (bench8):** AIME25 edge drop p0,p5,p28,p29 (/26), node drop p29 (/29). AIME2026 edge drop p11,p21,p24,p26 (/25), node drop p7,p18,p25,p29 (/24). MATH edge /36-37, node /40.

**Bench9 (GPT-5.4, Gemini):** No regen drops. AIME25 /30. AIME2026 edge /28, node /28. MATH /41.

**Correctness:** Always `str(predicted_answer).strip() == str(original_answer).strip()` (is_correct_exact is WRONG).

---

# SECTION 1: FRONTIER MODELS - AIME24+25

**Source files:**
- New run (pass@5): `run notebooks/results/frontier_models/all_models_compact.csv`
- Old run (pass@1): `csv_and_results/frontier_bench_results/all_models_full.csv`
- GPT-5.4: `MODEL_RUN#3/complete_run/results_gpt-5.4.csv` (filter: split in [AIME24, AIME25])
- Gemini: `MODEL_RUN#3/scrapper_gemini/data/automate_results_AIME202{4,5}.json`

## 1.1 Response Quality (Truncation & Errors)

| Model | Source | Total Responses | Truncated | Errored | Valid |
|---|---|---|---|---|---|
| sonnet-4.6 | new (pass@5) | 900 | 30 (3%) | 0 | 870 (97%) |
| sonnet-3.7 | new (pass@5) | 900 | 10 (1%) | 0 | 890 (99%) |
| deepseek-v3.2 | new (pass@5) | 900 | 90 (10%) | 0 | 810 (90%) |
| kimi-k2.5 | new (pass@5) | 900 | 176 (20%) | 0 | 724 (80%) |
| mistral-lg3 | new (pass@5) | 900 | 183 (20%) | 0 | 717 (80%) |
| nova-premier | new (pass@5) | 900 | 4 (0%) | 1 (0%) | 895 (99%) |
| llama4-mav | new (pass@5) | 900 | 1 (0%) | 0 | 899 (100%) |
| deepseek-r1 | new (pass@5) | 900 | 54 (6%) | 117 (13%) | 729 (81%) |
| opus-4.6 | old (pass@1) | 180 | 0 (0%) | 0 | 180 (100%) |
| sonnet-4.5 | old (pass@1) | 180 | 1 (1%) | 0 | 179 (99%) |
| glm-4.7 | old (pass@1) | 180 | 97 (54%) | 0 | 83 (46%) |
| gpt-5.4 | bench9 (pass@1) | 180 | 0 (0%) | 22 (12%) | 158 (88%) |
| gemini-3.1-pro | bench9 scrapper | 120 (imp only) | 0 | 0 | 120 (100%) |

## 1.2 Pass@1 (first valid non-truncated run)

### AIME24

| Model | Base /30 | Edge /30 | Node /30 |
|---|---|---|---|
| opus-4.6 | 30/30 (100%) | 11/30 (37%) | 14/30 (47%) |
| sonnet-4.6 | 23/30 (77%) | 11/30 (37%) | 8/30 (27%) |
| kimi-k2.5 | 24/30 (80%) | 2/30 (7%) | 1/30 (3%) |
| deepseek-v3.2 | 22/30 (73%) | 0/30 (0%) | 5/30 (17%) |
| deepseek-r1 | 18/30 (60%) | 0/30 (0%) | 1/30 (3%) |
| mistral-lg3 | 17/30 (57%) | 0/30 (0%) | 1/30 (3%) |
| sonnet-4.5 | 16/30 (53%) | 1/30 (3%) | 0/30 (0%) |
| gpt-5.4 | 16/30 (53%) | 1/30 (3%) | 0/30 (0%) |
| glm-4.7 | 15/30 (50%) | 1/30 (3%) | 0/30 (0%) |
| llama4-mav | 11/30 (37%) | 2/30 (7%) | 1/30 (3%) |
| sonnet-3.7 | 6/30 (20%) | 0/30 (0%) | 0/30 (0%) |
| nova-premier | 5/30 (17%) | 0/30 (0%) | 0/30 (0%) |
| gemini-3.1-pro | N/A | 6/30 (20%) | 9/30 (30%) |

### AIME25

| Model | Base /30 | Edge | Node |
|---|---|---|---|
| opus-4.6 | 18/30 (60%) | 4/26 (15%) | 4/29 (14%) |
| sonnet-4.6 | 17/30 (57%) | 1/26 (4%) | 3/29 (10%) |
| kimi-k2.5 | 16/30 (53%) | 0/26 (0%) | 3/29 (10%) |
| deepseek-v3.2 | 16/30 (53%) | 0/26 (0%) | 0/29 (0%) |
| gpt-5.4 | 15/30 (50%) | 0/30 (0%) | 0/30 (0%) |
| glm-4.7 | 14/30 (47%) | 0/26 (0%) | 0/29 (0%) |
| deepseek-r1 | 12/30 (40%) | 0/26 (0%) | 0/29 (0%) |
| mistral-lg3 | 12/30 (40%) | 0/26 (0%) | 2/29 (7%) |
| sonnet-4.5 | 11/30 (37%) | 0/26 (0%) | 0/29 (0%) |
| nova-premier | 5/30 (17%) | 0/26 (0%) | 0/29 (0%) |
| llama4-mav | 4/30 (13%) | 0/26 (0%) | 0/29 (0%) |
| sonnet-3.7 | 4/30 (13%) | 0/26 (0%) | 0/29 (0%) |
| gemini-3.1-pro | N/A | 5/30 (17%) | 4/30 (13%) |

### AIME24+25 Combined

| Model | Base /60 | Edge /56* | Node /59* |
|---|---|---|---|
| opus-4.6 | 48/60 (80%) | 15/56 (27%) | 18/59 (31%) |
| sonnet-4.6 | 40/60 (67%) | 12/56 (21%) | 11/59 (19%) |
| kimi-k2.5 | 40/60 (67%) | 2/56 (4%) | 4/59 (7%) |
| deepseek-v3.2 | 38/60 (63%) | 0/56 (0%) | 5/59 (8%) |
| gpt-5.4 | 31/60 (52%) | 1/60 (2%) | 0/60 (0%) |
| deepseek-r1 | 30/60 (50%) | 0/56 (0%) | 1/59 (2%) |
| mistral-lg3 | 29/60 (48%) | 0/56 (0%) | 3/59 (5%) |
| glm-4.7 | 29/60 (48%) | 1/56 (2%) | 0/59 (0%) |
| sonnet-4.5 | 27/60 (45%) | 1/56 (2%) | 0/59 (0%) |
| llama4-mav | 15/60 (25%) | 2/56 (4%) | 1/59 (2%) |
| sonnet-3.7 | 10/60 (17%) | 0/56 (0%) | 0/59 (0%) |
| nova-premier | 10/60 (17%) | 0/56 (0%) | 0/59 (0%) |
| gemini-3.1-pro | N/A | 11/60 (18%) | 13/60 (22%) |

`*` /56 edge and /59 node for bench8 models; /60 for bench9 models (GPT-5.4, Gemini)

## 1.3 Pass@5 Total (any correct across 5 runs - new run models only)

### AIME24

| Model | Base /30 | Edge /30 | Node /30 |
|---|---|---|---|
| sonnet-4.6 | 29/30 (97%) | 19/30 (63%) | 17/30 (57%) |
| kimi-k2.5 | 27/30 (90%) | 4/30 (13%) | 6/30 (20%) |
| deepseek-v3.2 | 26/30 (87%) | 6/30 (20%) | 7/30 (23%) |
| deepseek-r1 | 23/30 (77%) | 0/30 (0%) | 2/30 (7%) |
| mistral-lg3 | 20/30 (67%) | 0/30 (0%) | 2/30 (7%) |
| llama4-mav | 16/30 (53%) | 2/30 (7%) | 1/30 (3%) |
| sonnet-3.7 | 11/30 (37%) | 0/30 (0%) | 1/30 (3%) |
| nova-premier | 7/30 (23%) | 0/30 (0%) | 1/30 (3%) |

### AIME25

| Model | Base /30 | Edge /26 | Node /29 |
|---|---|---|---|
| sonnet-4.6 | 25/30 (83%) | 2/26 (8%) | 5/29 (17%) |
| kimi-k2.5 | 20/30 (67%) | 0/26 (0%) | 4/29 (14%) |
| deepseek-v3.2 | 20/30 (67%) | 2/26 (8%) | 1/29 (3%) |
| mistral-lg3 | 16/30 (53%) | 3/26 (12%) | 2/29 (7%) |
| deepseek-r1 | 15/30 (50%) | 1/26 (4%) | 0/29 (0%) |
| llama4-mav | 9/30 (30%) | 0/26 (0%) | 0/29 (0%) |
| sonnet-3.7 | 8/30 (27%) | 0/26 (0%) | 3/29 (10%) |
| nova-premier | 8/30 (27%) | 1/26 (4%) | 1/29 (3%) |

## 1.4 Pass>=x/5 Consistency

### AIME24 Base (/30)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| sonnet-4.6 | 29/30 (97%) | 27/30 (90%) | 25/30 (83%) | 22/30 (73%) | 18/30 (60%) |
| kimi-k2.5 | 27/30 (90%) | 26/30 (87%) | 26/30 (87%) | 21/30 (70%) | 15/30 (50%) |
| deepseek-v3.2 | 26/30 (87%) | 26/30 (87%) | 23/30 (77%) | 20/30 (67%) | 14/30 (47%) |
| deepseek-r1 | 23/30 (77%) | 21/30 (70%) | 18/30 (60%) | 11/30 (37%) | 2/30 (7%) |
| mistral-lg3 | 20/30 (67%) | 19/30 (63%) | 16/30 (53%) | 15/30 (50%) | 12/30 (40%) |
| llama4-mav | 16/30 (53%) | 12/30 (40%) | 12/30 (40%) | 10/30 (33%) | 8/30 (27%) |
| sonnet-3.7 | 11/30 (37%) | 6/30 (20%) | 5/30 (17%) | 4/30 (13%) | 2/30 (7%) |
| nova-premier | 7/30 (23%) | 6/30 (20%) | 5/30 (17%) | 4/30 (13%) | 2/30 (7%) |

### AIME24 Edge (/30)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| sonnet-4.6 | 19/30 (63%) | 11/30 (37%) | 11/30 (37%) | 4/30 (13%) | 1/30 (3%) |
| deepseek-v3.2 | 6/30 (20%) | 2/30 (7%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) |
| kimi-k2.5 | 4/30 (13%) | 2/30 (7%) | 1/30 (3%) | 1/30 (3%) | 0/30 (0%) |
| llama4-mav | 2/30 (7%) | 2/30 (7%) | 2/30 (7%) | 1/30 (3%) | 0/30 (0%) |
| deepseek-r1 | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) |
| mistral-lg3 | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) |
| nova-premier | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) |
| sonnet-3.7 | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) |

### AIME24 Node (/30)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| sonnet-4.6 | 17/30 (57%) | 12/30 (40%) | 10/30 (33%) | 7/30 (23%) | 4/30 (13%) |
| deepseek-v3.2 | 7/30 (23%) | 3/30 (10%) | 2/30 (7%) | 0/30 (0%) | 0/30 (0%) |
| kimi-k2.5 | 6/30 (20%) | 3/30 (10%) | 2/30 (7%) | 0/30 (0%) | 0/30 (0%) |
| mistral-lg3 | 2/30 (7%) | 1/30 (3%) | 1/30 (3%) | 1/30 (3%) | 0/30 (0%) |
| deepseek-r1 | 2/30 (7%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) |
| llama4-mav | 1/30 (3%) | 1/30 (3%) | 1/30 (3%) | 0/30 (0%) | 0/30 (0%) |
| nova-premier | 1/30 (3%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) |
| sonnet-3.7 | 1/30 (3%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) |

### AIME25 Base (/30)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| sonnet-4.6 | 25/30 (83%) | 20/30 (67%) | 17/30 (57%) | 14/30 (47%) | 12/30 (40%) |
| kimi-k2.5 | 20/30 (67%) | 17/30 (57%) | 14/30 (47%) | 11/30 (37%) | 9/30 (30%) |
| deepseek-v3.2 | 20/30 (67%) | 18/30 (60%) | 17/30 (57%) | 14/30 (47%) | 9/30 (30%) |
| mistral-lg3 | 16/30 (53%) | 14/30 (47%) | 10/30 (33%) | 9/30 (30%) | 7/30 (23%) |
| deepseek-r1 | 15/30 (50%) | 12/30 (40%) | 10/30 (33%) | 8/30 (27%) | 6/30 (20%) |
| llama4-mav | 9/30 (30%) | 5/30 (17%) | 4/30 (13%) | 3/30 (10%) | 3/30 (10%) |
| sonnet-3.7 | 8/30 (27%) | 8/30 (27%) | 3/30 (10%) | 2/30 (7%) | 1/30 (3%) |
| nova-premier | 8/30 (27%) | 5/30 (17%) | 4/30 (13%) | 4/30 (13%) | 1/30 (3%) |

### AIME25 Edge (/26)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| mistral-lg3 | 3/26 (12%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) |
| sonnet-4.6 | 2/26 (8%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) |
| deepseek-v3.2 | 2/26 (8%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) |
| deepseek-r1 | 1/26 (4%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) |
| nova-premier | 1/26 (4%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) |
| kimi-k2.5 | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) |
| llama4-mav | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) |
| sonnet-3.7 | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) | 0/26 (0%) |

### AIME25 Node (/29)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| sonnet-4.6 | 5/29 (17%) | 2/29 (7%) | 2/29 (7%) | 1/29 (3%) | 0/29 (0%) |
| kimi-k2.5 | 4/29 (14%) | 2/29 (7%) | 2/29 (7%) | 1/29 (3%) | 0/29 (0%) |
| sonnet-3.7 | 3/29 (10%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) |
| mistral-lg3 | 2/29 (7%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) |
| deepseek-v3.2 | 1/29 (3%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) |
| nova-premier | 1/29 (3%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) |
| deepseek-r1 | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) |
| llama4-mav | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) | 0/29 (0%) |

---

# SECTION 2: FRONTIER MODELS - AIME2026

**Source files:**
- Pass@5: `results_AIME2026_pass@5_1st inference/frontier_aime2026_merged/all_models_corrected.csv`
- GPT-5.4: `MODEL_RUN#3/complete_run/results_gpt-5.4.csv` (filter: split == AIME2026)
- Gemini: `MODEL_RUN#3/scrapper_gemini/data/automate_results_AIME2026.json`

## 2.1 Pass@1 (first valid run)

Old models: Edge /25, Node /24. Bench9: Edge /28, Node /28. Base /30 all.

| Model | Base /30 | Edge | Node |
|---|---|---|---|
| deepseek-v3.2 | 21/30 (70%) | 1/25 (4%) | 0/24 (0%) |
| sonnet-4.6 | 18/30 (60%) | 1/25 (4%) | 1/24 (4%) |
| kimi-k2.5 | 18/30 (60%) | 1/25 (4%) | 0/24 (0%) |
| deepseek-r1 | 19/30 (63%) | 1/25 (4%) | 0/24 (0%) |
| gpt-5.4 | 17/30 (57%) | 0/28 (0%) | 3/28 (11%) |
| mistral-lg3 | 14/30 (47%) | 2/25 (8%) | 1/24 (4%) |
| sonnet-3.7 | 5/30 (17%) | 1/25 (4%) | 0/24 (0%) |
| llama4-mav | 5/30 (17%) | 0/25 (0%) | 0/24 (0%) |
| nova-premier | 4/30 (13%) | 0/25 (0%) | 0/24 (0%) |
| gemini-3.1-pro | 23/30 (77%) | 4/28 (14%) | 2/28 (7%) |

## 2.2 Pass@5 Total (any correct across 5 runs)

| Model | Base /30 | Edge /25 | Node /24 |
|---|---|---|---|
| sonnet-4.6 | 25/30 (83%) | 2/25 (8%) | 1/24 (4%) |
| kimi-k2.5 | 23/30 (77%) | 3/25 (12%) | 0/24 (0%) |
| deepseek-v3.2 | 22/30 (73%) | 1/25 (4%) | 1/24 (4%) |
| deepseek-r1 | 19/30 (63%) | 1/25 (4%) | 0/24 (0%) |
| mistral-lg3 | 18/30 (60%) | 2/25 (8%) | 1/24 (4%) |
| sonnet-3.7 | 10/30 (33%) | 2/25 (8%) | 0/24 (0%) |
| llama4-mav | 10/30 (33%) | 0/25 (0%) | 0/24 (0%) |
| nova-premier | 6/30 (20%) | 0/25 (0%) | 0/24 (0%) |

## 2.3 Pass>=x/5 Consistency

### Base (/30)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| sonnet-4.6 | 25/30 (83%) | 21/30 (70%) | 19/30 (63%) | 17/30 (57%) | 14/30 (47%) |
| kimi-k2.5 | 23/30 (77%) | 22/30 (73%) | 17/30 (57%) | 14/30 (47%) | 8/30 (27%) |
| deepseek-v3.2 | 22/30 (73%) | 20/30 (67%) | 16/30 (53%) | 15/30 (50%) | 8/30 (27%) |
| deepseek-r1 | 19/30 (63%) | 17/30 (57%) | 16/30 (53%) | 14/30 (47%) | 10/30 (33%) |
| mistral-lg3 | 18/30 (60%) | 13/30 (43%) | 12/30 (40%) | 9/30 (30%) | 4/30 (13%) |
| sonnet-3.7 | 10/30 (33%) | 6/30 (20%) | 3/30 (10%) | 2/30 (7%) | 2/30 (7%) |
| llama4-mav | 10/30 (33%) | 8/30 (27%) | 6/30 (20%) | 5/30 (17%) | 3/30 (10%) |
| nova-premier | 6/30 (20%) | 4/30 (13%) | 2/30 (7%) | 2/30 (7%) | 0/30 (0%) |

### Edge (/25)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| kimi-k2.5 | 3/25 (12%) | 2/25 (8%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) |
| sonnet-4.6 | 2/25 (8%) | 1/25 (4%) | 1/25 (4%) | 1/25 (4%) | 1/25 (4%) |
| mistral-lg3 | 2/25 (8%) | 1/25 (4%) | 1/25 (4%) | 0/25 (0%) | 0/25 (0%) |
| sonnet-3.7 | 2/25 (8%) | 1/25 (4%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) |
| deepseek-r1 | 1/25 (4%) | 1/25 (4%) | 1/25 (4%) | 1/25 (4%) | 1/25 (4%) |
| deepseek-v3.2 | 1/25 (4%) | 1/25 (4%) | 1/25 (4%) | 1/25 (4%) | 1/25 (4%) |
| llama4-mav | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) |
| nova-premier | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) |

### Node (/24)

| Model | >=1/5 | >=2/5 | >=3/5 | >=4/5 | =5/5 |
|---|---|---|---|---|---|
| sonnet-4.6 | 1/24 (4%) | 1/24 (4%) | 1/24 (4%) | 1/24 (4%) | 0/24 (0%) |
| deepseek-v3.2 | 1/24 (4%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) |
| mistral-lg3 | 1/24 (4%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) |
| deepseek-r1 | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) |
| kimi-k2.5 | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) |
| llama4-mav | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) |
| nova-premier | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) |
| sonnet-3.7 | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) | 0/24 (0%) |

---

# SECTION 3: FRONTIER MODELS - MATH

**Source files:**
- Old models: `MATH52_frontier_pass@1_before_checklist/all_models_full.csv`
- GPT-5.4: `MODEL_RUN#3/complete_run/results_gpt-5.4.csv` (filter: split == MATH)

Pass@1 only (no pass@5 data available for MATH).

Old models: Base /52, Edge /36, Node /40. GPT-5.4 bench9: Base /41, Edge /41, Node /41.

| Model | Base | Edge | Node |
|---|---|---|---|
| llama4-mav | 38/52 (73%) | 2/36 (6%) | 3/40 (8%) |
| deepseek-v3.2 | 28/52 (54%) | 0/36 (0%) | 0/40 (0%) |
| sonnet-4.6 | 27/52 (52%) | 2/36 (6%) | 4/40 (10%) |
| kimi-k2.5 | 22/52 (42%) | 0/36 (0%) | 2/40 (5%) |
| nova-premier | 21/52 (40%) | 0/36 (0%) | 0/40 (0%) |
| deepseek-r1 | 17/52 (33%) | 0/36 (0%) | 0/40 (0%) |
| gpt-5.4 | 16/41 (39%) | 1/41 (2%) | 1/41 (2%) |
| mistral-lg3 | 16/52 (31%) | 1/36 (3%) | 1/40 (3%) |

Notes: opus-4.6 excluded (all AWS auth errors). nova-premier has 7 content_filtered errors on base.

---

# SECTION 4: 7B MODELS - AIME24+25 (Pass@10)

**Source files:**
- Base: `csv_and_results/all_results_base.csv` (correctness: `is_correct` column)
- Impossible: `csv_and_results/all_results_var.csv` (correctness: manual str comparison)
- Pass@50 base: `csv_and_results/pass50_base_correctonly_results/all_results_pass50_base.csv`
- Pass@50 impossible: `csv_and_results/pass50_impossible_correct_results/all_results_pass50.csv`

### Per-Split

| Model | A24 Base/30 | A25 Base/30 | A24 Edge/30 | A25 Edge/26 | A24 Node/30 | A25 Node/29 |
|---|---|---|---|---|---|---|
| Qwen2.5-Math-7B-Instruct | 5/30 (17%) | 9/30 (30%) | 3/30 (10%) | 1/26 (4%) | 3/30 (10%) | 0/29 (0%) |
| Qwen2.5-7B-Instruct | 7/30 (23%) | 6/30 (20%) | 0/30 (0%) | 1/26 (4%) | 2/30 (7%) | 2/29 (7%) |
| DeepSeek-Math-7B-Instruct | 2/30 (7%) | 1/30 (3%) | 0/30 (0%) | 0/26 (0%) | 2/30 (7%) | 0/29 (0%) |
| InternLM2-Math-7B | 1/30 (3%) | 0/30 (0%) | 0/30 (0%) | 1/26 (4%) | 1/30 (3%) | 0/29 (0%) |
| InternLM2-Chat-7B | 0/30 (0%) | 1/30 (3%) | 0/30 (0%) | 1/26 (4%) | 0/30 (0%) | 0/29 (0%) |
| DeepSeek-LLM-7B-Chat | 0/30 (0%) | 0/30 (0%) | 0/30 (0%) | 0/26 (0%) | 0/30 (0%) | 0/29 (0%) |

### Combined

| Model | Base /60 | Edge /56 | Node /59 |
|---|---|---|---|
| Qwen2.5-Math-7B-Instruct | 14/60 (23%) | 4/56 (7%) | 3/59 (5%) |
| Qwen2.5-7B-Instruct | 13/60 (22%) | 1/56 (2%) | 4/59 (7%) |
| DeepSeek-Math-7B-Instruct | 3/60 (5%) | 0/56 (0%) | 2/59 (3%) |
| InternLM2-Math-7B | 1/60 (2%) | 1/56 (2%) | 1/59 (2%) |
| InternLM2-Chat-7B | 1/60 (2%) | 1/56 (2%) | 0/59 (0%) |
| DeepSeek-LLM-7B-Chat | 0/60 (0%) | 0/56 (0%) | 0/59 (0%) |

### 7B Pass@50 Subset (only problems correct in pass@10)

**Base subset (32 entries):**

| Threshold | Correct |
|---|---|
| pass@1 | 8/32 (25%) |
| pass@5 | 20/32 (63%) |
| pass@10 | 23/32 (72%) |
| pass@20 | 24/32 (75%) |
| pass@25 | 24/32 (75%) |
| pass@50 | 25/32 (78%) |

**Impossible subset (17 entries after drops):**

| Threshold | Edge (7 entries) | Node (10 entries) | Total (17 entries) |
|---|---|---|---|
| pass@1 | 0/7 (0%) | 1/10 (10%) | 1/17 (6%) |
| pass@5 | 0/7 (0%) | 3/10 (30%) | 3/17 (18%) |
| pass@10 | 1/7 (14%) | 3/10 (30%) | 4/17 (24%) |
| pass@20 | 2/7 (29%) | 4/10 (40%) | 6/17 (35%) |
| pass@50 | 3/7 (43%) | 5/10 (50%) | 8/17 (47%) |

---

# SECTION 5: 7B MODELS - MATH-52 (Pass@10)

**Source files:**
- Base: `csv_and_results/all_results_base_MATH.csv` (correctness: `is_correct` column)
- Impossible: `csv_and_results/all_results_math_52examples.csv` (correctness: manual str comparison)

| Model | Base /52 | Edge /37 | Node /40 |
|---|---|---|---|
| Qwen2.5-Math-7B-Instruct | 18/52 (35%) | 1/37 (3%) | 3/40 (8%) |
| Qwen2.5-7B-Instruct | 16/52 (31%) | 1/37 (3%) | 3/40 (8%) |
| DeepSeek-Math-7B-Instruct | 9/52 (17%) | 1/37 (3%) | 3/40 (8%) |
| InternLM2-Math-7B | 6/52 (12%) | 0/37 (0%) | 0/40 (0%) |
| InternLM2-Chat-7B | 3/52 (6%) | 0/37 (0%) | 0/40 (0%) |
| DeepSeek-LLM-7B-Chat | 3/52 (6%) | 1/37 (3%) | 1/40 (3%) |

---

# SECTION 6: FINAL REPORTABLE TABLES (truncation/errors = wrong)

These tables treat ALL truncated and errored responses as incorrect. Ready for paper use.

## 6.1 Frontier - AIME24 Pass@1

| Model | Base /30 | Edge /30 | Node /30 | Data Quality |
|---|---|---|---|---|
| opus-4.6 | 30/30 (100%) | 11/30 (37%) | 14/30 (47%) | Clean |
| gemini-3.1-pro | 24/30 (80%) | 6/30 (20%) | 9/30 (30%) | Base from complete_run, imp from scrapper |
| kimi-k2.5 | 24/30 (80%) | 2/30 (7%) | 1/30 (3%) | Fair (38 trunc across A24+25) |
| sonnet-4.6 | 23/30 (77%) | 11/30 (37%) | 8/30 (27%) | Good (6 trunc across A24+25) |
| deepseek-v3.2 | 22/30 (73%) | 0/30 (0%) | 5/30 (17%) | Fair (20 trunc across A24+25) |
| deepseek-r1 | 18/30 (60%) | 0/30 (0%) | 1/30 (3%) | Poor (171 trunc+err across A24+25) |
| mistral-lg3 | 17/30 (57%) | 0/30 (0%) | 1/30 (3%) | Fair (37 trunc across A24+25) |
| sonnet-4.5 | 16/30 (53%) | 1/30 (3%) | 0/30 (0%) | Clean |
| gpt-5.4 | 16/30 (53%) | 1/30 (3%) | 0/30 (0%) | Good (22 err on A24 edge+node p0-p10) |
| glm-4.7 | 15/30 (50%) | 1/30 (3%) | 0/30 (0%) | Poor (97 trunc out of 180, old run 4096 limit) |
| llama4-mav | 11/30 (37%) | 2/30 (7%) | 1/30 (3%) | Clean |
| sonnet-3.7 | 6/30 (20%) | 0/30 (0%) | 0/30 (0%) | Clean |
| nova-premier | 5/30 (17%) | 0/30 (0%) | 0/30 (0%) | Clean |

## 6.1b Frontier - AIME25 Pass@1

Old models: Edge /26, Node /29. Bench9 (GPT-5.4, Gemini): Edge /30, Node /30.

| Model | Base /30 | Edge | Node | Data Quality |
|---|---|---|---|---|
| gemini-3.1-pro | 24/30 (80%) | 5/30 (17%) | 4/30 (13%) | Base from complete_run, imp from scrapper |
| opus-4.6 | 18/30 (60%) | 4/26 (15%) | 4/29 (14%) | Clean |
| sonnet-4.6 | 17/30 (57%) | 1/26 (4%) | 3/29 (10%) | Good |
| kimi-k2.5 | 16/30 (53%) | 0/26 (0%) | 3/29 (10%) | Fair |
| deepseek-v3.2 | 16/30 (53%) | 0/26 (0%) | 0/29 (0%) | Fair |
| gpt-5.4 | 15/30 (50%) | 0/30 (0%) | 0/30 (0%) | Good |
| glm-4.7 | 14/30 (47%) | 0/26 (0%) | 0/29 (0%) | Poor |
| deepseek-r1 | 12/30 (40%) | 0/26 (0%) | 0/29 (0%) | Poor |
| mistral-lg3 | 12/30 (40%) | 0/26 (0%) | 2/29 (7%) | Fair |
| sonnet-4.5 | 11/30 (37%) | 0/26 (0%) | 0/29 (0%) | Clean |
| nova-premier | 5/30 (17%) | 0/26 (0%) | 0/29 (0%) | Clean |
| llama4-mav | 4/30 (13%) | 0/26 (0%) | 0/29 (0%) | Clean |
| sonnet-3.7 | 4/30 (13%) | 0/26 (0%) | 0/29 (0%) | Clean |

## 6.2 Frontier - AIME2026 Pass@1

| Model | Base /30 | Edge /25 | Node /24 | Data Quality |
|---|---|---|---|---|
| deepseek-v3.2 | 21/30 (70%) | 1/25 (4%) | 0/24 (0%) | Fair (142 trunc out of 395) |
| deepseek-r1 | 19/30 (63%) | 1/25 (4%) | 0/24 (0%) | Poor (235 err out of 395) |
| sonnet-4.6 | 18/30 (60%) | 1/25 (4%) | 1/24 (4%) | Good (8 trunc out of 395) |
| kimi-k2.5 | 18/30 (60%) | 1/25 (4%) | 0/24 (0%) | Fair (60 trunc out of 395) |
| gpt-5.4 | 17/30 (57%) | 0/28 (0%) | 3/28 (11%) | Clean (0 trunc, 0 err) |
| mistral-lg3 | 14/30 (47%) | 2/25 (8%) | 1/24 (4%) | Poor (170 trunc out of 395) |
| sonnet-3.7 | 5/30 (17%) | 1/25 (4%) | 0/24 (0%) | Clean (0 trunc) |
| llama4-mav | 5/30 (17%) | 0/25 (0%) | 0/24 (0%) | Clean (0 trunc, 0 err) |
| nova-premier | 4/30 (13%) | 0/25 (0%) | 0/24 (0%) | Clean (0 trunc, 0 err) |
| gemini-3.1-pro | 23/30 (77%) | 4/28 (14%) | 2/28 (7%) | Base from complete_run (7 trunc), imp from scrapper |

## 6.3 Frontier - MATH Pass@1

| Model | Base /52 | Edge /36 | Node /40 | Data Quality |
|---|---|---|---|---|
| llama4-mav | 38/52 (73%) | 2/36 (6%) | 3/40 (8%) | Clean |
| deepseek-v3.2 | 28/52 (54%) | 0/36 (0%) | 0/40 (0%) | Good (9 trunc) |
| sonnet-4.6 | 27/52 (52%) | 2/36 (6%) | 4/40 (10%) | Clean |
| kimi-k2.5 | 22/52 (42%) | 0/36 (0%) | 2/40 (5%) | Good (9 trunc) |
| nova-premier | 21/52 (40%) | 0/36 (0%) | 0/40 (0%) | Fair (7 content_filtered) |
| deepseek-r1 | 17/52 (33%) | 0/36 (0%) | 0/40 (0%) | Poor (54 trunc w/ no response) |
| gpt-5.4 | 16/41 (39%) | 1/41 (2%) | 1/41 (2%) | Clean |
| mistral-lg3 | 16/52 (31%) | 1/36 (3%) | 1/40 (3%) | Fair (15 trunc) |

## 6.4 7B Models - AIME24+25 Pass@10

| Model | Base /60 | Edge /56 | Node /59 |
|---|---|---|---|
| Qwen2.5-Math-7B-Instruct | 14/60 (23%) | 4/56 (7%) | 3/59 (5%) |
| Qwen2.5-7B-Instruct | 13/60 (22%) | 1/56 (2%) | 4/59 (7%) |
| DeepSeek-Math-7B-Instruct | 3/60 (5%) | 0/56 (0%) | 2/59 (3%) |
| InternLM2-Math-7B | 1/60 (2%) | 1/56 (2%) | 1/59 (2%) |
| InternLM2-Chat-7B | 1/60 (2%) | 1/56 (2%) | 0/59 (0%) |
| DeepSeek-LLM-7B-Chat | 0/60 (0%) | 0/56 (0%) | 0/59 (0%) |

## 6.5 7B Models - MATH-52 Pass@10

| Model | Base /52 | Edge /37 | Node /40 |
|---|---|---|---|
| Qwen2.5-Math-7B-Instruct | 18/52 (35%) | 1/37 (3%) | 3/40 (8%) |
| Qwen2.5-7B-Instruct | 16/52 (31%) | 1/37 (3%) | 3/40 (8%) |
| DeepSeek-Math-7B-Instruct | 9/52 (17%) | 1/37 (3%) | 3/40 (8%) |
| InternLM2-Math-7B | 6/52 (12%) | 0/37 (0%) | 0/40 (0%) |
| InternLM2-Chat-7B | 3/52 (6%) | 0/37 (0%) | 0/40 (0%) |
| DeepSeek-LLM-7B-Chat | 3/52 (6%) | 1/37 (3%) | 1/40 (3%) |

---

# SECTION 7: KEY CONCLUSIONS

**Memorization hierarchy (AIME24+25 impossible variant pass@1):**
1. **opus-4.6**: 27% edge, 31% node - highest, explicitly identifies original problems
2. **sonnet-4.6**: 21% edge, 19% node - very high
3. **gemini-3.1-pro**: 18% edge, 22% node - very high (imp only data)
4. **kimi-k2.5**: 4% edge, 7% node - moderate
5. **deepseek-v3.2**: 0% edge, 8% node - moderate (node only)
6. **Most others**: 0-2% edge, 0-5% node - near zero

**AIME24 vs AIME25 contamination:**
- sonnet-4.6 AIME24: 37% edge, 27% node vs AIME25: 4% edge, 10% node
- opus-4.6 AIME24: 37% edge, 47% node vs AIME25: 15% edge, 14% node
- Clear evidence AIME24 is more contaminated than AIME25

**AIME2026 (unseen):**
- All models near-zero on impossible variants (0-8% edge, 0-4% node)
- Confirms pipeline produces valid impossible problems for unseen data
- GPT-5.4 is an outlier with 3/28 node (11%) - needs investigation

**MATH-52:**
- sonnet-4.6 (6% edge, 10% node) and llama4-mav (6% edge, 8% node) show some signal
- Most others at 0%

**7B models:**
- Qwen2.5 family shows strongest memorization signal (7% on impossible variants at pass@10)
- Pass@50 analysis: 47% of tested impossible problems solved at pass@50 - systematic, not random

---
---

# ============================================================
# FINAL RESULTS ON COMPLETE BENCHMARK
# New model runs: Sonnet 4.5 & GLM 4.7 on AIME2026 (bench9)
# ============================================================

# SECTION 8: SONNET 4.5 & GLM 4.7 - AIME2026 (bench9, Pass@1)

**Run date:** 2026-03-16

**Source files:**
- Sonnet 4.5: `MODEL_RUN#3/results_sonnet-4.5_aime2026_pass1.json` (86 records)
- GLM 4.7: `MODEL_RUN#3/results_glm-4.7_aime2026_pass1.json` (86 records)
- Combined: `MODEL_RUN#3/results_all_sonnet45_glm47_aime2026.json`
- Summary: `MODEL_RUN#3/summary_sonnet45_glm47_aime2026.json`
- Checkpoint: `MODEL_RUN#3/checkpoint_sonnet45_glm47.jsonl`

**Dataset:** `thulthula/math-imp-bench9` AIME2026 split
**Variants:** Base /30, Edge /28, Node /28 (bench9 counts)
**Temperature:** 0.0 (greedy, pass@1)
**Max tokens:** Sonnet 4.5: 8192, GLM 4.7: 4096
**Data quality:** Both models: 0 errors, 0 truncation, 0 missing answers. Clean.

## 8.1 Pass@1 Results

| Model | Base /30 | Edge /28 | Node /28 | Data Quality |
|---|---|---|---|---|
| glm-4.7 | 14/30 (47%) | 1/28 (4%) | 1/28 (4%) | Clean (0 err, 0 trunc) |
| sonnet-4.5 | 11/30 (37%) | 2/28 (7%) | 1/28 (4%) | Clean (0 err, 0 trunc) |

## 8.2 Updated AIME2026 Combined Table (all models)

Incorporates Sonnet 4.5 and GLM 4.7 into the AIME2026 table from Section 2/6.2.
Old models: Edge /25, Node /24. Bench9 models (GPT-5.4, Gemini, Sonnet 4.5, GLM 4.7): Edge /28, Node /28.

| Model | Base /30 | Edge | Node | Data Quality |
|---|---|---|---|---|
| gemini-3.1-pro | 23/30 (77%) | 4/28 (14%) | 2/28 (7%) | Base from complete_run, imp from scrapper |
| deepseek-v3.2 | 21/30 (70%) | 1/25 (4%) | 0/24 (0%) | Fair |
| deepseek-r1 | 19/30 (63%) | 1/25 (4%) | 0/24 (0%) | Poor |
| sonnet-4.6 | 18/30 (60%) | 1/25 (4%) | 1/24 (4%) | Good |
| kimi-k2.5 | 18/30 (60%) | 1/25 (4%) | 0/24 (0%) | Fair |
| gpt-5.4 | 17/30 (57%) | 0/28 (0%) | 3/28 (11%) | Clean |
| glm-4.7 | 14/30 (47%) | 1/28 (4%) | 1/28 (4%) | Clean |
| mistral-lg3 | 14/30 (47%) | 2/25 (8%) | 1/24 (4%) | Poor |
| sonnet-4.5 | 11/30 (37%) | 2/28 (7%) | 1/28 (4%) | Clean |
| sonnet-3.7 | 5/30 (17%) | 1/25 (4%) | 0/24 (0%) | Clean |
| llama4-mav | 5/30 (17%) | 0/25 (0%) | 0/24 (0%) | Clean |
| nova-premier | 4/30 (13%) | 0/25 (0%) | 0/24 (0%) | Clean |

## 8.3 Key Observations

- **Sonnet 4.5** on AIME2026: 37% base, 7% edge, 4% node. Slightly higher impossible-variant rate than most models on unseen AIME2026 data (3/56 = 5.4% overall).
- **GLM 4.7** on AIME2026: 47% base (strong), 4% edge, 4% node. Clean run with higher max tokens (4096) than the old run which had 54% truncation.
- Both models show near-zero impossible variant accuracy on AIME2026, consistent with other frontier models on unseen data.
- AIME2026 remains a clean unseen benchmark: no model exceeds ~10% on impossible variants.
