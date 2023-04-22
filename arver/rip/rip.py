"""Representation of a set of ripped CDDA files."""

import os
import wave

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, List

from arver.checksum.checksum import copy_crc, accuraterip_checksums
from arver.disc.info import DiscInfo
from arver.disc.utils import FRAMES_PER_SECOND, frames_to_msf

CHANNELS = 2
BYTES_PER_SAMPLE = 2
SAMPLES_PER_SECOND = 44100
SAMPLES_PER_FRAME = SAMPLES_PER_SECOND // FRAMES_PER_SECOND


class AudioFormatError(Exception):
    """Raised when unsupported audio file (or non-audio file) is read."""


@dataclass
class WavProperties:
    """Basic properties of a WAV file."""
    channels: int
    byte_width: int
    sample_rate: int
    samples: int

    @classmethod
    def from_file(cls, path):
        """Read audio properties from a WAV file. Returns None on error."""
        try:
            with wave.open(path) as wav:
                params = wav.getparams()
                frames = wav.getnframes()
                return cls(params.nchannels, params.sampwidth, params.framerate, frames)
        except (OSError, wave.Error) as exc:
            raise AudioFormatError from exc

    def is_cdda(self):
        """
        Determine if specified WAV file has been ripped from a CD.

        WAV files ripped from a CD are 16-bit LPCM stereo with 44.1 kHz frequency.
        Python wave module doesn't provide means to determine if the file is LPCM
        or anything else, so the method doesn't check that.

        If WAV file is ripped from a CD, its number of samples must be evenly
        divisible by the number of samples per CD frame.
        """
        return self.channels == CHANNELS and \
            self.byte_width == BYTES_PER_SAMPLE and \
            self.sample_rate == SAMPLES_PER_SECOND and \
            self.samples % SAMPLES_PER_FRAME == 0


def _shorten_path(path: str, max_length: int = 30) -> str:
    """Shorten long path to an abbreviated file name of specified maximum length."""
    name = os.path.basename(path)
    if len(name) <= max_length:
        return name

    adj = 0 if max_length % 2 != 0 else -1
    midpoint = max_length // 2
    return name[:midpoint + adj] + '~' + name[-midpoint:]


# pylint: disable=too-many-instance-attributes
class WavFile:
    """WAV file to be verified against AccurateRip checksum."""

    def __init__(self, path):
        self._path = path
        self._short_name = _shorten_path(path)

        self._properties = WavProperties.from_file(path)
        self._is_cdda = 'yes' if self._properties.is_cdda() else 'no'
        self._frames = self._properties.samples // SAMPLES_PER_FRAME
        self._length = frames_to_msf(self._frames)

        self._ar1 = 0x0
        self._ar2 = 0x0
        self._crc = 0x0

    def __str__(self):
        return f'{self._short_name:<30s}    {self._is_cdda:>4s}    ' + \
               f'{self._length:>8s}    {self._frames:>6d}    ' + \
               f'{self._crc:08x}    {self._ar1:08x}    {self._ar2:08x}'

    def set_copy_crc(self):
        """Calculate and set copy CRC."""
        self._crc = copy_crc(self._path)

    def set_accuraterip_checksums(self, track_no, total_tracks):
        """Calculate and set both types of AccurateRip checksums."""
        self._ar1, self._ar2 = accuraterip_checksums(self._path, track_no, total_tracks)


class _Status(Enum):
    """Possible track verification results."""
    SUCCESS = 0
    FAILED = 1
    NODATA = 2


@dataclass
class TrackVerificationResult:
    """Results of AccurateRip verification of a single track."""
    path: str
    checksum: int
    version: str
    confidence: int
    response: int
    status: _Status

    def _status_string(self) -> str:
        results = {_Status.SUCCESS: 'OK', _Status.FAILED: 'FAILED', _Status.NODATA: 'N/A'}
        return results[self.status]

    def as_table_row(self) -> str:
        """Return string formatted as row suitable for verification summary table."""
        short_name = _shorten_path(self.path)
        status = self._status_string()
        confidence = str(self.confidence) if self.confidence != -1 else '--'
        response = str(self.response) if self.response != -1 else '--'

        return f'{short_name:<30s}    {status:>6s}    {self.checksum:08x}    ' \
               f'{self.version:>4s}    {confidence:>4s}    {response:>4s}'


@dataclass
class DiscVerificationResult:
    """Results of AccurateRip verification of a complete disc."""
    all_ok: ClassVar[str] = 'All tracks verified successfully.'

    ok_nodata: ClassVar[str] = 'All tracks with available checksums verified successfully.'

    some_failed: ClassVar[str] = 'Verification of some tracks failed. Your ' \
    'disc may be damaged.'

    all_failed: ClassVar[str] = 'Verification of all tracks failed. Looks ' \
    'like your disc pressing does not exist in AccurateRip database.'

    tracks: List[TrackVerificationResult]

    def as_table(self) -> str:
        """Format verification results as a table."""

        header = f'{"file name":^30s}    {"result":>6s}    ' \
            f'{"checksum":8s}    {"type":4s}    ' \
            f'{"conf":4s}    {"resp":4s}'.rstrip()
        underline = f'{30*"-"}    {6*"-"}    {8*"-"}    {4*"-"}    {4*"-"}    {4*"-"}'
        text = [header, underline] + [track.as_table_row() for track in self.tracks]
        return '\n'.join(text)

    def summary(self) -> str:
        """Return a string with the description of verification result."""
        num_failed = len([track for track in self.tracks if track.status == _Status.FAILED])
        num_nodata = len([track for track in self.tracks if track.status == _Status.NODATA])

        no_checksum = ''
        if num_nodata != 0:
            plural = 'tracks' if num_nodata > 1 else 'track'
            no_checksum += f'{num_nodata} {plural} not present in AccurateRip database.\n'

        if num_failed == 0 and num_nodata == 0:
            return no_checksum + self.all_ok

        if num_failed == 0 and num_nodata != 0:
            return no_checksum + self.ok_nodata

        if num_failed == len(self.tracks) - num_nodata:
            return no_checksum + self.all_failed

        return no_checksum + self.some_failed


class Rip:
    """This class represents a set of ripped WAV files to be verified."""

    def __init__(self, paths):
        self._paths = paths
        self._discard_htoa()

        self.tracks = []
        for path in self._paths:
            try:
                self.tracks.append(WavFile(path))
            except AudioFormatError:
                # ignore non-audio or unsupported audio format
                continue

    def _discard_htoa(self):
        """Discard paths where file names match commonly used HTOA naming patterns."""
        htoa_patterns = ['track00.wav', 'track00.cdda.wav']
        self._paths = [path for path in self._paths if os.path.basename(path) not in htoa_patterns]

    def __str__(self):
        header = f'{"file name":^30s}    ' + \
            f'{"CDDA":^4s}    {"length":^8s}    {"frames":^6s}    ' + \
            f'{"CRC":^8s}    {"ARv1":^8s}    {"ARv2":^8s}'.rstrip()

        underline = f'{30*"-"}    {4*"-"}    {8*"-"}    {6*"-"}    ' + \
                    f'{8*"-"}    {8*"-"}    {8*"-"}'

        str_ = [header, underline]
        for track in self.tracks:
            str_.append(str(track))
        return '\n'.join(str_)

    def __len__(self):
        return len(self.tracks)

    def calculate_checksums(self):
        """
        Iterate file list and calculate copy CRCs and AccurateRip checksums.
        This method must be called before verify() can be used.
        """
        total_tracks = len(self.tracks)
        for num, track in enumerate(self.tracks, start=1):
            track.set_copy_crc()
            track.set_accuraterip_checksums(num, total_tracks)

    def verify(self, disc_info: DiscInfo) -> DiscVerificationResult:
        """Verify a set of ripped files against a CD with specified TOC."""
        print(f'Verifying {len(self)} tracks:\n')

        if disc_info.accuraterip_data is None:
            raise ValueError('Cannot verify: missing AccurateRip data!')

        checksums = disc_info.accuraterip_data.make_dict()
        results = []

        for num, track in enumerate(self.tracks, start=1):
            print(f'Track {num}:')
            print(f'\tPath: {track._path}')
            print(f'\tCopy CRC: {track._crc:08x}')

            ar1, ar2 = track._ar1, track._ar2

            if len(checksums[num]) == 0:
                results.append(
                    TrackVerificationResult(track._path, ar2, 'ARv2', -1, -1, _Status.NODATA))
                print('\tAccurateRip: no checksums available for this track')
                continue

            if ar2 in checksums[num]:
                conf = checksums[num][ar2]['confidence']
                resp = checksums[num][ar2]['response']
                print(f'\tAccurateRip: {ar2:08x} (ARv2), confidence {conf}, response {resp}')
                results.append(
                    TrackVerificationResult(track._path, ar2, 'ARv2', conf, resp, _Status.SUCCESS))
                continue

            if ar1 in checksums[num]:
                conf = checksums[num][ar1]['confidence']
                resp = checksums[num][ar1]['response']
                print(f'\tAccurateRip: {ar1:08x} (ARv1), confidence {conf}, response {resp}')
                results.append(
                    TrackVerificationResult(track._path, ar1, 'ARv1', conf, resp, _Status.SUCCESS))
                continue

            print(f'\tAccurateRip: {ar2:08x} (ARv2) - no match!')
            results.append(TrackVerificationResult(track._path, ar2, 'ARv2', -1, -1,
                                                   _Status.FAILED))

        return DiscVerificationResult(results)
