"""Utilities for communicating with AccurateRip database."""

import requests
from arver import APPNAME, VERSION, URL

USER_AGENT_STRING = f'{APPNAME}/{VERSION} ( {URL} )'
URL_BASE = 'http://www.accuraterip.com/accuraterip/'


class Response:
    """
    AccurateRip response decoded from binary format: number of tracks,
    two AccurateRip disc IDs and FreeDB disc ID followed by list of
    confidences and two AccurateRip checksums for each track.
    """
    def __repr__(self):
        return ''


class Fetcher:
    """Get AccurateRip data for specified disc."""
    def __init__(self, tracks, ar1, ar2, freedb):
        self._tracks = tracks
        self._ar1 = ar1
        self._ar2 = ar2
        self._freedb = freedb
        self.url = URL_BASE + self._dbar_prefix() + self._dbar_id() + '.bin'

    def _dbar_prefix(self):
        return f'{self._ar1[-1]}/{self._ar1[-2]}/{self._ar1[-3]}/'

    def _dbar_id(self):
        return f'dBAR-0{self._tracks:02d}-{self._ar1}-{self._ar2}-{self._freedb}'

    def _parse_binary_data(self, blob):
        print(blob)
        return []

    def fetch(self):
        """Return a list of Response objects or None on error."""
        try:
            data = requests.get(self.url, headers={'User-Agent': USER_AGENT_STRING})
            return self._parse_binary_data(data.content)
        except requests.HTTPError:
            return None
