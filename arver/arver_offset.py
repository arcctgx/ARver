"""Detect possible sample offsets in a set of audio files."""

import argparse
import sys

from arver.disc.info import DiscInfo, get_disc_info
from arver.rip.offset import find_pressing_offset
from arver.rip.rip import Rip
from arver.version import version_string


def _parse_args():
    parser = argparse.ArgumentParser(description="""TODO offset detection""")

    parser.add_argument('rip_files',
                        nargs='+',
                        metavar='file',
                        help='audio file for calculating checksums')

    toc_source = parser.add_mutually_exclusive_group()

    toc_source.add_argument('-d',
                            '--drive',
                            metavar='device_path',
                            help='read disc TOC from a CD in specified drive (e.g. /dev/sr0)')

    toc_source.add_argument('-i',
                            '--disc-id',
                            metavar='disc_id',
                            help='get disc TOC from MusicBrainz by disc ID query')

    toc_source.add_argument('-t',
                            '--track-lengths',
                            action='store_true',
                            help='derive disc TOC from the lengths of audio tracks')

    parser.add_argument('-x',
                        '--exclude',
                        action='append',
                        metavar='pattern',
                        help='file name pattern to exclude')

    parser.add_argument('-P',
                        '--pregap-length',
                        metavar='frames',
                        type=int,
                        default=0,
                        help='length of track one pregap in CDDA frames')

    parser.add_argument('-D',
                        '--data-length',
                        metavar='frames',
                        type=int,
                        default=0,
                        help='length of Enhanced CD data track in CDDA frames')

    parser.add_argument('-v', '--version', action='version', version=version_string())

    return parser.parse_args()


def main():
    args = _parse_args()

    rip = Rip(args.rip_files, args.exclude)
    if len(rip) == 0:
        print('No audio files were loaded. Did you specify correct files?')
        sys.exit(1)

    if args.track_lengths:
        disc = DiscInfo.from_track_lengths(rip.track_frames(), args.pregap_length, args.data_length)
    else:
        disc = get_disc_info(args.drive, args.disc_id)

    if disc is None:
        print('Failed to get disc info, exiting.')
        sys.exit(2)

    print(disc)
    print()

    disc.fetch_accuraterip_data()
    if disc.accuraterip_data is None:
        print('Failed to ger AccurateRip data, exiting.')
        sys.exit(3)

    print(disc.accuraterip_data.summary())
    print()

    find_pressing_offset(disc, rip)


if __name__ == '__main__':
    main()
