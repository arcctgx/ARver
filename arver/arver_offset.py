"""
Detect possible sample offsets in a set of audio files.
"""

import argparse
from pprint import pprint

from arver.audio.checksums import get_frame450_checksums
from arver.version import version_string


def _parse_args():
    parser = argparse.ArgumentParser(description="""TODO offset detection""")

    parser.add_argument('rip_files',
                        nargs='+',
                        metavar='file',
                        help='audio file for calculating checksums')

    parser.add_argument('-v', '--version', action='version', version=version_string())

    return parser.parse_args()


def main():
    args = _parse_args()

    offsets = get_frame450_checksums(args.rip_files[0])
    hexoff = [(off[0], f'{off[1]:08x}') for off in offsets]
    pprint(hexoff)


if __name__ == '__main__':
    main()
