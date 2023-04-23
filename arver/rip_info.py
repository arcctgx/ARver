"""
Display properties of a set of WAV files, including copy CRCs and
two types of AccurateRip checksums.
"""

import argparse
import sys

from arver import VERSION
from arver.rip.rip import Rip


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
    parser.add_argument('-v', '--version', action='version', version=VERSION)

    return parser.parse_args()


def main():
    args = _parse_args()

    rip = Rip(args.rip_files)
    if len(rip) == 0:
        print('No WAV files were loaded. Did you specify correct files?')
        sys.exit(1)

    rip.calculate_checksums()
    print(rip)


if __name__ == '__main__':
    main()
