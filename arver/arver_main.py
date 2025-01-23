"""Verify rip correctness using AccurateRip database."""

import argparse
import sys
import textwrap

from arver.disc.info import DiscInfo, get_disc_info
from arver.rip.rip import Rip
from arver.version import version_string


def _parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent("""\
        Verify a set of audio tracks against checksums from AccurateRip database.

        Disc TOC necessary for AccurateRip lookup is obtained either from reading a
        physical CD in drive (the default behavior, recommended if the disc contains
        data tracks), from MusicBrainz disc ID query, or is estimated from the lengths
        of provided audio tracks.

        Calculation of AccurateRip checksums requires correct track sequence, so the
        files must be specified in the correct order. Pregap track (HTOA) must not be
        included.

        Disc ID calculation requires information about the length of track one pregap,
        and of the data track, if they exist. This information cannot be derived from
        a set of ripped files, so options for specifying lengths of these tracks are
        available. They have no effect when the disc TOC is obtained from a physical
        CD or from MusicBrainz disc ID query."""))

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

    parser.add_argument('-p',
                        '--permissive',
                        action='store_true',
                        help='ignore mismatched track lengths')

    parser.add_argument('-x',
                        '--exclude',
                        action='append',
                        metavar='pattern',
                        help='file name pattern to exclude')

    parser.add_argument('-1',
                        '--use-arv1',
                        action='store_true',
                        help='use only ARv1 checksums for verification')

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
        print('Cannot verify, showing rip info instead.')
        print()
        print(rip.as_table())
        sys.exit(3)

    print(disc.accuraterip_data.summary())
    print()

    try:
        verdict = rip.verify(disc, args.permissive, args.use_arv1)
    except ValueError:
        print("Audio files don't match CD TOC, exiting.")
        sys.exit(4)

    print()
    print(verdict.as_table())
    print()
    print(verdict.summary())


if __name__ == '__main__':
    main()
