"""
Display information about compact disc in drive, or derived from
MusicBrainz disc ID. Download and display AccurateRip data of the CD.
"""

import argparse
import sys

from arver.disc.disc import Disc


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Display information about compact disc in drive, or derived
        from MusicBrainz disc ID. Download and display AccurateRip data of the disc.""")

    parser.add_argument('-d', '--disc-id', nargs=1,
        help='get TOC from MusicBrainz by disc ID')

    return parser.parse_args()


def main():
    args = _parse_args()

    if args.disc_id is None:
        disc = Disc.from_cd()
    else:
        disc_id = args.disc_id[0]
        disc = Disc.from_disc_id(disc_id)

    if disc is None:
        if args.disc_id is None:
            print('Could not read disc. Is there a CD in the drive?')
        else:
            print(f'Could not look up disc ID "{disc_id}", is it correct?')

        print('Failed to get disc info, exiting.')
        sys.exit(1)

    print(disc)
    print()

    disc.fetch_disc_data()
    if disc.disc_data is None:
        print('Failed to download AccurateRip data, exiting.')
        sys.exit(2)

    print(disc.disc_data)


if __name__ == '__main__':
    main()
