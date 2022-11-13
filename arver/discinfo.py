"""
Display information about compact disc in drive, or derived from
MusicBrainz disc ID. Download and display AccurateRip data of the CD.
"""

import argparse
import sys

from arver import VERSION
from arver.disc.disc import Disc


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Display information about compact disc in drive, or
        derived from MusicBrainz disc ID. Fetch and display AccurateRip data
        of the disc.""")

    parser.add_argument('-i',
                        '--disc-id',
                        metavar='disc_id',
                        nargs=1,
                        help='get disc TOC from MusicBrainz by disc ID')

    parser.add_argument('-v', '--version', action='version', version=VERSION)

    return parser.parse_args()


def _get_disc(disc_id):
    if disc_id is None:
        disc = Disc.from_cd()
    else:
        disc = Disc.from_disc_id(*disc_id)

    if disc is None:
        if disc_id is None:
            print('Could not read disc. Is there a CD in the drive?')
        else:
            print(f'Could not look up disc ID "{disc_id}", is it correct?')

    return disc


def main():
    args = _parse_args()
    disc = _get_disc(args.disc_id)

    if disc is None:
        print('Failed to get disc info, exiting.')
        sys.exit(1)

    print(disc)
    print()

    disc.fetch_accuraterip_data()
    if disc.accuraterip_data is None:
        print('Failed to download AccurateRip data, exiting.')
        sys.exit(2)

    n_resp = len(disc.accuraterip_data)
    plural = 's' if n_resp > 1 else ''
    print(f'Received {n_resp} AccurateRip response{plural}:\n')
    print(disc.accuraterip_data)


if __name__ == '__main__':
    main()
