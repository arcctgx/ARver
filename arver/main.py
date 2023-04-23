"""
Verify rip correctness using AccurateRip database.
"""

import argparse
import sys

from arver import VERSION
from arver.disc_info import get_disc
from arver.rip.rip import Rip


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Verify a set of audio files against checksums from
        AccurateRip database. Disc TOC necessary for AccurateRip lookup is
        obtained either from a physical CD in drive (recommended if disc has
        data tracks), or from MusicBrainz disc ID (-i option). Calculation of
        AccurateRip checksums requires correct track sequence, so files must
        be specified in the correct order. Pre-gap track (HTOA) must not be
        included.""")

    parser.add_argument('rip_files',
                        nargs='+',
                        metavar='file',
                        help='audio file for calculating checksums')

    parser.add_argument('-i',
                        '--disc-id',
                        metavar='disc_id',
                        nargs=1,
                        help='get disc TOC from MusicBrainz by disc ID')

    parser.add_argument('-v', '--version', action='version', version=VERSION)

    return parser.parse_args()


def main():
    args = _parse_args()
    disc = get_disc(args.disc_id)

    if disc is None:
        print('Failed to get disc info, exiting.')
        sys.exit(1)

    print(disc)
    print()

    disc.fetch_accuraterip_data()
    if disc.accuraterip_data is None:
        print('Failed to download AccurateRip data, exiting.')
        sys.exit(2)

    print(disc.accuraterip_data.summary())
    print()

    rip = Rip(args.rip_files)
    if len(rip) == 0:
        print('No WAV files were loaded. Did you specify correct files?')
        sys.exit(3)

    rip.calculate_checksums()
    verdict = rip.verify(disc)

    print()
    print(verdict.as_table())
    print()
    print(verdict.summary())


if __name__ == '__main__':
    main()
