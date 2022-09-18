"""Utilities for communicating with AccurateRip database."""

import struct
from dataclasses import dataclass
from typing import List

import requests

from arver import APPNAME, VERSION, URL


USER_AGENT_STRING = f'{APPNAME}/{VERSION} {URL}'
URL_BASE = 'http://www.accuraterip.com/accuraterip/'


@dataclass
class Track:
    """AccurateRip track data."""
    confidence: int
    ar1: int
    ar2: int


@dataclass
class Response:
    """
    AccurateRip response decoded from binary format: number of tracks,
    two AccurateRip disc IDs and FreeDB disc ID followed by list of
    confidences and two AccurateRip checksums for each track.
    """
    num_tracks: int
    ar1: int
    ar2: int
    freedb: int
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
        chunk = self._disc_data[:13]
        self._disc_data = self._disc_data[13:]

        num_tracks, ar_id1, ar_id2, freedb_id = struct.unpack('<BLLL', chunk)
        print(f'{num_tracks}\t{ar_id1:08x}\t{ar_id2:08x}\t{freedb_id:08x}')

        if num_tracks != self._num_tracks or \
            f'{ar_id1:08x}' != self._ar_id1 or f'{ar_id2:08x}' != self._ar_id2 or \
            f'{freedb_id:08x}' != self._freedb_id:
            raise ValueError('Unexpected AccurateRip response header')

        return num_tracks

    def _parse_track(self):
        chunk = self._disc_data[:9]
        self._disc_data = self._disc_data[9:]

        confidence, checksum_v1, checksum_v2 = struct.unpack('<BLL', chunk)
        print(f'{confidence}\t{checksum_v1:08x}\t{checksum_v2:08x}')

    def _parse_disc_data(self):
        while len(self._disc_data) > 0:
            print(len(self._disc_data))
            print(self._disc_data.hex())

            num_tracks = self._parse_header()
            print(len(self._disc_data))
            print(self._disc_data.hex())

            for _ in range(num_tracks):
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
