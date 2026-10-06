import gzip
import io
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from read_prediction.extended import EVENT_DTYPE
from read_prediction.notebook_selected_training import MIX_WEIGHTS, PARAMETERS, load_four_days, train_events
from read_prediction.range_label import TICKS


class SelectedTrainingTests(unittest.TestCase):
    def test_training_and_validation_labels_stop_at_their_own_boundaries(self):
        day = 86400
        rows = [(0, 0, 512, 0), (10, 0, 512, 1), (20, 0, 512, 0), (30, 0, 512, 1),
                (3 * day - 10, 512, 512, 0), (3 * day + 10, 512, 512, 1),
                (3 * day + 20, 0, 512, 0), (3 * day + 30, 0, 512, 1),
                (4 * day - 10, 0, 512, 0), (4 * day + 10, 0, 512, 1)]
        events = np.array([(time * TICKS, offset, size, read) for time, offset, size, read in rows], dtype=EVENT_DTYPE)
        with TemporaryDirectory() as directory:
            result = train_events(events, "prn_1", Path(directory), PARAMETERS, MIX_WEIGHTS)
        for rule in ("same_start", "range"):
            self.assertEqual(result[rule]["training_samples"], 2)
            self.assertEqual(result[rule]["global_median_seconds"], 10.)
            for metric in result[rule]["validation"].values():
                self.assertEqual(metric["n"], 1)
                self.assertEqual(metric["all_writes"], 2)

    def test_loader_uses_duration_not_an_exact_event_count_and_rejects_caps(self):
        boundary = 4 * 86400 * TICKS
        text = f"0,prn,1,Write,0,512,0\n10,prn,1,Read,0,512,0\n{boundary},prn,1,Read,0,512,0\n"
        compressed = gzip.compress(text.encode())
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with tarfile.open(root / "msr-cambridge1.tar", "w") as archive:
                member = tarfile.TarInfo("MSR-Cambridge/prn_1.csv.gz")
                member.size = len(compressed)
                archive.addfile(member, io.BytesIO(compressed))
            events = load_four_days(root, "prn_1", root / "events.bin", max_events=2)
            self.assertEqual(len(events), 2)
            self.assertLess(events["timestamp"][-1], boundary)
            del events
            with self.assertRaisesRegex(ValueError, "Event cap"):
                load_four_days(root, "prn_1", root / "capped.bin", max_events=1)


if __name__ == "__main__":
    unittest.main()
