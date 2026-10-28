# Predicting the Number of Requests Until Overwrite

The model predicts the number of subsequent read and write requests until the next write with the same starting byte offset. The final write is included in the count.

## Models

Two LightGBM models were trained using MAE loss on observed request counts:

- [prxy_1.lightgbm.txt](prxy_1.lightgbm.txt)
- [prn_1.lightgbm.txt](prn_1.lightgbm.txt)

## Training code

[count_mae_control.py](../count_mae_control.py), function `run()`, trains the models, selects the number of iterations using validation data, and saves the models. Experiment settings are in [count_mae_protocol.json](../count_mae_protocol.json).

## Results

Evaluation uses writes in `[10M, 10.9M)` with extended observation. MAE is the mean absolute error in number of requests; lower is better. All methods are compared on the same writes with observed outcomes.

| Trace | Our model | Best simple baseline |
|---|---:|---:|
| `prxy_1` | **3 011** | 4 501 |
| `prn_1` | **84 317** | 105 369 |

MAE is **33.1%** lower than the best simple baseline for `prxy_1` and **20.0%** lower for `prn_1`.

**Limitation:** error is calculated only for observed overwrites: 98.2% of evaluation writes for `prxy_1` and 62.3% for `prn_1`. Errors remain large in some groups, and performance on new traces has not been tested. Lower average error does not establish sufficient accuracy in every case.
