#!/usr/bin/env python3

"""Read disc IDs and TOC from a physical CD in drive."""

from arver.cd.disc import Disc


def main():
    disc = Disc.from_cd()

    if disc:
        print(disc)
    else:
        print('Failed to read disc info. Is there a CD in the drive?')


if __name__ == '__main__':
    main()
