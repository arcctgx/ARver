"""Get disc IDs and TOC from MusicBrainz data."""

import os
import sys

from arver.cd.disc import Disc


def main():
    if len(sys.argv) != 2:
        print(f'usage: {os.path.basename(sys.argv[0])} <discID>')
        sys.exit(1)

    disc_id = sys.argv[1]
    disc = Disc.from_disc_id(disc_id)

    if disc:
        print(disc)
    else:
        print(f'Failed to get disc info from discID "{disc_id}"!')


if __name__ == '__main__':
    main()
