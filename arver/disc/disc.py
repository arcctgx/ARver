"""
AccurateRip Disc.
"""

import json

import discid
import musicbrainzngs

from arver import APPNAME, VERSION, URL
from arver.disc.id import freedb_id, accuraterip_ids
from arver.disc.database import Fetcher


def _read_disc_info():
    try:
        disc = discid.read()
    except discid.DiscError:
        return None

    offsets = [track.offset for track in disc.tracks]

    info = {
        'id': {
            'discid': disc.id,
            'freedb': disc.freedb_id,
            'accuraterip': accuraterip_ids(offsets, disc.sectors)
        },
        'toc': {
            'tracks': len(offsets),
            'offsets': offsets,
            'leadout': disc.sectors
        }
    }

    return info


def _get_musicbrainz_disc_info(disc_id):
    musicbrainzngs.set_useragent(APPNAME, VERSION, URL)

    try:
        disc_data = musicbrainzngs.get_releases_by_discid(disc_id)
    except musicbrainzngs.ResponseError:
        return None

    offsets = disc_data['disc']['offset-list']
    leadout = int(disc_data['disc']['sectors'])

    info = {
        'id': {
            'discid': disc_data['disc']['id'],
            'freedb': freedb_id(offsets, leadout),
            'accuraterip': accuraterip_ids(offsets, leadout)
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
        self._ar1 = disc_data['id']['accuraterip'][0]
        self._ar2 = disc_data['id']['accuraterip'][1]
        self._freedb = disc_data['id']['freedb']
        self.tracks = disc_data['toc']['tracks']
        self.responses = None

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

    def get_responses(self):
        """Download AccurateRip responses for specified CD."""
        fetcher = Fetcher(self.tracks, self._ar1, self._ar2, self._freedb)
        self.responses = fetcher.fetch()
