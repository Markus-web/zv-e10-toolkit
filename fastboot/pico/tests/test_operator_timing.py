import io
import unittest

from operator_timing import countdown


class CountdownTests(unittest.TestCase):
    def test_countdown_prints_each_second_and_label(self):
        output = io.StringIO()
        sleeps = []

        countdown(3, 'NOW: reset pulse', sleep=sleeps.append, stream=output)

        self.assertEqual(output.getvalue(), '3\n2\n1\nNOW: reset pulse\n')
        self.assertEqual(sleeps, [1, 1, 1])

    def test_zero_seconds_prints_only_label(self):
        output = io.StringIO()

        countdown(0, 'NOW', sleep=self.fail, stream=output)

        self.assertEqual(output.getvalue(), 'NOW\n')

    def test_negative_seconds_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'non-negative'):
            countdown(-1, 'NOW')


if __name__ == '__main__':
    unittest.main()
