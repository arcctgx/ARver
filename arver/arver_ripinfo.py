"""
Display properties of a set of audio files, including copy CRCs and
two types of AccurateRip checksums.
"""

import argparse
import sys

from arver.rip.rip import Rip
from arver.version import version_string


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Display properties and checksums of specified audio
        files. Calculation of AccurateRip checksums requires correct track
        sequence, so files must be specified in the correct order. Pre-gap
        track (HTOA) must not be included. Non-audio files and unsupported
        audio formats are quietly ignored.""")

    parser.add_argument('rip_files',
                        nargs='+',
                        metavar='file',
                        help='audio file for calculating checksums')

    parser.add_argument('-x',
                        '--exclude',
                        action='append',
                        metavar='pattern',
                        help='file name pattern to exclude')

    parser.add_argument('-v', '--version', action='version', version=version_string())

    return parser.parse_args()


def main():
    args = _parse_args()

    rip = Rip(args.rip_files, args.exclude)
    if len(rip) == 0:
        print('No audio files were loaded. Did you specify correct files?')
        sys.exit(1)

    print(rip.as_table())


if __name__ == '__main__':
    main()
