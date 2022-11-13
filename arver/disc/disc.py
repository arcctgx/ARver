"""
Representation of a Compact Disc for verification using AccurateRip database.
"""

import json

import discid
import musicbrainzngs

from arver import APPNAME, VERSION, URL
from arver.disc.id import freedb_id, accuraterip_ids
from arver.disc.database import AccurateRipFetcher
from arver.disc.utils import frames_to_msf, LEAD_IN_FRAMES


def _calculate_track_lengths(offsets, leadout):
    shifted = offsets[1:] + [leadout]
    frames = [shf - off for shf, off in zip(shifted, offsets)]
    msf = [frames_to_msf(frm) for frm in frames]
    return [{'frames': frm, 'msf': msf} for frm, msf in zip(frames, msf)]


def _get_htoa(offsets):
    htoa = None
    htoa_frames = offsets[0] - LEAD_IN_FRAMES

    if htoa_frames > 0:
        htoa = {'frames': htoa_frames, 'msf': frames_to_msf(htoa_frames)}

    return htoa


def _read_disc_info():
    try:
        disc = discid.read()
    except discid.DiscError:
        return None

    offsets = [track.offset for track in disc.tracks]
    leadout = disc.sectors
    htoa = _get_htoa(offsets)

    return {
        'id': {
            'discid': disc.id,
            'freedb': disc.freedb_id,
            'accuraterip': accuraterip_ids(offsets, disc.sectors)
        },
        'toc': {
            'tracks': len(offsets),
            'offsets': offsets,
            'leadout': leadout,
            'htoa': htoa,
            'track-lengths': _calculate_track_lengths(offsets, leadout)
        }
    }


def _get_musicbrainz_disc_info(disc_id):
    musicbrainzngs.set_useragent(APPNAME, VERSION, URL)

    try:
        response = musicbrainzngs.get_releases_by_discid(disc_id)
    except musicbrainzngs.ResponseError:
        return None

    offsets = response['disc']['offset-list']
    leadout = int(response['disc']['sectors'])
    htoa = _get_htoa(offsets)

    return {
        'id': {
            'discid': response['disc']['id'],
            'freedb': freedb_id(offsets, leadout),
            'accuraterip': accuraterip_ids(offsets, leadout)
        },
        'toc': {
            'tracks': len(offsets),
            'offsets': offsets,
            'leadout': leadout,
            'htoa': htoa,
            'track-lengths': _calculate_track_lengths(offsets, leadout)
        }
    }


class Disc:
    """Class representing a Compact Disc to verify."""

    def __init__(self, disc_info):
        self._disc_info = disc_info
        self._ar1 = disc_info['id']['accuraterip'][0]
        self._ar2 = disc_info['id']['accuraterip'][1]
        self._freedb = disc_info['id']['freedb']
        self.tracks = disc_info['toc']['tracks']
        self.accuraterip_data = None

    def _format_tracklist(self):
        str_ = ''
        str_ += 'track     length     frames\n'
        str_ += '-----    --------    ------\n'

        htoa = self._disc_info['toc']['htoa']
        if htoa is not None:
            str_ += f' HTOA    {htoa["msf"]:>8s}    {htoa["frames"]:>6d}\n'

        for num, trk in enumerate(self._disc_info['toc']['track-lengths'], start=1):
            str_ += f'{num:>5d}    {trk["msf"]:>8s}    {trk["frames"]:>6d}\n'

        return str_.strip()

    def __str__(self):
        str_ = ''
        str_ += f'AccurateRip disc ID: 0{self.tracks:02d}-{self._ar1}-{self._ar2}-{self._freedb}\n'
        str_ += f'MusicBrainz disc ID: {self._disc_info["id"]["discid"]}\n'
        str_ += '\n' + self._format_tracklist()
        return str_

    def __repr__(self):
        return json.dumps(self._disc_info, indent=2)

    @classmethod
    def from_cd(cls):
        """Return Disc instance based on CD in drive, or None on error."""
        disc_info = _read_disc_info()
        if disc_info is not None:
            return cls(disc_info)
        return None

    @classmethod
    def from_disc_id(cls, disc_id):
        """Return Disc instance corresponding to MusicBrainz disc ID, or None on error."""
        disc_info = _get_musicbrainz_disc_info(disc_id)
        if disc_info is not None:
            return cls(disc_info)
        return None

    def fetch_accuraterip_data(self):
        """Download AccurateRip disc data for a specified Compact Disc."""
        fetcher = AccurateRipFetcher(self.tracks, self._ar1, self._ar2, self._freedb)
        self.accuraterip_data = fetcher.fetch()
