"""Pulse GP27 -> 470R -> camera D+ (A6); no carrier, no records.

Use it to stop the 1L7S blink and return the camera to normal boot without
removing the battery. Requires the v15 firmware.
"""
import argparse
import struct
import time
from pico_link import (Link, SENDER_VERSION, decode_reset_observation,
                       safe_idle)
from operator_timing import countdown

def pulse_resets(link, pulses=1, interval=1.0, pulse_us=None,
                 sleep=time.sleep):
    """Issue an explicit bounded pulse train for reset-line diagnostics."""
    observations = []
    body = b'' if pulse_us is None else struct.pack('<I', pulse_us)
    for index in range(pulses):
        observation = decode_reset_observation(link.exchange(2, body))
        if observation:
            observations.append(observation)
        if index + 1 < pulses:
            sleep(interval)
    return observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--countdown', type=int, default=0, metavar='SECONDS',
                        help='operator-visible delay before the reset pulse')
    parser.add_argument('--pulses', type=int, default=1,
                        help='number of reset pulses, 1-20 (default: 1)')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='seconds between pulses (default: 1.0)')
    parser.add_argument('--pulse-us', type=int,
                        help='diagnostic width, 10-100000 us; default 10 us')
    args = parser.parse_args()
    if args.countdown < 0:
        parser.error('--countdown must be non-negative')
    if not 1 <= args.pulses <= 20:
        parser.error('--pulses must be between 1 and 20')
    if args.interval < 0:
        parser.error('--interval must be non-negative')
    if args.pulse_us is not None and not 10 <= args.pulse_us <= 100000:
        parser.error('--pulse-us must be between 10 and 100000')

    link = Link(args.port)
    try:
        if link.exchange(1) != SENDER_VERSION:
            raise RuntimeError('Unexpected firmware (need zve10_uart_od 15)')
        before = link.status()
        if not safe_idle(before):
            raise RuntimeError('Pico must be idle input without pulls')
        print('before:', before, flush=True)
        countdown(args.countdown, f'NOW: {args.pulses} reset pulse(s)')
        observations = pulse_resets(link, args.pulses, args.interval,
                                    args.pulse_us)
        print(f'RESET PULSED {args.pulses} time(s). Carrier is off; '
              'the camera should boot normally.', flush=True)
        if observations:
            print('pad observations:', observations, flush=True)
        after = link.status()
        if not safe_idle(after):
            raise RuntimeError('Pico did not return to idle input')
        print('after :', after, flush=True)
    finally:
        try:
            link.exchange(3, b'\x00')
        except Exception:
            pass
        link.serial.close()


if __name__ == '__main__':
    main()
