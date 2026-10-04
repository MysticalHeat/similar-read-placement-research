# Synthetic Read-Temperature Prediction Demonstration
**A synthetic pipeline demonstration—not a test of SSD speedup.**

## What we checked
We tested the following pipeline on two predefined scenarios: past accesses → prediction of a page's future category → comparison of methods on identical keys. Each scenario comprised 96 logical pages of 4 KiB and 6 hours of events. History, prediction horizon and step were all 600 s; features came from `[t−600,t)`, and labels from `[t,t+600)`: cold = 0, warm = 1–2, hot ≥ 3 future READs.

Train/val/test: 0–180/200–260/280–360 min, with gaps, history resets and 10 min of warmup. Z is historical frequency, D is always-cold, A is count-only CART, and X is CART using four past-access features. Maximum depth 3, minimum leaf size 50; four fixed benchmark fits, with no parameter tuning.

## Observed results
E004: **11 selected checks passed**, with 8 toy fits and 0 benchmark fits. Counts/labels matched independent expectations in 6912 bin comparisons and 5568 decision comparisons. E005: 4 benchmark fits and 0 tuning fits; val/test predictions for **BOTH cases** were saved before the evaluation labels were read in E005; the finite frozen-model future-mutation check passed. This is neither the full unit-test suite nor proof for all inputs. [C037–C038]

**Macro-F1; N denotes page–time pairs, not independent replicates:**

| Scenario / split | N | Z: frequency | D: always-cold | A: count-only CART | X: four-feature CART |
|---|---:|---:|---:|---:|---:|
| phase_cycle / val | 480 | 0.000 | 0.167 | 1.000 | 1.000 |
| phase_cycle / test | 672 | 0.000 | 0.167 | 1.000 | 1.000 |
| independent_negative / val | 480 | 0.326 | 0.162 | 0.251 | 0.259 |
| independent_negative / test | 672 | 0.331 | 0.162 | 0.248 | 0.274 |

## Interpretation and negative result
In the engineered cycle, **A = X**: learning the rule count 0 → warm, 1 → hot, 4 → cold was sufficient. No benefit from the additional features was observed; historical-frequency baseline Z performs poorly by construction in this scenario. [C039]

In independent_negative, the trained methods **performed worse than Z on both val and test**. On test, X−Z = −0.0569 macro-F1; A/X did not predict cold. The low scores were retained, and the seed was not tuned. [C040]

## What we can conclude
The pipeline received **bounded technical support from fixed synthetic checks**. This is not proof of real-world read predictability, novelty or SSD speedup. Two artificial cases and dependent windows do not constitute an iid sample; p-values/confidence intervals were not calculated. A full join, hash recomputation and independent replication were not performed; reviewers had only partial access to long JSON records. H005, placement, migration costs and SSD throughput were not tested.

Resources: 10.46 s of observed worker wall time and 10.21 CPU-s; maximum **sampled current VmRSS** of 34.34 MiB. Startup/tool/exit costs and the earlier B001 STOP remain separately UNKNOWN, not zero. There is no whole-domain RAM/time/disk certificate; OS exit was not independently observed; memory-sampling intervals slightly exceeded the soft 0.25 s target. Historical R002 remains open. [C041]

## Artifacts and reproduction
All paths below are relative to `.research/`. Primary data: `experiments/raw/E004/checks.json`; `experiments/raw/E005/*.score.json#seen_strata.all`, `models.json`, `prediction-commit.json`, manifests. Exact values/confusion matrices: [analysis.md](analysis.md), [metrics.csv](metrics.csv). Independent review: `reviews/synthetic-deadline-results-review-v0.3.md`; claims/support: `claims/evidence-map.md` C037–C041.

Exact executed commands/configuration/freeze: `protocol/synthetic-deadline-approval-D001-2026-10-02.md` and `experiments/control/synthetic-deadline-v0.3/`. **Do not rerun commands using occupied IDs:** a new approved plan is required. Raw data, earlier versions and the failed B001 attempt were preserved.

**Summary:** “On synthetic data, the pipeline passed the selected checks; the cycle was learned using the count alone, but on the independent scenario the model performed worse than the frequency heuristic. We have not yet tested SSD speedup.”
