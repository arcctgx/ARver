"""Utilities for communicating with AccurateRip database."""

import json
import struct
from dataclasses import dataclass
from typing import ClassVar, List

import requests

from arver import APPNAME, VERSION, URL


USER_AGENT_STRING = f'{APPNAME}/{VERSION} {URL}'
URL_BASE = 'http://www.accuraterip.com/accuraterip/'


@dataclass
class Header:
    """
    AccurateRip response header. Consists of the number of tracks, two types
    of AccurateRip disc IDs, and a FreeDB disc ID.
    """
    size: ClassVar[int] = 13
    num_tracks: int
    ar_id1: int
    ar_id2: int
    freedb_id: int

    @classmethod
    def from_bytes(cls, data):
        """
        Create Header object from the initial bytes of provided binary data. The data
        is little endian: number of tracks is an unsigned byte, and the three disc IDs
        are unsigned long integers.
        """
        header_bytes = data[:Header.size]
        unpacked = struct.unpack('<BLLL', header_bytes)
        return cls(*unpacked)

    def __str__(self):
        return f'0{self.num_tracks:02d}-{self.ar_id1:08x}-{self.ar_id2:08x}-{self.freedb_id:08x}'


@dataclass
class Track:
    """
    AccurateRip track data. Consists of two AccurateRip checksums and corresponding
    confidence value.
    """
    size: ClassVar[int] = 9
    confidence: int
    checksum_v1: int
    checksum_v2: int

    @classmethod
    def from_bytes(cls, data):
        """
        Create Track object from the initial bytes of provided binary data. The data is
        little endian: confidence is an unsigned byte, and the two AccurateRip checksums
        are unsigned long integers.
        """
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
    which stores the number of tracks and three types of disc IDs, and a list of
    Track objects which store two AccurateRip checksums and their confidence.
    """
    header: Header
    tracks: List[Track]

    def __str__(self):
        str_ = []
        str_.append(f'disc id: {self.header}')
        for num, track in enumerate(self.tracks, start=1):
            str_.append(f'track {num:2d}:\t{track}')
        return '\n'.join(str_)


@dataclass
class DiscData:
    """
    A collection of all Response objects received from AccurateRip database
    for requested disc.
    """
    responses: List[Response]

    def __str__(self):
        str_ = ''
        for num, response in enumerate(self.responses, start=1):
            str_ += f'AccurateRip response {num}:\n'
            str_ += str(response)
            str_ += '\n\n'

        return str_.strip()

    def __repr__(self):
        return json.dumps(self.make_dict(), indent=2)

    def make_dict(self):
        """
        Convert DiscData object to a dictionary for easy lookup of checksums during
        file verification. The conversion is "lossy": AccurateRip checksums equal to
        zero and with zero confidence are omitted.

        Resulting dictionary has the following structure:

        {
            "1": {
                "checksum_1": {
                    "confidence": X,
                    "version": Y,
                    "response": Z
                },
                "checksum_2": {
                    ...
                },
                ...
            },
            "2": {
                ...
            },
            ...
        }

        Conversion assumes that checksums other than zero are unique in scope of
        one track. If this is not the casse, lower confidence value from later
        response may overwrite higher confidence value from earlier response.
        """
        data = {}

        num_responses = len(self.responses)
        num_tracks = self.responses[0].header.num_tracks

        for trk in range(num_tracks):
            index = trk + 1
            data[index] = {}

            for rsp in range(num_responses):
                track = self.responses[rsp].tracks[trk]

                if track.confidence == 0:
                    continue

                if track.checksum_v1 != 0:
                    data[index][track.checksum_v1] = {
                        'confidence': track.confidence,
                        'version': 1,
                        'response': rsp + 1,
                    }

                if track.checksum_v2 != 0:
                    data[index][track.checksum_v2] = {
                        'confidence': track.confidence,
                        'version': 2,
                        'response': rsp + 1
                    }

        return data


class Fetcher:
    """
    Class for fetching AccurateRip data of a Compact Disc, parsing the
    binary data and representing AccurateRip responses in a usable form.
    """
    def __init__(self, num_tracks, ar_id1, ar_id2, freedb_id):
        self._num_tracks = num_tracks
        self._ar_id1 = ar_id1
        self._ar_id2 = ar_id2
        self._freedb_id = freedb_id
        self._disc_data = bytes()

    def _make_url(self):
        """Build URL to fetch AccurateRip disc data from."""
        dir_ = f'{self._ar_id1[-1]}/{self._ar_id1[-2]}/{self._ar_id1[-3]}/'
        file_ = f'dBAR-0{self._num_tracks:02d}-{self._ar_id1}-{self._ar_id2}-{self._freedb_id}.bin'
        return URL_BASE + dir_ + file_

    def _shift_data(self, num_bytes):
        """Left shift disc data by num_bytes (discard initial bytes)."""
        self._disc_data = self._disc_data[num_bytes:]

    def _validate_header(self, header):
        """Check if AccurateRip response header matches requested disc."""
        if header.num_tracks != self._num_tracks or \
            f'{header.ar_id1:08x}' != self._ar_id1 or \
            f'{header.ar_id2:08x}' != self._ar_id2 or \
            f'{header.freedb_id:08x}' != self._freedb_id:
            raise ValueError(f'Unexpected AccurateRip response header: {header}')

    def _parse_disc_data(self):
        """
        Parse AccurateRip binary disc data. The data consists of one or more
        Responses. Each Response consists of a Header and one or more Tracks:

        disc_data
        |
        |-- Response1
        |   |-- Header
        |   |-- Track1
        |   |-- Track2
        |   ...
        |   `-- TrackN
        ...
        |
        `-- ResponseN
            |-- Header
            |-- Track1
            |-- Track2
            ...
            `-- TrackN

        All Headers in disc data are expected to be the same, and must match
        the number of tracks and the three disc IDs stored in Fetcher instance.
        This means the number of tracks must also be the same in each Response.

        Disc data is stored in Fetcher instance as an array of bytes, and is
        parsed in the following way:

        1. Read Header.size bytes from disc data and create a Header object.
        2. Verify that created Header matches disc data in Fetcher instance (abort if it doesn't).
        3. Shift disc data left by Header.size bytes (discard parsed header bytes).
        4. Read the number of tracks from Header. For each track:
            - read Track.size bytes from disc data and create a Track object,
            - shift disc data left by Track.size bytes (discard parsed track bytes).
        5. Create a Response object from the Header and the list of Tracks.
        6. If the size of remaining disc data is greater than zero, repeat steps 1-5.
        7. Return DiscData object created from the list of Responses.

        Two exceptions can be raised: ValueError when Header data doesn't match
        the disc info in Fetcher instance, and a struct.error when the binary
        disc data cannot be unpacked. Both indicate that disc data acquired from
        AccurateRip is corrupted, and in such case all Responses are discarded
        (they cannot be trusted, even if some of them were successfully parsed).
        """
        responses = []

        while len(self._disc_data) > 0:
            header = Header.from_bytes(self._disc_data)
            self._validate_header(header)
            self._shift_data(Header.size)

            tracks = []
            for _ in range(header.num_tracks):
                tracks.append(Track.from_bytes(self._disc_data))
                self._shift_data(Track.size)

            responses.append(Response(header, tracks))

        return DiscData(responses)

    def fetch(self):
        """
        Fetch binary disc data from AccurateRip database. Return a DiscData
        object, or None on error.
        """
        try:
            response = requests.get(self._make_url(), headers={'User-Agent': USER_AGENT_STRING})
            response.raise_for_status()
            self._disc_data = response.content
            return self._parse_disc_data()
        except (requests.HTTPError, struct.error, ValueError) as error:
            print(error)
            return None
