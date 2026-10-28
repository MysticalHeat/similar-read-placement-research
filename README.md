# Predicting I/O requests until overwrite

Two LightGBM models predict the number of subsequent host read and write requests until the next write with the same starting byte offset, including that write.

## Results

| Trace | LightGBM MAE | Best simple baseline MAE | Known outcomes |
|---|---:|---:|---:|
| prxy_1 | 3,011 | 4,501 | 98.2% |
| prn_1 | 84,317 | 105,369 | 62.3% |

These extended-evaluation scores use observed overwrites only. Errors remain large in some groups, and new traces have not been tested. See [the short report](mae_control/REPORT.md) and `experiment.ipynb`.

## Run

```bash
uv sync --python 3.12 --extra notebook
uv run python -m unittest discover -s tests -p 'test_*pipeline.py' -v
uv run python -m unittest discover -s tests -p 'test_mae_control.py' -v
uv run python predict.py --trace prxy_1 --input examples/features.json
uv run python predict.py --trace prn_1 --input examples/features.json
```

Inputs are eight prepared causal features: `gap1`, `gap2`, `gap3`, `current_size`, `current_offset`, `past_W_100k`, `past_R_100k`, `read_age`. Missing history is `null` or `-1`. Predictions are positive integer request counts.

## Training and verification

The training code is `count_mae_control.py`; its settings are in `count_mae_protocol.json`. Data files are excluded from Git; see `dataset/README.md` for prepared prefixes and follow-up tails. To reproduce in a fresh directory:

```bash
uv run python count_mae_control.py run prxy_1 --output-dir reproduced_mae
uv run python count_mae_control.py run prn_1 --output-dir reproduced_mae
uv run python count_mae_control.py verify prxy_1 --output-dir mae_control
uv run python count_mae_control.py verify prn_1 --output-dir mae_control
```

The models and scores are unchanged; the experiment metadata was revised to remove the archived comparison. `original_protocol_sha256` identifies the original frozen settings. The baseline-only criterion is evaluated retrospectively from the original saved predictions. The original experiment and its records are preserved in the separate legacy archive.
