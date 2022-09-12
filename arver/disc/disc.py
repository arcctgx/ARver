"""
AccurateRip Disc.
"""

import json

import discid
import musicbrainzngs

from arver.disc.accuraterip_id import calculate_ids
from arver.version import APPNAME, VERSION

URL_BASE = 'http://www.accuraterip.com/accuraterip/'


def _read_disc_info():
    try:
        disc = discid.read()
    except discid.DiscError:
        return None

    offsets = [track.offset for track in disc.tracks]
    accuraterip_ids = calculate_ids(offsets, disc.sectors)

    info = {
        'id': {
            'discid': disc.id,
            'freedb': disc.freedb_id,
            'accuraterip': accuraterip_ids
        },
        'toc': {
            'tracks': len(offsets),
            'offsets': offsets,
            'leadout': disc.sectors
        }
    }

    return info


def _calculate_freedb_id(offsets, leadout):
    disc = discid.put(1, len(offsets), leadout, offsets)
    return disc.freedb_id


def _get_musicbrainz_disc_info(disc_id):
    musicbrainzngs.set_useragent(APPNAME, VERSION)

    try:
        disc_data = musicbrainzngs.get_releases_by_discid(disc_id)
    except musicbrainzngs.ResponseError:
        return None

    offsets = disc_data['disc']['offset-list']
    leadout = int(disc_data['disc']['sectors'])
    freedb_id = _calculate_freedb_id(offsets, leadout)
    accuraterip_ids = calculate_ids(offsets, leadout)

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


class Disc:
    """Class representing a Compact Disc to verify."""
    def __init__(self, disc_data):
        self._data = disc_data
        self.tracks = disc_data['toc']['tracks']
        self.ar1 = disc_data['id']['accuraterip'][0]
        self.ar2 = disc_data['id']['accuraterip'][1]
        self.freedb = disc_data['id']['freedb']
        self.responses = []

    def __repr__(self):
        return json.dumps(self._data, indent=2)

    @classmethod
    def from_cd(cls):
        """Return Disc instance based on CD in drive, or None on error."""
        disc_data = _read_disc_info()
        if disc_data:
            return cls(disc_data)
        return None

    @classmethod
    def from_disc_id(cls, disc_id):
        """Return Disc instance corresponding to MusicBrainz disc ID, or None on error."""
        disc_data = _get_musicbrainz_disc_info(disc_id)
        if disc_data:
            return cls(disc_data)
        return None

    def _dbar_prefix(self):
        return f'{self.ar1[-1]}/{self.ar1[-2]}/{self.ar1[-3]}/'

    def _dbar_id(self):
        return f'dBAR-0{self.tracks:02d}-{self.ar1}-{self.ar2}-{self.freedb}'

    def get_responses(self):
        """Download AccurateRip responses for specified CD."""
        url = URL_BASE + self._dbar_prefix() + self._dbar_id()
        print(url)
        raise NotImplementedError


class Response:
    """AccurateRip response decoded from binary format."""
