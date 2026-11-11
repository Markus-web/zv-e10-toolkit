"""Passively summarize GP28 transitions using sender firmware capture command.

The Pico must run ``zve10_uart_od 15`` and remain idle. In that state GP28 is
an input with no pulls. Connect it to the camera-side signal being diagnosed,
plus a common ground. This tool never starts the carrier or reset output.
"""
import argparse
import json
import struct
import time

from pico_link import Link, SENDER_VERSION, safe_idle

CAPTURE = 0x0A
MAX_CAPTURE_EDGES = 64


def decode_capture(data):
    if len(data) < 2:
        raise ValueError('Short capture reply')
    count = int.from_bytes(data[:2], 'little')
    if count > MAX_CAPTURE_EDGES or len(data) != 2 + count * 5:
        raise ValueError('Malformed capture reply')

    edges = []
    previous_us = -1
    for offset in range(2, len(data), 5):
        delta_us, level = struct.unpack_from('<IB', data, offset)
        if delta_us < previous_us or level not in (0, 1):
            raise ValueError('Invalid capture edge')
        edges.append((delta_us, level))
        previous_us = delta_us
    return edges


def summarize(captures):
    intervals = []
    transitions = 0
    active = 0
    saturated = 0
    for edges in captures:
        transitions += len(edges)
        if edges:
            active += 1
        if len(edges) == MAX_CAPTURE_EDGES:
            saturated += 1
        intervals.extend(edges[index][0] - edges[index - 1][0]
                         for index in range(1, len(edges)))
    return {
        'capture_windows': len(captures),
        'active_windows': active,
        'saturated_windows': saturated,
        'transitions': transitions,
        'min_edge_interval_us': min(intervals) if intervals else None,
        'max_edge_interval_us': max(intervals) if intervals else None,
    }


def run(port, duration):
    link = Link(port)
    captures = []
    try:
        version = link.exchange(1)
        if version != SENDER_VERSION:
            raise RuntimeError('Unexpected firmware (need zve10_uart_od 15)')
        before = link.status()
        if not safe_idle(before):
            raise RuntimeError('Monitor Pico must be idle input without pulls')

        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            captures.append(decode_capture(link.exchange(CAPTURE)))

        after = link.status()
        if not safe_idle(after):
            raise RuntimeError('Monitor Pico did not remain safely idle')
        result = summarize(captures)
        result.update({'firmware': version.decode(), 'duration_s': duration,
                       'safe_idle_before': True, 'safe_idle_after': True})
        return result
    finally:
        link.serial.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    parser.add_argument('--duration', type=float, default=20,
                        help='capture duration in seconds (default: 20)')
    args = parser.parse_args()
    if args.duration <= 0:
        parser.error('--duration must be positive')
    print(json.dumps(run(args.port, args.duration), indent=2), flush=True)


if __name__ == '__main__':
    main()
