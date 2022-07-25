#!/usr/bin/env python3

"""Read disc info (including TOC) from a physical CD in drive."""

import json
import discid

import accuraterip


def _read_disc_info():
    try:
        disc = discid.read()
    except discid.DiscError:
        return None

    offsets = [track.offset for track in disc.tracks]
    sectors = disc.sectors
    accuraterip_ids = accuraterip.calculate_ids(offsets, sectors)

    info = {}
    info['discid'] = disc.id
    info['freedb-id'] = disc.freedb_id
    info['accuraterip-id'] = accuraterip_ids
    info['offset-list'] = offsets
    info['sectors'] = disc.sectors

    return info


def main():
    disc_info = _read_disc_info()

    if disc_info:
        print(json.dumps(disc_info, indent=2))
    else:
        print('Failed to read disc info. Is there a CD in the drive?')


if __name__ == '__main__':
    main()
