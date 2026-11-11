import struct
import unittest

from monitor_line import decode_capture, summarize


def reply(*edges):
    return len(edges).to_bytes(2, 'little') + b''.join(
        struct.pack('<IB', delta, level) for delta, level in edges)


class DecodeCaptureTests(unittest.TestCase):
    def test_decodes_edges(self):
        self.assertEqual(decode_capture(reply((20, 0), (41, 1))),
                         [(20, 0), (41, 1)])

    def test_rejects_bad_length(self):
        with self.assertRaisesRegex(ValueError, 'Malformed'):
            decode_capture(b'\x01\x00')

    def test_rejects_non_monotonic_edges(self):
        with self.assertRaisesRegex(ValueError, 'Invalid'):
            decode_capture(reply((40, 0), (20, 1)))


class SummaryTests(unittest.TestCase):
    def test_reports_activity_and_intervals(self):
        result = summarize([[], [(10, 0), (31, 1), (52, 0)]])
        self.assertEqual(result['capture_windows'], 2)
        self.assertEqual(result['active_windows'], 1)
        self.assertEqual(result['transitions'], 3)
        self.assertEqual(result['min_edge_interval_us'], 21)
        self.assertEqual(result['max_edge_interval_us'], 21)


if __name__ == '__main__':
    unittest.main()
