# Predicting I/O requests until overwrite

This project uses **LightGBM** to predict how many read and write requests will occur before a write to the same starting byte offset happens again. It contains separate models for the `prxy_1` and `prn_1` traces.

For example, if a write occurs at event 100 and the next write at the same offset occurs at event 104, the target is **4 requests**. All intervening reads and writes count, as does the final write.

## Where to start

| I want to… | Open |
|---|---|
| See the main results | [Short report](mae_control/REPORT.md) |
| Explore results and prediction examples | [Experiment notebook](experiment.ipynb) |
| Find the trained models | [`mae_control/prxy_1.lightgbm.txt`](mae_control/prxy_1.lightgbm.txt) and [`mae_control/prn_1.lightgbm.txt`](mae_control/prn_1.lightgbm.txt) |
| Run a prediction | [`predict.py`](predict.py) and [`examples/features.json`](examples/features.json) |
| See the training and evaluation code | [`count_mae_control.py`](count_mae_control.py), function `run()` |
| Find training settings | [`count_mae_protocol.json`](count_mae_protocol.json) |
| Prepare data for reproduction | [Dataset documentation](dataset/README.md) |

## Results

Extended evaluation on writes in `[10M, 10.9M)`. MAE is the mean absolute error in **number of requests**; lower is better. Methods are compared on the same writes with observed outcomes.

| Trace | LightGBM MAE | Best simple baseline MAE | Known outcomes |
|---|---:|---:|---:|
| `prxy_1` | **3,011** | 4,501 | 98.2% |
| `prn_1` | **84,317** | 105,369 | 62.3% |

The best simple baseline is the median of the available last three write gaps for `prxy_1` and the observed training-target median for `prn_1`. LightGBM reduces MAE against these baselines by **33.1%** and **20.0%**, respectively.

**Limitation:** training and point-error evaluation use only writes whose next overwrite was observed. Unknown outcomes are excluded; some distance groups still have large errors, and performance on new traces has not been tested.

## Run a prediction

Requirements: Python 3.12+ and [uv](https://docs.astral.sh/uv/). From the project root:

```bash
uv sync --python 3.12 --extra notebook
uv run python predict.py --trace prxy_1 --input examples/features.json
uv run python predict.py --trace prn_1 --input examples/features.json
```

The output contains one positive integer `predicted_request_count` for each input record. The example file contains prepared features; the prediction command does **not** read raw trace events. The saved models and example inputs are included in Git, so these commands do not require the dataset.

Each record must contain these eight causal features:

| Feature | Meaning |
|---|---|
| `gap1`, `gap2`, `gap3` | Most recent consecutive write gaps at the same offset, in event counts |
| `current_size`, `current_offset` | Current write size and starting offset, in bytes |
| `past_W_100k`, `past_R_100k` | Counts of writes and reads at the same offset in the preceding 100,000 events |
| `read_age` | Events since the previous read at the same offset |

Missing history can be `null` or `-1`. See [`examples/features.json`](examples/features.json) for the input format.

## Train or verify

Training and full verification require the prepared event prefixes and follow-up files described in [dataset/README.md](dataset/README.md). **These large data files are not included in Git.**

```bash
# Train into a new directory; existing per-trace results are not overwritten.
uv run python count_mae_control.py run prxy_1 --output-dir reproduced_mae
uv run python count_mae_control.py run prn_1 --output-dir reproduced_mae

# Recalculate and check the saved results.
uv run python count_mae_control.py verify prxy_1 --output-dir mae_control
uv run python count_mae_control.py verify prn_1 --output-dir mae_control
```

The models and scores are unchanged after the experiment metadata was revised. `original_protocol_sha256` identifies the original frozen settings; the baseline-only criterion was evaluated retrospectively from the original predictions. The original records are preserved in the separate legacy archive.

## Run tests

```bash
uv run python -m unittest discover -s tests -p 'test_*pipeline.py' -v
uv run python -m unittest discover -s tests -p 'test_mae_control.py' -v
```

These tests check feature preparation, labels, baseline calculations and predictions from the saved models; they do not require the large datasets.
