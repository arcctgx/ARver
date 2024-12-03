"""
Detect possible sample offsets in a set of audio files.
"""

import argparse
import sys
from pprint import pprint

from arver.audio.checksums import get_frame450_checksums
from arver.disc.info import DiscInfo, get_disc_info
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
    #print(disc.accuraterip_data)

    ####################################
    ### offset detection starts here ###
    ####################################

    disc_frame450_checksums = disc.accuraterip_data.make_dict(frame450=True)
    #pprint(raw_db)

    for num, track in enumerate(rip.tracks, start=1):
        print(num, track.path)

        # raw is a list of (offset, checksum) pairs. Convert it to a dict
        # {checksum: offset} so it's more convenient to work with. Omit all
        # zero checksums (either real silent samples or calculation errors).
        raw = get_frame450_checksums(track.path)
        offsets = {checksum: offset for (offset, checksum) in raw if checksum != 0}
        #print(len(offsets))
        #pprint(offsets)

        track_checksums = disc_frame450_checksums[num]
        #pprint(track)

        for checksum, meta in track_checksums.items():
            # Many responses contain frame 450 checksums equal to zero.
            # This can only mean "no data", so ignore these checksums.
            if checksum == 0:
                continue

            #print(f'Checking {k:08x}')
            try:
                offset = offsets[checksum]
                print(f'Possible pressing offset: {offset:+5d} (confidence: {meta["confidence"]})')
            except KeyError:
                pass

        print()


if __name__ == '__main__':
    main()
