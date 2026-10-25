
### Paired Wilcoxon signed-rank tests (synthetic)

| scope                          | A          | B         |   n |   mean_diff_pt | win_rate   |   p_value |
|:-------------------------------|:-----------|:----------|----:|---------------:|:-----------|----------:|
| all budgets, all workloads     | VRS+C      | GDS       | 250 |           5.51 | 78%        |   2.7e-17 |
| all budgets, all workloads     | VRS+C      | VRS       | 250 |           4.24 | 100%       |   5.1e-42 |
| all budgets, all workloads     | VRS        | GDS       | 250 |           1.27 | 62%        |   0.00062 |
| all budgets, all workloads     | VRS        | GenAgents | 250 |           7.58 | 79%        |   6.4e-18 |
| all budgets, all workloads     | VRS        | ImpDecay  | 250 |           6.81 | 86%        |   7.4e-37 |
| all budgets, all workloads     | GDS        | LRU       | 250 |          17.12 | 90%        |   1.1e-40 |
| all budgets, all workloads     | GenAgents  | LRU       | 250 |          10.81 | 90%        |   2.9e-40 |
| all budgets, all workloads     | LRU        | Random    | 250 |          12.6  | 99%        |   2.1e-42 |
| all budgets, all workloads     | Ebbinghaus | Random    | 250 |          15.38 | 100%       |   9.5e-43 |
| B = 10%                        | VRS+C      | GDS       |  50 |           4.64 | 76%        |   0.00012 |
| B = 10%                        | VRS+C      | VRS       |  50 |           4.34 | 100%       |   1.8e-15 |
| B = 10%                        | VRS        | GDS       |  50 |           0.3  | 62%        |   0.22    |
| B = 10%                        | VRS        | GenAgents |  50 |           5.08 | 78%        |   0.0011  |
| IRM (stationary), all budgets  | VRS        | GDS       |  50 |           6.51 | 92%        |   1.1e-12 |
| Temporal locality, all budgets | VRS        | GDS       |  50 |          -9.81 | 0%         |   1.8e-15 |
| Rare-critical, all budgets     | VRS        | GDS       |  50 |           4.39 | 92%        |   2.2e-12 |
| Drift, all budgets             | VRS        | GDS       |  50 |           5.07 | 96%        |   5.9e-14 |
| Mixed assistant, all budgets   | VRS        | GDS       |  50 |           0.17 | 28%        |   0.062   |

### Gap decomposition at B = 10% (points of OPT)

| Workload          |   DENSITY* (% OPT) |   VRS (% OPT) |   GDS (% OPT) |   Information gap (OPT − DENSITY*) |   Estimation gap (DENSITY* − VRS) |   VRS (% of DENSITY*) |
|:------------------|-------------------:|--------------:|--------------:|-----------------------------------:|----------------------------------:|----------------------:|
| Drift             |               73.9 |          73.8 |          68.3 |                               26.1 |                               0.1 |                  99.9 |
| IRM (stationary)  |               85.1 |          76.8 |          72.1 |                               14.9 |                               8.3 |                  90.2 |
| Mixed assistant   |               93.8 |          82.4 |          83.3 |                                6.2 |                              11.4 |                  87.8 |
| Rare-critical     |               85.7 |          78.6 |          74.2 |                               14.3 |                               7.2 |                  91.6 |
| Temporal locality |               95.7 |          78.5 |          90.6 |                                4.3 |                              17.2 |                  82   |

### DENSITY* / VRS / GDS across budgets (avg over workloads, fraction of OPT)

|   cap_frac |   DENSITY* |   GDS |   VRS |
|-----------:|-----------:|------:|------:|
|      0.025 |      0.785 | 0.566 | 0.621 |
|      0.05  |      0.82  | 0.673 | 0.688 |
|      0.1   |      0.869 | 0.777 | 0.78  |
|      0.2   |      0.926 | 0.88  | 0.873 |
|      0.4   |      0.975 | 0.96  | 0.959 |

### Price of clairvoyance, simulated E[OPT]/E[DENSITY]

|   req_per_item |   (100, 1) |   (100, 10) |   (1000, 1) |   (1000, 10) |
|---------------:|-----------:|------------:|------------:|-------------:|
|           0.25 |      8.661 |       5.105 |      12.103 |        8.917 |
|           0.5  |      5.912 |       4.032 |       8.024 |        6.363 |
|           1    |      4.222 |       3.003 |       5.504 |        4.429 |
|           2    |      3.151 |       2.362 |       3.974 |        3.291 |
|           4    |      2.456 |       1.945 |       2.97  |        2.543 |
|           8    |      1.989 |       1.652 |       2.328 |        2.049 |
|          16    |      1.681 |       1.454 |       1.901 |        1.721 |
|          32    |      1.468 |       1.316 |       1.619 |        1.498 |
|          64    |      1.328 |       1.222 |       1.429 |        1.347 |
|         128    |      1.229 |       1.156 |       1.299 |        1.242 |
|         256    |      1.16  |       1.109 |       1.209 |        1.169 |

### Compression sensitivity (avg over workloads at B = 10%, fraction of evict-only OPT)

|             |   GDS+C |   GenAgents+C |   VRS+C |
|:------------|--------:|--------------:|--------:|
| (0.1, 0.3)  |   0.757 |         0.723 |   0.808 |
| (0.1, 0.6)  |   0.869 |         0.857 |   0.891 |
| (0.1, 0.9)  |   1.005 |         1.012 |   0.992 |
| (0.25, 0.3) |   0.766 |         0.73  |   0.781 |
| (0.25, 0.6) |   0.81  |         0.765 |   0.824 |
| (0.25, 0.9) |   0.936 |         0.935 |   0.904 |
| (0.5, 0.6)  |   0.776 |         0.737 |   0.783 |
| (0.5, 0.9)  |   0.845 |         0.82  |   0.821 |

### Workload-distribution sensitivity (fraction of OPT, B = 10%)

|                                        |   LRU |   Ebbinghaus |   GenAgents |   GDS |   VRS |   VRS+C | best   |
|:---------------------------------------|------:|-------------:|------------:|------:|------:|--------:|:-------|
| ('irm', 'critical_value_mult=10.0')    | 0.499 |        0.562 |       0.641 | 0.721 | 0.768 |   0.825 | VRS+C  |
| ('irm', 'critical_value_mult=100.0')   | 0.499 |        0.562 |       0.641 | 0.721 | 0.768 |   0.825 | VRS+C  |
| ('irm', 'critical_value_mult=30.0')    | 0.499 |        0.562 |       0.641 | 0.721 | 0.768 |   0.825 | VRS+C  |
| ('irm', 'rate_shape=1.1')              | 0.621 |        0.693 |       0.713 | 0.761 | 0.784 |   0.835 | VRS+C  |
| ('irm', 'rate_shape=1.5')              | 0.499 |        0.562 |       0.641 | 0.721 | 0.768 |   0.825 | VRS+C  |
| ('irm', 'rate_shape=3.0')              | 0.415 |        0.431 |       0.62  | 0.705 | 0.758 |   0.827 | VRS+C  |
| ('irm', 'size_sigma=0.3')              | 0.512 |        0.572 |       0.653 | 0.681 | 0.737 |   0.802 | VRS+C  |
| ('irm', 'size_sigma=0.6')              | 0.499 |        0.562 |       0.641 | 0.721 | 0.768 |   0.825 | VRS+C  |
| ('irm', 'size_sigma=1.0')              | 0.486 |        0.553 |       0.622 | 0.781 | 0.814 |   0.858 | VRS+C  |
| ('irm', 'value_sigma=0.5')             | 0.537 |        0.603 |       0.563 | 0.64  | 0.701 |   0.784 | VRS+C  |
| ('irm', 'value_sigma=1.0')             | 0.499 |        0.562 |       0.641 | 0.721 | 0.768 |   0.825 | VRS+C  |
| ('irm', 'value_sigma=2.0')             | 0.465 |        0.52  |       0.849 | 0.886 | 0.905 |   0.923 | VRS+C  |
| ('mixed', 'critical_value_mult=10.0')  | 0.644 |        0.684 |       0.766 | 0.804 | 0.788 |   0.825 | VRS+C  |
| ('mixed', 'critical_value_mult=100.0') | 0.427 |        0.424 |       0.883 | 0.896 | 0.891 |   0.909 | VRS+C  |
| ('mixed', 'critical_value_mult=30.0')  | 0.563 |        0.587 |       0.806 | 0.833 | 0.824 |   0.853 | VRS+C  |
| ('mixed', 'rate_shape=1.1')            | 0.658 |        0.68  |       0.855 | 0.867 | 0.86  |   0.88  | VRS+C  |
| ('mixed', 'rate_shape=1.5')            | 0.563 |        0.587 |       0.806 | 0.833 | 0.824 |   0.853 | VRS+C  |
| ('mixed', 'rate_shape=3.0')            | 0.489 |        0.477 |       0.76  | 0.81  | 0.795 |   0.828 | VRS+C  |
| ('mixed', 'size_sigma=0.3')            | 0.566 |        0.585 |       0.805 | 0.821 | 0.804 |   0.837 | VRS+C  |
| ('mixed', 'size_sigma=0.6')            | 0.563 |        0.587 |       0.806 | 0.833 | 0.824 |   0.853 | VRS+C  |
| ('mixed', 'size_sigma=1.0')            | 0.558 |        0.589 |       0.805 | 0.866 | 0.854 |   0.876 | VRS+C  |
| ('mixed', 'value_sigma=0.5')           | 0.544 |        0.564 |       0.775 | 0.8   | 0.784 |   0.818 | VRS+C  |
| ('mixed', 'value_sigma=1.0')           | 0.563 |        0.587 |       0.806 | 0.833 | 0.824 |   0.853 | VRS+C  |
| ('mixed', 'value_sigma=2.0')           | 0.601 |        0.631 |       0.888 | 0.925 | 0.924 |   0.936 | VRS+C  |

### LoCoMo (interleaved protocol): % of OPT (mean ± std)

| Policy | B = 5% | B = 10% | B = 20% | B = 40% | Evidence recall @10% |
|---|---|---|---|---|---|
| Random | 19.4 ± 3.5 | 25.3 ± 3.3 | 37.7 ± 3.9 | 60.0 ± 4.1 | 21.1% |
| FIFO | 21.2 ± 3.5 | 29.6 ± 3.5 | 42.0 ± 3.6 | 64.1 ± 5.7 | 24.6% |
| LRU | 22.2 ± 3.8 | 30.7 ± 3.9 | 43.9 ± 4.7 | 68.5 ± 5.9 | 25.6% |
| LFU | 19.0 ± 3.7 | 29.5 ± 4.7 | 45.4 ± 5.6 | 71.6 ± 5.5 | 24.7% |
| GDS | 36.6 ± 4.3 | 45.9 ± 4.4 | 60.1 ± 6.2 | 82.1 ± 6.0 | 38.4% |
| Ebbinghaus | 22.7 ± 3.9 | 31.4 ± 4.1 | 45.1 ± 5.3 | 71.2 ± 5.6 | 26.2% |
| GenAgents | 33.8 ± 4.5 | 42.3 ± 3.9 | 56.7 ± 5.5 | 81.5 ± 5.7 | 35.3% |
| ImpDecay | 33.0 ± 5.5 | 42.6 ± 4.6 | 58.4 ± 6.6 | 81.9 ± 5.6 | 35.6% |
| VRS | 34.1 ± 5.7 | 43.9 ± 5.1 | 59.3 ± 6.1 | 82.0 ± 5.9 | 36.8% |
| VRS+C | 48.1 ± 3.8 | 54.0 ± 4.6 | 65.9 ± 5.6 | 84.1 ± 5.6 | 56.4% |
| GenAgents+C | **53.5 ± 4.4** | **60.8 ± 4.6** | **70.3 ± 3.6** | **86.7 ± 4.0** | 79.0% |
| LRU+C | 22.8 ± 3.8 | 31.0 ± 3.8 | 44.1 ± 4.7 | 68.6 ± 5.9 | 25.9% |
| VRS-noRate | 32.3 ± 6.8 | 40.5 ± 6.6 | 56.9 ± 6.2 | 80.7 ± 6.0 | 33.8% |
| VRS-noValue | 12.6 ± 4.1 | 18.7 ± 4.6 | 31.3 ± 5.1 | 58.7 ± 6.1 | 15.5% |
| VRS-noSize | 31.1 ± 5.6 | 40.8 ± 4.5 | 56.3 ± 6.2 | 81.3 ± 5.8 | 34.1% |
| VRS (no LLM) | 12.6 ± 4.1 | 18.7 ± 4.6 | 31.3 ± 5.1 | 58.7 ± 6.1 | 15.5% |
| GDS (no LLM) | 18.1 ± 3.3 | 25.8 ± 3.5 | 39.4 ± 5.0 | 62.4 ± 6.0 | 21.5% |
| GenAgents (no LLM) | 22.2 ± 3.8 | 30.7 ± 3.9 | 43.9 ± 4.7 | 68.5 ± 5.9 | 25.6% |

### LoCoMo (end protocol): % of OPT (mean ± std)

| Policy | B = 5% | B = 10% | B = 20% | B = 40% | Evidence recall @10% |
|---|---|---|---|---|---|
| Random | 10.4 ± 4.1 | 14.4 ± 3.8 | 21.5 ± 4.1 | 37.8 ± 3.3 | 7.9% |
| FIFO | 10.3 ± 4.4 | 16.4 ± 5.3 | 22.4 ± 4.1 | 36.6 ± 4.1 | 8.9% |
| LRU | 10.3 ± 4.4 | 16.4 ± 5.3 | 22.4 ± 4.1 | 36.6 ± 4.1 | 8.9% |
| LFU | 10.3 ± 4.4 | 16.4 ± 5.3 | 22.4 ± 4.1 | 36.6 ± 4.1 | 8.9% |
| GDS | 25.9 ± 7.4 | 34.8 ± 6.2 | 49.2 ± 5.7 | 71.5 ± 7.3 | 19.3% |
| Ebbinghaus | 10.3 ± 4.4 | 16.4 ± 5.3 | 22.4 ± 4.1 | 36.6 ± 4.1 | 8.9% |
| GenAgents | 23.8 ± 8.6 | 28.6 ± 4.2 | 40.1 ± 6.8 | 65.0 ± 7.3 | 15.7% |
| ImpDecay | 26.7 ± 6.2 | 35.7 ± 7.0 | 45.1 ± 5.2 | 67.7 ± 8.2 | 19.7% |
| VRS | 38.7 ± 7.5 | 47.0 ± 7.0 | 53.9 ± 6.8 | 73.5 ± 7.4 | 26.0% |
| VRS+C | **58.5 ± 5.9** | 64.5 ± 7.5 | 67.9 ± 5.8 | **77.0 ± 6.7** | 47.4% |
| GenAgents+C | 55.1 ± 8.7 | **70.5 ± 8.7** | **69.1 ± 6.4** | 75.1 ± 4.9 | 63.4% |
| LRU+C | 10.6 ± 4.1 | 16.4 ± 5.3 | 22.6 ± 4.0 | 36.7 ± 4.1 | 9.0% |
| VRS-noRate | 45.3 ± 9.7 | 48.7 ± 7.1 | 56.6 ± 6.6 | 73.5 ± 6.8 | 26.9% |
| VRS-noValue | 8.7 ± 5.3 | 10.9 ± 4.7 | 16.4 ± 3.8 | 30.4 ± 4.0 | 5.9% |
| VRS-noSize | 31.0 ± 8.7 | 39.6 ± 7.6 | 49.1 ± 6.0 | 72.0 ± 6.9 | 21.9% |
| VRS (no LLM) | 8.7 ± 5.3 | 10.9 ± 4.7 | 16.4 ± 3.8 | 30.4 ± 4.0 | 5.9% |
| GDS (no LLM) | 8.7 ± 3.5 | 13.5 ± 3.8 | 18.7 ± 3.8 | 33.0 ± 4.7 | 7.3% |
| GenAgents (no LLM) | 10.3 ± 4.4 | 16.4 ± 5.3 | 22.4 ± 4.1 | 36.6 ± 4.1 | 8.9% |

### LoCoMo paired Wilcoxon tests

| scope                    | A         | B                  |   n |   mean_diff_pt | win_rate   |   p_value |
|:-------------------------|:----------|:-------------------|----:|---------------:|:-----------|----------:|
| interleaved, all budgets | VRS       | GDS                | 400 |          -1.34 | 31%        |   5e-14   |
| interleaved, all budgets | VRS+C     | GDS                | 400 |           6.86 | 96%        |   2.8e-66 |
| interleaved, all budgets | VRS+C     | VRS                | 400 |           8.19 | 99%        |   4.1e-67 |
| interleaved, all budgets | VRS       | GenAgents          | 400 |           1.27 | 61%        |   1.6e-08 |
| interleaved, all budgets | VRS       | LRU                | 400 |          13.5  | 98%        |   1.1e-66 |
| interleaved, all budgets | GDS       | LRU                | 400 |          14.84 | 100%       |   2.8e-67 |
| interleaved, all budgets | VRS       | VRS (no LLM)       | 400 |          24.52 | 100%       |   2.7e-67 |
| interleaved, all budgets | GDS       | GDS (no LLM)       | 400 |          19.75 | 100%       |   2.7e-67 |
| interleaved, all budgets | GenAgents | GenAgents (no LLM) | 400 |          12.23 | 98%        |   1.4e-66 |
| end, all budgets         | VRS       | GDS                |  40 |           7.9  | 90%        |   2e-07   |
| end, all budgets         | VRS+C     | GDS                |  40 |          21.62 | 100%       |   1.8e-12 |
| end, all budgets         | VRS+C     | VRS                |  40 |          13.72 | 100%       |   1.8e-12 |
| end, all budgets         | VRS       | GenAgents          |  40 |          13.89 | 100%       |   1.8e-12 |
| end, all budgets         | VRS       | LRU                |  40 |          31.84 | 100%       |   3.6e-08 |
| end, all budgets         | GDS       | LRU                |  40 |          23.94 | 95%        |   9.1e-12 |

### LoCoMo instance statistics

- conversations: 10; items per conversation: 369–689 (total 5882); questions used: 1535
- oracle instances: 440; max MIP gap 9.5e-16