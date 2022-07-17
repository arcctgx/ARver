#!/usr/bin/env python3

"""Get Table of Contents (TOC) from a physical CD in drive."""

import json
import discid

import accuraterip


def _get_toc():
    try:
        disc = discid.read()
    except discid.DiscError:
        return None

    toc = {}
    toc['discid'] = disc.id
    toc['freedb-id'] = disc.freedb_id
    toc['offset-list'] = [track.offset for track in disc.tracks]
    toc['sectors'] = disc.sectors

    return toc


def main():
    toc = _get_toc()

    if toc:
        print(json.dumps(toc, indent=2))
        print('AccurateRip IDs:', accuraterip.calculate_ids(toc))
    else:
        print('Failed to get the table of contents. Is there a CD in the drive?')


if __name__ == '__main__':
    main()
