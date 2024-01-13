"""
Display AccurateRip disc data stored in a dBAR binary file cached
by certain AccurateRip-aware CD rippers (e.g. EAC or Whipper).
"""

import argparse
import sys

from arver.disc.database import AccurateRipParser
from arver.version import version_string


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Display AccurateRip disc data cached in a dBAR file.""")

    parser.add_argument('dbar_file', nargs=1, help='cached AccurateRip response file')
    parser.add_argument('-v', '--version', action='version', version=version_string())

    return parser.parse_args()


def main():
    args = _parse_args()

    dbar_parser = AccurateRipParser(*args.dbar_file)
    disc = dbar_parser.parse()
    if disc is None:
        print('Failed to parse AccurateRip data file, exiting.')
        sys.exit(1)

    print(disc.summary())
    print()
    print(disc)


if __name__ == '__main__':
    main()
