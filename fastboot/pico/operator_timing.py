"""Operator-visible timing helpers for physical-camera commands."""

import sys
import time


def countdown(seconds, label, sleep=time.sleep, stream=sys.stdout):
    """Print a flushed one-second countdown followed by an action label."""
    if seconds < 0:
        raise ValueError('countdown must be non-negative')
    for remaining in range(seconds, 0, -1):
        print(remaining, file=stream, flush=True)
        sleep(1)
    print(label, file=stream, flush=True)
