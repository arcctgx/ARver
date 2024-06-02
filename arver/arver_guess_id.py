"""Guess AccurateRip disc ID from a set of audio files."""

import argparse
import sys
from typing import List

from arver.disc.database import AccurateRipFetcher
from arver.disc.fingerprint import accuraterip_ids, freedb_id
from arver.disc.info import ENHANCED_CD_DATA_TRACK_GAP
from arver.disc.utils import LEAD_IN_FRAMES
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


def _guess_disc_id(track_frames: List[int], pregap_length: int = 0, data_length: int = 0) -> str:
    print('track_frames:', track_frames)

    initial_offset = LEAD_IN_FRAMES + pregap_length
    print('pregap_length:', pregap_length)

    lba_offsets = [initial_offset]
    for length in track_frames[:-1]:
        lba_offsets.append(length + lba_offsets[-1])

    leadout = lba_offsets[-1] + track_frames[-1]
    if data_length > 0:
        # leadout begins after the data track, and there's a gap before the data:
        leadout += ENHANCED_CD_DATA_TRACK_GAP + data_length

    print('lba_offsets:', lba_offsets)
    print('leadout:', leadout)

    tracks = len(lba_offsets)

    freedb = freedb_id(lba_offsets, leadout)
    if data_length > 0:
        # we must include the data track in FreeDB ID calculation:
        data_track_offset = lba_offsets[-1] + track_frames[-1] + ENHANCED_CD_DATA_TRACK_GAP
        print('data_track_offset:', data_track_offset)
        freedb = freedb_id(lba_offsets + [data_track_offset], leadout)

    # ...but we don't use data track for calculating AccurateRip IDs, even if it exists.
    accuraterip = accuraterip_ids(lba_offsets, leadout)

    disc_id = f'{tracks:03d}-{accuraterip[0]}-{accuraterip[1]}-{freedb}'
    print('disc_id:', disc_id)

    return disc_id


def main():
    args = _parse_args()

    rip = Rip(args.rip_files, args.exclude)
    if len(rip) == 0:
        print('No audio files were loaded. Did you specify correct files?')
        sys.exit(1)

    disc_id = _guess_disc_id(rip.track_frames(), args.pregap_length, args.data_length)
    fetcher = AccurateRipFetcher.from_id(disc_id)
    accuraterip_data = fetcher.fetch()

    if accuraterip_data is None:
        sys.exit(2)

    print()
    print(accuraterip_data.summary())
    print()
    print(accuraterip_data)


if __name__ == '__main__':
    main()
