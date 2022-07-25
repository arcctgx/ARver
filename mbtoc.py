#!/usr/bin/env python3

"""Get disc IDs and TOC from MusicBrainz data."""

import json
import os
import sys

import discid
import musicbrainzngs

import accuraterip
import version


def _calculate_freedb_id(offsets, leadout):
    disc = discid.put(1, len(offsets), leadout, offsets)
    return disc.freedb_id


def _get_disc_info(disc_id):
    musicbrainzngs.set_useragent(version.APPNAME, version.VERSION)

    try:
        disc_data = musicbrainzngs.get_releases_by_discid(disc_id)
    except musicbrainzngs.ResponseError:
        return None

    offsets = disc_data['disc']['offset-list']
    leadout = int(disc_data['disc']['sectors'])
    freedb_id = _calculate_freedb_id(offsets, leadout)
    accuraterip_ids = accuraterip.calculate_ids(offsets, leadout)

    info = {
        'id': {
            'discid': disc_data['disc']['id'],
            'freedb': freedb_id,
            'accuraterip': accuraterip_ids
        },
        'toc': {
            'tracks': len(offsets),
            'offsets': offsets,
            'leadout': leadout
        }
    }

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
