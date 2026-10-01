# Authorized literal data inspection v1

2026-09-30. User approved <=120 seconds total / <=512 MiB read-only local Python profiling, no network/install/input changes. Latest request reduces scope to a few-minute plausibility assessment, not training or confirmatory evaluation. Files supplied by advisor for this local task; provenance/license/semantic schema remain unknown and no redistribution is authorized.

This inspection only counts literal tokens and field forms, file bytes and hashes. It does NOT interpret W/R as validated schema, infer time/units, fit a model, release test scores or pass training Gate 1. It therefore may proceed under the specific audit permission even while semantic/provenance gates for training remain unresolved.

First-party script: experiments/scripts/profile_tokens.py, read and inspected by orchestrator before execution. Stdlib only, binary streaming, capped line size/op labels, no writes, stdout JSON. Shared internal wall deadline 115s, command timeout 120s; RLIMIT_AS 512 MiB, no subprocess/threads/network. Partial/failed output retained; no automatic retry/limit extension. Inputs dataset/hm_0.csv and dataset/prxy_0.csv opened rb; stat identity checked before/after and full hash only on stable EOF. Integer parse validity is a syntax observation, not documented physical units. SHA256/code hash/runtime and actual command captured in new raw audit E001 (classification: data inspection, not SSD experiment).

Planned command after source inspection: python3 -B .research/experiments/scripts/profile_tokens.py dataset/hm_0.csv dataset/prxy_0.csv
Outputs from stdout/exit status saved without overwriting any raw artifact. No original trace rows/addresses exported. On complete counts, assess only whether these literal-form files contain read labels; no claim of prediction accuracy, throughput, real-world feasibility or novelty follows.

Training protocol experiment-plan.md remains unapproved and is not executed. No synthetic benchmark or model training authorized/frozen by this audit document.
