# Frontier Model Evaluation Results

> Correctness for impossible variants (edge/node deletion) is determined by whether the model's predicted answer matches the **original problem's answer** (i.e., memorization signal).
>
> **Unique Imp.** = a problem is considered solved if *either* the node or edge deletion variant is solved.

## AIME24

| Model | Original | Node Deletion | Edge Deletion | Unique Imp. |
|-------|----------|---------------|---------------|-------------|
| opus-4.6 | 30/30 (100.0%) | 14/30 (46.7%) | 11/30 (36.7%) | 17/30 (56.7%) |
| kimi-k2.5 | 22/30 (73.3%) | 5/30 (16.7%) | 4/30 (13.3%) | 7/30 (23.3%) |
| sonnet-4.5 | 16/30 (53.3%) | 0/30 (0.0%) | 1/30 (3.3%) | 1/30 (3.3%) |
| glm-4.7 | 15/30 (50.0%) | 0/30 (0.0%) | 1/30 (3.3%) | 1/30 (3.3%) |
| mistral-lg3 | 15/30 (50.0%) | 1/30 (3.3%) | 0/30 (0.0%) | 1/30 (3.3%) |
| llama4-mav | 11/30 (36.7%) | 1/30 (3.3%) | 1/30 (3.3%) | 1/30 (3.3%) |
| deepseek-r1 | 26/30 (86.7%) | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) |
| grok | 26/30 (86.7%) | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) |
| deepseek-v3.2 | 18/30 (60.0%) | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) |
| deepseek | 10/30 (33.3%) | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) |
| nova-premier | 5/30 (16.7%) | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) |

## AIME25

| Model | Original | Node Deletion | Edge Deletion | Unique Imp. |
|-------|----------|---------------|---------------|-------------|
| opus-4.6 | 18/30 (60.0%) | 5/30 (16.7%) | 8/30 (26.7%) | 10/30 (33.3%) |
| kimi-k2.5 | 16/30 (53.3%) | 1/30 (3.3%) | 4/30 (13.3%) | 4/30 (13.3%) |
| deepseek-r1 | 22/30 (73.3%) | 1/30 (3.3%) | 2/30 (6.7%) | 3/30 (10.0%) |
| deepseek-v3.2 | 13/30 (43.3%) | 0/30 (0.0%) | 2/30 (6.7%) | 2/30 (6.7%) |
| mistral-lg3 | 8/30 (26.7%) | 0/30 (0.0%) | 2/30 (6.7%) | 2/30 (6.7%) |
| glm-4.7 | 14/30 (46.7%) | 0/30 (0.0%) | 1/30 (3.3%) | 1/30 (3.3%) |
| sonnet-4.5 | 11/30 (36.7%) | 0/30 (0.0%) | 1/30 (3.3%) | 1/30 (3.3%) |
| nova-premier | 5/30 (16.7%) | 0/30 (0.0%) | 1/30 (3.3%) | 1/30 (3.3%) |
| llama4-mav | 4/30 (13.3%) | 0/30 (0.0%) | 1/30 (3.3%) | 1/30 (3.3%) |
| deepseek | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) |
| grok | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) | 0/30 (0.0%) |

## Combined (AIME 2024 + 2025)

| Model | Original | Node Deletion | Edge Deletion | Unique Imp. |
|-------|----------|---------------|---------------|-------------|
| opus-4.6 | 48/60 (80.0%) | 19/60 (31.7%) | 19/60 (31.7%) | 27/60 (45.0%) |
| kimi-k2.5 | 38/60 (63.3%) | 6/60 (10.0%) | 8/60 (13.3%) | 11/60 (18.3%) |
| deepseek-r1 | 48/60 (80.0%) | 1/60 (1.7%) | 2/60 (3.3%) | 3/60 (5.0%) |
| mistral-lg3 | 23/60 (38.3%) | 1/60 (1.7%) | 2/60 (3.3%) | 3/60 (5.0%) |
| deepseek-v3.2 | 31/60 (51.7%) | 0/60 (0.0%) | 2/60 (3.3%) | 2/60 (3.3%) |
| glm-4.7 | 29/60 (48.3%) | 0/60 (0.0%) | 2/60 (3.3%) | 2/60 (3.3%) |
| sonnet-4.5 | 27/60 (45.0%) | 0/60 (0.0%) | 2/60 (3.3%) | 2/60 (3.3%) |
| llama4-mav | 15/60 (25.0%) | 1/60 (1.7%) | 2/60 (3.3%) | 2/60 (3.3%) |
| nova-premier | 10/60 (16.7%) | 0/60 (0.0%) | 1/60 (1.7%) | 1/60 (1.7%) |
| grok | 26/60 (43.3%) | 0/60 (0.0%) | 0/60 (0.0%) | 0/60 (0.0%) |
| deepseek | 10/60 (16.7%) | 0/60 (0.0%) | 0/60 (0.0%) | 0/60 (0.0%) |

## Memorization Hits (Impossible Variant Predicted == Original Answer)

| Model | Split | Variant | Problem Idx | Original Answer | Predicted Answer |
|-------|-------|---------|-------------|-----------------|------------------|
| sonnet-4.5 | AIME25 | edge_deletion | 28 | 49 | 49 |
| sonnet-4.5 | AIME24 | edge_deletion | 28 | 468 | 468 |
| opus-4.6 | AIME25 | node_deletion | 0 | 70 | 70 |
| opus-4.6 | AIME25 | edge_deletion | 2 | 106 | 106 |
| opus-4.6 | AIME25 | edge_deletion | 0 | 70 | 70 |
| opus-4.6 | AIME25 | edge_deletion | 4 | 293 | 293 |
| opus-4.6 | AIME25 | edge_deletion | 5 | 237 | 237 |
| opus-4.6 | AIME25 | node_deletion | 17 | 504 | 504 |
| opus-4.6 | AIME25 | node_deletion | 25 | 60 | 60 |
| opus-4.6 | AIME25 | edge_deletion | 26 | 735 | 735 |
| opus-4.6 | AIME25 | edge_deletion | 25 | 60 | 60 |
| opus-4.6 | AIME25 | edge_deletion | 28 | 49 | 49 |
| opus-4.6 | AIME25 | node_deletion | 27 | 468 | 468 |
| opus-4.6 | AIME24 | edge_deletion | 0 | 204 | 204 |
| opus-4.6 | AIME24 | node_deletion | 0 | 204 | 204 |
| opus-4.6 | AIME25 | node_deletion | 29 | 82 | 82 |
| opus-4.6 | AIME25 | edge_deletion | 29 | 82 | 82 |
| opus-4.6 | AIME24 | edge_deletion | 3 | 321 | 321 |
| opus-4.6 | AIME24 | node_deletion | 4 | 371 | 371 |
| opus-4.6 | AIME24 | edge_deletion | 4 | 371 | 371 |
| opus-4.6 | AIME24 | node_deletion | 5 | 211 | 211 |
| opus-4.6 | AIME24 | edge_deletion | 5 | 211 | 211 |
| opus-4.6 | AIME24 | node_deletion | 6 | 315 | 315 |
| opus-4.6 | AIME24 | edge_deletion | 7 | 236 | 236 |
| opus-4.6 | AIME24 | node_deletion | 9 | 33 | 33 |
| opus-4.6 | AIME24 | node_deletion | 11 | 55 | 55 |
| opus-4.6 | AIME24 | edge_deletion | 10 | 80 | 80 |
| opus-4.6 | AIME24 | node_deletion | 12 | 104 | 104 |
| opus-4.6 | AIME24 | edge_deletion | 12 | 104 | 104 |
| opus-4.6 | AIME24 | edge_deletion | 14 | 127 | 127 |
| opus-4.6 | AIME24 | node_deletion | 14 | 127 | 127 |
| opus-4.6 | AIME24 | node_deletion | 15 | 902 | 902 |
| opus-4.6 | AIME24 | edge_deletion | 15 | 902 | 902 |
| opus-4.6 | AIME24 | edge_deletion | 16 | 385 | 385 |
| opus-4.6 | AIME24 | node_deletion | 16 | 385 | 385 |
| opus-4.6 | AIME24 | node_deletion | 18 | 721 | 721 |
| opus-4.6 | AIME24 | edge_deletion | 18 | 721 | 721 |
| opus-4.6 | AIME24 | node_deletion | 22 | 104 | 104 |
| opus-4.6 | AIME24 | node_deletion | 27 | 73 | 73 |
| opus-4.6 | AIME24 | node_deletion | 29 | 601 | 601 |
| deepseek-r1 | AIME25 | edge_deletion | 0 | 70 | 70 |
| deepseek-r1 | AIME25 | edge_deletion | 28 | 49 | 49 |
| deepseek-r1 | AIME25 | node_deletion | 29 | 82 | 82 |
| deepseek-v3.2 | AIME25 | edge_deletion | 0 | 70 | 70 |
| deepseek-v3.2 | AIME25 | edge_deletion | 28 | 49 | 49 |
| kimi-k2.5 | AIME25 | node_deletion | 0 | 70 | 70 |
| kimi-k2.5 | AIME25 | edge_deletion | 0 | 70 | 70 |
| kimi-k2.5 | AIME25 | edge_deletion | 20 | 62 | 62 |
| kimi-k2.5 | AIME25 | edge_deletion | 28 | 49 | 49 |
| kimi-k2.5 | AIME25 | edge_deletion | 29 | 82 | 82 |
| kimi-k2.5 | AIME24 | edge_deletion | 0 | 204 | 204 |
| kimi-k2.5 | AIME24 | node_deletion | 13 | 699 | 699 |
| kimi-k2.5 | AIME24 | node_deletion | 16 | 385 | 385 |
| kimi-k2.5 | AIME24 | edge_deletion | 14 | 127 | 127 |
| kimi-k2.5 | AIME24 | node_deletion | 17 | 110 | 110 |
| kimi-k2.5 | AIME24 | edge_deletion | 16 | 385 | 385 |
| kimi-k2.5 | AIME24 | node_deletion | 21 | 116 | 116 |
| kimi-k2.5 | AIME24 | edge_deletion | 21 | 116 | 116 |
| kimi-k2.5 | AIME24 | node_deletion | 29 | 601 | 601 |
| glm-4.7 | AIME25 | edge_deletion | 28 | 49 | 49 |
| glm-4.7 | AIME24 | edge_deletion | 0 | 204 | 204 |
| llama4-mav | AIME25 | edge_deletion | 28 | 49 | 49 |
| llama4-mav | AIME24 | node_deletion | 29 | 601 | 601 |
| llama4-mav | AIME24 | edge_deletion | 29 | 601 | 601 |
| nova-premier | AIME25 | edge_deletion | 28 | 49 | 49 |
| mistral-lg3 | AIME25 | edge_deletion | 0 | 70 | 70 |
| mistral-lg3 | AIME25 | edge_deletion | 28 | 49 | 49 |
| mistral-lg3 | AIME24 | node_deletion | 22 | 104 | 104 |
