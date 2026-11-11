import unittest

from reset_only import pulse_resets


class FakeLink:
    def __init__(self):
        self.commands = []

    def exchange(self, command, body=b''):
        self.commands.append((command, body))
        return b'\x01\x00\x01\x05'


class PulseResetTests(unittest.TestCase):
    def test_pulse_train_has_bounded_intervals(self):
        link = FakeLink()
        sleeps = []

        observations = pulse_resets(
            link, pulses=3, interval=0.5, sleep=sleeps.append)

        self.assertEqual(link.commands, [(2, b''), (2, b''), (2, b'')])
        self.assertEqual(sleeps, [0.5, 0.5])
        self.assertEqual(observations, [{
            'before': 1, 'during': 0, 'after': 1, 'gpio_function': 5,
        }] * 3)

    def test_old_firmware_empty_reply_remains_supported(self):
        link = FakeLink()
        link.exchange = lambda command, body=b'': b''

        self.assertEqual(pulse_resets(link), [])

    def test_rejects_malformed_observation(self):
        link = FakeLink()
        link.exchange = lambda command, body=b'': b'\x01'

        with self.assertRaisesRegex(ValueError, 'Malformed'):
            pulse_resets(link)

    def test_encodes_diagnostic_pulse_width(self):
        link = FakeLink()

        pulse_resets(link, pulse_us=10000)

        self.assertEqual(link.commands, [(2, b'\x10\x27\x00\x00')])


if __name__ == '__main__':
    unittest.main()
