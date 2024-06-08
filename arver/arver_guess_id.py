"""Guess AccurateRip disc ID from a set of audio files."""

import argparse
import sys

from arver.disc.info import DiscInfo
from arver.rip.rip import Rip
from arver.version import version_string


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Guess AccurateRip disc ID from a set of audio files.
        EXPERIMENTAL.""")

    parser.add_argument('rip_files',
                        nargs='+',
                        metavar='file',
                        help='audio files for disc ID calculation')

    parser.add_argument('-d',
                        '--data-length',
                        metavar='frames',
                        type=int,
                        default=0,
                        help='length of Enhanced CD data track in CDDA frames')

    parser.add_argument('-p',
                        '--pregap-length',
                        metavar='frames',
                        type=int,
                        default=0,
                        help='length of track 1 pregap in CDDA frames')

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

    disc = DiscInfo.from_track_frames(rip.track_frames(), args.pregap_length, args.data_length)

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
