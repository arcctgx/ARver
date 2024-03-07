"""Utilities for communicating with AccurateRip database."""

import struct
from dataclasses import dataclass
from typing import ClassVar, List, Optional

import requests

from arver import APPNAME, URL, VERSION

FETCH_TIMEOUT_SECONDS = 5
URL_BASE = 'http://www.accuraterip.com/accuraterip/'
USER_AGENT_STRING = f'{APPNAME}/{VERSION} {URL}'


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
    confidence value. The first checksum is either v1 or v2 track checksum (database
    does not indicate which one). The other one is the checksum of frame 450 used for
    offset detection.
    """
    size: ClassVar[int] = 9
    confidence: int
    checksum: int
    checksum_450: int

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
        return f'{self.checksum:08x}   (confidence: {self.confidence})'


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
        str_.append(f'disc ID: {self.header}')
        for num, track in enumerate(self.tracks, start=1):
            str_.append(f'track {num:2d}:   {track}')
        return '\n'.join(str_)


@dataclass
class AccurateRipDisc:
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

    def __len__(self):
        return len(self.responses)

    def _max_confidence(self) -> int:
        return max(track.confidence for response in self.responses for track in response.tracks)

    def summary(self) -> str:
        """Summarize the number of responses and maximum confidence."""
        num = len(self)
        word = 'response' if num == 1 else 'responses'
        return f'Got {num} AccurateRip {word} (max confidence: {self._max_confidence()})'

    def make_dict(self):
        """
        Convert AccurateRipDisc object to a dictionary for easy lookup of checksums
        during file verification. The conversion is "lossy": AccurateRip checksums
        with zero confidence are omitted.

        For a disc with N tracks, resulting dictionary has the following structure:

        {
            "1": {
                "checksum_1": {
                    "confidence": X,
                    "response": Y
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
            "N": {
                ...
            },
            "N+1": {}
        }

        Conversion assumes that checksums other than zero are unique in scope of
        one track. If this is not the case, lower confidence value from later
        response may overwrite higher confidence value from earlier response.

        The "N+1" track with no checksums is needed to prevent out-of-bounds
        dictionary lookup when verifying mixed mode CDs. It is never reached
        when handling other disc types. See doc/data_track.md for a detailed
        description.
        """
        data = {}

        num_responses = len(self.responses)
        num_tracks = self.responses[0].header.num_tracks

        for trk in range(num_tracks):
            index = trk + 1
            data[index] = {}

            for rsp in range(num_responses):
                track = self.responses[rsp].tracks[trk]

                if track.confidence != 0:
                    data[index][track.checksum] = {
                        'confidence': track.confidence,
                        'response': rsp + 1,
                    }

        # An extra track for handling mixed mode CDs.
        data[index + 1] = {}

        return data


# pylint: disable=too-few-public-methods
class AccurateRipFetcher:
    """
    Class for fetching AccurateRip data of a Compact Disc, parsing the
    binary data and representing AccurateRip responses in a usable form.
    """

    def __init__(self, num_tracks: int, ar_id1: str, ar_id2: str, freedb_id: str):
        self._num_tracks = num_tracks
        self._ar_id1 = ar_id1
        self._ar_id2 = ar_id2
        self._freedb_id = freedb_id
        self._raw_bytes = bytes()

    @classmethod
    def from_id(cls, accuraterip_id: str) -> 'AccurateRipFetcher':
        """Create Fetcher object from AccurateRip ID string."""
        parts = accuraterip_id.split('-')
        return cls(int(parts[0]), parts[1], parts[2], parts[3])

    def _make_url(self):
        """Build URL to fetch AccurateRip disc data from."""
        dir_ = f'{self._ar_id1[-1]}/{self._ar_id1[-2]}/{self._ar_id1[-3]}/'
        file_ = f'dBAR-0{self._num_tracks:02d}-{self._ar_id1}-{self._ar_id2}-{self._freedb_id}.bin'
        return URL_BASE + dir_ + file_

    def _shift_bytes(self, num_bytes):
        """Left shift raw disc data by num_bytes (discard initial bytes)."""
        self._raw_bytes = self._raw_bytes[num_bytes:]

    def _validate_header(self, header):
        """Check if AccurateRip response header matches requested disc."""
        if header.num_tracks != self._num_tracks or \
            f'{header.ar_id1:08x}' != self._ar_id1 or \
            f'{header.ar_id2:08x}' != self._ar_id2 or \
            f'{header.freedb_id:08x}' != self._freedb_id:
            raise ValueError(f'Unexpected AccurateRip response header: {header}')

    def _parse_raw_bytes(self):
        """
        Parse AccurateRip binary disc data. The data consists of one or more
        Responses. Each Response consists of a Header and one or more Tracks:

        AccurateRipDisc
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
        the number of tracks and the three disc IDs stored in AccurateRipFetcher
        instance. This means the number of tracks must also be the same in each
        Response.

        Raw disc data is stored in AccurateRipFetcher instance as an array of
        bytes, and is parsed in the following way:

        1. Read Header.size bytes from disc data and create a Header object.
        2. Verify that created Header matches disc data in AccurateRipFetcher instance
           (raise ValueError if it doesn't).
        3. Shift disc data left by Header.size bytes (discard parsed header bytes).
        4. Read the number of tracks from Header. For each track:
            - read Track.size bytes from disc data and create a Track object,
            - shift disc data left by Track.size bytes (discard parsed track bytes).
        5. Create a Response object from the Header and the list of Tracks.
        6. If the size of remaining disc data is greater than zero, repeat steps 1-5.
        7. Return AccurateRipDisc object created from the list of Responses.

        Two exceptions can be raised: ValueError when Header data doesn't match
        the disc info in AccurateRipFetcher instance, and a struct.error when the
        binary disc data cannot be unpacked. Both indicate that disc data acquired
        from AccurateRip is corrupted, and in such case all Responses are discarded
        (they cannot be trusted, even if some of them were successfully parsed).
        """
        responses = []

        while len(self._raw_bytes) > 0:
            header = Header.from_bytes(self._raw_bytes)
            self._validate_header(header)
            self._shift_bytes(Header.size)

            tracks = []
            for _ in range(header.num_tracks):
                tracks.append(Track.from_bytes(self._raw_bytes))
                self._shift_bytes(Track.size)

            responses.append(Response(header, tracks))

        return AccurateRipDisc(responses)

    def fetch(self) -> Optional[AccurateRipDisc]:
        """
        Fetch binary disc data from AccurateRip database. Return an AccurateRipDisc
        object, or None on error.
        """
        try:
            response = requests.get(self._make_url(),
                                    headers={'User-Agent': USER_AGENT_STRING},
                                    timeout=FETCH_TIMEOUT_SECONDS)
            response.raise_for_status()
            self._raw_bytes = response.content
            return self._parse_raw_bytes()
        except requests.ConnectTimeout:
            print('Failed to connect to AccurateRip database. Try again later.')
        except requests.HTTPError as error:
            if error.response.status_code == 404:
                print('Could not find disc in AccurateRip database.')
            else:
                print(f'Failed to download AccurateRip data: {error}')
        except (struct.error, ValueError) as error:
            print(f'Could not decode AccurateRip response: {error}')

        return None


class AccurateRipParser(AccurateRipFetcher):
    """Class for parsing AccurateRip data stored in a cached dBAR file."""

    def __init__(self, path: str):
        # Call parent init with dummy values because we don't know the number of
        # tracks or disc fingerprints. Header validator method is a no-op anyway.
        super().__init__(0, '00000000', '00000000', '00000000')
        self._path = path

    def _validate_header(self, header):
        """
        We only have dummy values for the number of tracks and disc fingerprints,
        so override this method so that it doesn't actually verify these values.
        """

    def parse(self) -> Optional[AccurateRipDisc]:
        """
        Read cached AccurateRip disc data from a file. Return an AccurateRipDisc
        object, or None on error.
        """
        try:
            with open(self._path, mode='rb') as dbar:
                self._raw_bytes = dbar.read()
            return self._parse_raw_bytes()
        except (OSError, struct.error, ValueError) as error:
            print(error)
            return None
