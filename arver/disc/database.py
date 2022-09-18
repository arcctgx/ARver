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
        self._disc_data = bytes()

    def _make_url(self):
        dirs = f'{self._ar1[-1]}/{self._ar1[-2]}/{self._ar1[-3]}/'
        file_name = f'dBAR-0{self._tracks:02d}-{self._ar1}-{self._ar2}-{self._freedb}.bin'
        return URL_BASE + dirs + file_name

    def _parse_header(self):
        chunk = self._disc_data[:13]
        self._disc_data = self._disc_data[13:]

        num_tracks, ar1, ar2, freedb = struct.unpack('<BLLL', chunk)
        print(f'{num_tracks}\t{ar1:08x}\t{ar2:08x}\t{freedb:08x}')

        if num_tracks != self._tracks or \
            f'{ar1:08x}' != self._ar1 or f'{ar2:08x}' != self._ar2 or \
            f'{freedb:08x}' != self._freedb:
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
