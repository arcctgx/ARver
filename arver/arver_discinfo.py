"""
Display information about compact disc in drive, or derived from
MusicBrainz disc ID. Download and display AccurateRip data of the CD.
"""

import argparse
import sys

from arver.disc.info import get_disc_info
from arver.version import version_string


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Display information about compact disc in drive, or
        derived from MusicBrainz disc ID. Fetch and display AccurateRip data
        of the disc.""")

    toc_source = parser.add_mutually_exclusive_group()

    toc_source.add_argument('-d',
                            '--drive',
                            metavar='device_path',
                            help='read disc TOC from a CD in specified drive (e.g. /dev/sr0)')

    toc_source.add_argument('-i',
                            '--disc-id',
                            metavar='disc_id',
                            help='get disc TOC from MusicBrainz by disc ID query')

    parser.add_argument('-v', '--version', action='version', version=version_string())

    return parser.parse_args()


def main():
    args = _parse_args()
    disc = get_disc_info(args.drive, args.disc_id)

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
    print(disc.accuraterip_data)


if __name__ == '__main__':
    main()
