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
    def __init__(self, tracks, ar1, ar2, freedb):
        self._tracks = tracks
        self._ar1 = ar1
        self._ar2 = ar2
        self._freedb = freedb
        self.url = URL_BASE + self._dbar_prefix() + self._dbar_id() + '.bin'
        self.response = bytes()

    def _dbar_prefix(self):
        return f'{self._ar1[-1]}/{self._ar1[-2]}/{self._ar1[-3]}/'

    def _dbar_id(self):
        return f'dBAR-0{self._tracks:02d}-{self._ar1}-{self._ar2}-{self._freedb}'

    def _parse_header(self):
        chunk = self.response[:13]
        self.response = self.response[13:]

        num_tracks = chunk[0]
        ar1 = struct.unpack('<L', chunk[1:5])[0]
        ar2 = struct.unpack('<L', chunk[5:9])[0]
        freedb = struct.unpack('<L', chunk[9:13])[0]

        print(f'{self._tracks}\t{self._ar1}\t{self._ar2}\t{self._freedb}')
        print(f'{num_tracks}\t{ar1:08x}\t{ar2:08x}\t{freedb:08x}')

        if num_tracks != self._tracks or \
            f'{ar1:08x}' != self._ar1 or f'{ar2:08x}' != self._ar2 or \
            f'{freedb:08x}' != self._freedb:
            raise ValueError('Unexpected content of AccurateRip response')

        return num_tracks

    def _parse_track(self):
        chunk = self.response[0:9]
        self.response = self.response[9:]

        confidence = chunk[0]
        checksum_v1 = struct.unpack('<L', chunk[1:5])[0]
        checksum_v2 = struct.unpack('<L', chunk[5:9])[0]
        print(f'{confidence}\t{checksum_v1:08x}\t{checksum_v2:08x}')

    def _parse_response(self):
        print(len(self.response))
        print(self.response.hex())

        num_tracks = self._parse_header()
        print(len(self.response))
        print(self.response.hex())

        for _ in range(num_tracks):
            self._parse_track()
            print(len(self.response))
            print(self.response.hex())

        return []

    def fetch(self):
        """Return a list of Response objects or None on error."""
        try:
            response = requests.get(self.url, headers={'User-Agent': USER_AGENT_STRING})
            self.response = response.content
            return self._parse_response()
        except requests.HTTPError:
            return None
