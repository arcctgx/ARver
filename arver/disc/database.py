"""Utilities for communicating with AccurateRip database."""

import struct
from dataclasses import dataclass
from typing import ClassVar, List

import requests

from arver import APPNAME, VERSION, URL


USER_AGENT_STRING = f'{APPNAME}/{VERSION} {URL}'
URL_BASE = 'http://www.accuraterip.com/accuraterip/'


@dataclass
class Header:
    """AccurateRip response header."""
    size: ClassVar[int] = 13
    num_tracks: int
    ar_id1: int
    ar_id2: int
    freedb_id: int

    @classmethod
    def from_bytes(cls, data):
        """Create Header object from initial bytes of provided binary data."""
        header_bytes = data[:Header.size]
        unpacked = struct.unpack('<BLLL', header_bytes)
        return cls(*unpacked)

    def __str__(self):
        full_id = f'0{self.num_tracks:02d}-{self.ar_id1:08x}-{self.ar_id2:08x}-{self.freedb_id:08x}'
        return f'disc id: {full_id}'


@dataclass
class Track:
    """AccurateRip track data."""
    size: ClassVar[int] = 9
    confidence: int
    checksum_v1: int
    checksum_v2: int

    @classmethod
    def from_bytes(cls, data):
        """Create Track object from initial bytes of provided binary data."""
        track_bytes = data[:Track.size]
        unpacked = struct.unpack('<BLL', track_bytes)
        return cls(*unpacked)

    def __str__(self):
        ar1 = f'{self.checksum_v1:08x}'
        ar2 = f'{self.checksum_v2:08x}'
        return f'v1: {ar1}\tv2: {ar2}\t(confidence: {self.confidence})'


@dataclass
class Response:
    """
    AccurateRip response decoded from binary format: consists of a Header object
    (which stores the number of tracks and three types of disc IDs), and a list
    of Track objects which store two AccurateRip checksums and their confidence.
    """
    header: Header
    tracks: List[Track]

    def __str__(self):
        str_ = []
        str_.append(str(self.header))
        for num, track in enumerate(self.tracks, start=1):
            str_.append(f'track {num:2d}:\t{str(track)}')
        return '\n'.join(str_)


class Fetcher:
    """Get AccurateRip data for specified disc."""
    def __init__(self, num_tracks, ar_id1, ar_id2, freedb_id):
        self._num_tracks = num_tracks
        self._ar_id1 = ar_id1
        self._ar_id2 = ar_id2
        self._freedb_id = freedb_id
        self._disc_data = bytes()

    def _make_url(self):
        dir_ = f'{self._ar_id1[-1]}/{self._ar_id1[-2]}/{self._ar_id1[-3]}/'
        file_ = f'dBAR-0{self._num_tracks:02d}-{self._ar_id1}-{self._ar_id2}-{self._freedb_id}.bin'
        return URL_BASE + dir_ + file_

    def _left_shift_data(self, num_bytes):
        """Left shift disc data by num_bytes (discard initial bytes)."""
        self._disc_data = self._disc_data[num_bytes:]

    def _is_valid_header(self, header):
        """Check if AccurateRip response header matches requested disc."""
        return header.num_tracks == self._num_tracks and \
            f'{header.ar_id1:08x}' == self._ar_id1 and \
            f'{header.ar_id2:08x}' == self._ar_id2 and \
            f'{header.freedb_id:08x}' == self._freedb_id

    def _parse_header(self):
        header = Header.from_bytes(self._disc_data)
        self._left_shift_data(Header.size)
        if not self._is_valid_header(header):
            raise ValueError('Unexpected AccurateRip response header')
        return header

    def _parse_track(self):
        track = Track.from_bytes(self._disc_data)
        self._left_shift_data(Track.size)
        return track

    def _parse_disc_data(self):
        responses = []

        while len(self._disc_data) > 0:
            header = self._parse_header()

            tracks = []
            for _ in range(header.num_tracks):
                track = self._parse_track()
                tracks.append(track)

            response = Response(header, tracks)
            responses.append(response)

        return responses

    def fetch(self):
        """Return a list of Response objects or None on error."""
        try:
            response = requests.get(self._make_url(), headers={'User-Agent': USER_AGENT_STRING})
            self._disc_data = response.content
            return self._parse_disc_data()
        except requests.HTTPError:
            return None
