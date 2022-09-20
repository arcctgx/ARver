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


@dataclass
class Response:
    """
    AccurateRip response decoded from binary format: consists of a Header object
    (which stores the number of tracks and three types of disc IDs), and a list
    of Track objects which store two AccurateRip checksums and their confidence.
    """
    header: Header
    tracks: List[Track]


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

    def _parse_header(self):
        header = Header.from_bytes(self._disc_data)
        self._disc_data = self._disc_data[Header.size:]

        print(header)

        # TODO this sanity check should be a separate Fetcher method
        if header.num_tracks != self._num_tracks or \
            f'{header.ar_id1:08x}' != self._ar_id1 or \
            f'{header.ar_id2:08x}' != self._ar_id2 or \
            f'{header.freedb_id:08x}' != self._freedb_id:
            raise ValueError('Unexpected AccurateRip response header')

        return header

    def _parse_track(self):
        track = Track.from_bytes(self._disc_data)
        self._disc_data = self._disc_data[Track.size:]

        print(track)

    def _parse_disc_data(self):
        while len(self._disc_data) > 0:
            print(len(self._disc_data))
            print(self._disc_data.hex())

            header = self._parse_header()
            print(len(self._disc_data))
            print(self._disc_data.hex())

            for _ in range(header.num_tracks):
                self._parse_track()
                print(len(self._disc_data))
                print(self._disc_data.hex())

        return []

    def fetch(self):
        """Return a list of Response objects or None on error."""
        try:
            response = requests.get(self._make_url(), headers={'User-Agent': USER_AGENT_STRING})
            self._disc_data = response.content
            return self._parse_disc_data()
        except requests.HTTPError:
            return None
