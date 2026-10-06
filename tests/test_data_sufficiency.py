import unittest

from read_prediction.experiments.data_sufficiency import WindowCounter


class WindowCounterTests(unittest.TestCase):
    def test_overwritten_writes_still_have_address_read_labels(self):
        counter = WindowCounter()
        for kind in (b"Write", b"Write", b"Read", b"Read"):
            counter.add(kind, 512)
        metrics = counter.summary()
        self.assertEqual(metrics["observed_labels"], 2)
        self.assertEqual(metrics["distinct_target_reads"], 1)
        self.assertEqual(metrics["read_first"], 1)
        self.assertEqual(metrics["write_first"], 1)

    def test_split_boundary_prevents_future_read_label(self):
        train, validation = WindowCounter(), WindowCounter()
        train.add(b"Write", 512)
        validation.add(b"Read", 512)
        self.assertEqual(train.summary()["observed_labels"], 0)
        self.assertEqual(train.summary()["unresolved_first_event"], 1)
        self.assertEqual(validation.summary()["observed_labels"], 0)

    def test_offsets_and_source_order_are_respected(self):
        counter = WindowCounter()
        for kind, offset in ((b"Read", 0), (b"Write", 0), (b"Write", 512), (b"Read", 0)):
            counter.add(kind, offset)
        metrics = counter.summary()
        self.assertEqual(metrics["observed_labels"], 1)
        self.assertEqual(metrics["read_first"], 1)
        self.assertEqual(metrics["unresolved_first_event"], 1)


if __name__ == "__main__":
    unittest.main()
