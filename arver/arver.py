"""
Verify the set of WAV files ripped from CD.
"""

import argparse
import sys

from arver.rip.rip import Rip


def _parse_args():
    parser = argparse.ArgumentParser(
        description="""Calculate AccurateRip checksums of WAV files and compare
        calculated checksums with ones downloaded from AccurateRip database.""")

    parser.add_argument('wav_files', metavar='wav_file', nargs='+',
        help='WAV file to verify')

    toc_sources = parser.add_mutually_exclusive_group()
    toc_sources.add_argument('-d', '--drive',
        help='get TOC from CD in drive')
    toc_sources.add_argument('-i', '--disc-id',
        help='get TOC from MusicBrainz by Disc ID')

    return parser.parse_args()


def main():
    args = _parse_args()
    print(Rip(args.wav_files))


if __name__ == '__main__':
    main()
