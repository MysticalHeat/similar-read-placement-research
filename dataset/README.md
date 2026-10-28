# Data

`prepared/prxy_1.bin` and `prepared/prn_1.bin` contain the first 11 million Read+Write events of each MSR Cambridge trace. A record consists of four little-endian signed 64-bit integers `(timestamp, offset, size, is_read)` (32 bytes). `is_read` is 1 for Read and 0 for Write. Offset and size are bytes. The pipeline uses event indices, not timestamps, for all distances.

| Prepared prefix | Events | SHA-256 |
|---|---:|---|
| prxy_1.bin | 11,000,000 | `58274611e15cd7c9075df2f1fd718c0f737d043cab0bea2beb7d1c9690a311e2` |
| prn_1.bin | 11,000,000 | `935d5b6f418bb41da596462ecd34649f903a41c878c45146efcffd476ed189fc` |

`followup/` contains only additional events after index 11,000,000, in the same binary format:

| Tail | Events | SHA-256 |
|---|---|---|
| prxy_1.bin | `[11M,12M)` | `f9db40737abe2bb3f8c0e01442ae905034e05e6af5cac62c28ac64d81c36bfbb` |
| prn_1.bin | `[11M,11233411)` | `9c808790d1ff1ac9505ef183216761367002880d9ac9f9053110b1949f119ace` |

These tails are used **only for evaluation labels**. Features, anchors and validation are identical between original and extended evaluation. The observation endpoint is fixed in the protocol before the experiment. Sidecar JSON files record the verified prefix identity, tail hash, event range and source cache. The same metadata is included in the comparison results.

If the full legacy event caches are available, prepare tails with:

```bash
uv run python count_mae_control.py prepare-followup prxy_1 --source-events ../research1_legacy_2026-10-27/results/all-write/prxy_1/events.bin
uv run python count_mae_control.py prepare-followup prn_1 --source-events ../research1_legacy_2026-10-27/results/new-workloads/prn_1/events.bin
```

The command refuses existing tails and checks that the first 11M source events match the prepared prefix before copying the tail. Raw MSR CSV-to-event preprocessing and original source metadata remain in the legacy archive.

`msr-cambridge1.tar` contains the original two traces. Attribution and format details are in `MSR-Cambridge/README.txt` inside the archive and at <https://iotta.snia.org/traces/block-io/388>. Other local traces are not used in this experiment. Large data and sidecars are excluded from Git: copy `prepared/` and `followup/` separately when moving the project.
