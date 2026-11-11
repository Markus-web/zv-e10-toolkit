"""Inspect v15 sender firmware and idle pin status without sending camera records."""
import argparse
import json
from pico_link import Link, SENDER_VERSION, safe_idle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', required=True)
    args = parser.parse_args()
    link = Link(args.port)
    try:
        version = link.exchange(1)
        if version != SENDER_VERSION:
            raise ValueError('Expected zve10_uart_od 15, received ' + repr(version))
        status = link.status()
        if not safe_idle(status):
            raise ValueError('Sender is not idle with open-drain configuration')
        print(json.dumps({'firmware': version.decode(), 'status': status}, indent=2))
    finally:
        link.serial.close()


if __name__ == '__main__':
    main()
