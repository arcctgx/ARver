#!/usr/bin/env python3

"""Download disc info (including TOC) from MusicBrainz based on disc ID."""

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


def _get_disc_info(disc_id):
    musicbrainzngs.set_useragent(version.APPNAME, version.VERSION)

    try:
        disc_data = musicbrainzngs.get_releases_by_discid(disc_id)
    except musicbrainzngs.ResponseError:
        return None

    offsets = disc_data['disc']['offset-list']
    sectors = int(disc_data['disc']['sectors'])
    freedb_id = _calculate_freedb_id(offsets, sectors)
    accuraterip_ids = accuraterip.calculate_ids(offsets, sectors)

    info = {}
    info['discid'] = disc_data['disc']['id']
    info['freedb-id'] = freedb_id
    info['accuraterip-id'] = accuraterip_ids
    info['offset-list'] = offsets
    info['sectors'] = sectors

    return info


def main():
    if len(sys.argv) != 2:
        print(f'usage: {os.path.basename(sys.argv[0])} <discID>')
        sys.exit(1)

    disc_id = sys.argv[1]
    disc_info = _get_disc_info(disc_id)

    if disc_info:
        print(json.dumps(disc_info, indent=2))
    else:
        print(f'Failed to get disc info from discID "{disc_id}"!')


if __name__ == '__main__':
    main()
