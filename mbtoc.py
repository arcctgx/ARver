#!/usr/bin/env python3

"""Get table of contents (TOC) from MusicBrainz disc ID."""

import json
import os
import sys

import discid
import musicbrainzngs

import accuraterip
import version


def _calculate_freedb_id(offsets, sectors):
    disc = discid.put(1, len(offsets), sectors, offsets)
    return disc.freedb_id


def _get_toc(disc_id):
    musicbrainzngs.set_useragent(version.APPNAME, version.VERSION)

    try:
        disc_data = musicbrainzngs.get_releases_by_discid(disc_id)
    except musicbrainzngs.ResponseError:
        return None

    offsets = disc_data['disc']['offset-list']
    sectors = int(disc_data['disc']['sectors'])
    freedb_id = _calculate_freedb_id(offsets, sectors)
    accuraterip_ids = accuraterip.calculate_ids(offsets, sectors)

    toc = {}
    toc['discid'] = disc_data['disc']['id']
    toc['freedb-id'] = freedb_id
    toc['accuraterip-id'] = accuraterip_ids
    toc['offset-list'] = offsets
    toc['sectors'] = sectors

    return toc


def main():
    if len(sys.argv) != 2:
        print(f'usage: {os.path.basename(sys.argv[0])} <discID>')
        sys.exit(1)

    disc_id = sys.argv[1]
    toc = _get_toc(disc_id)

    if toc:
        print(json.dumps(toc, indent=2))
    else:
        print(f'Failed to get CD data matching discID "{disc_id}"!')


if __name__ == '__main__':
    main()
