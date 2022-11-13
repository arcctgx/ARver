"""Representation of a set of ripped CDDA files."""

import os
import wave

from dataclasses import dataclass

from arver.checksum.checksum import copy_crc, accuraterip_checksums
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


def _shorten_path(path, max_length=30):
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

        self.num_tracks = len(self.tracks)

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

    def calculate_checksums(self):
        """
        Iterate file list and calculate copy CRCs and AccurateRip checksums.
        This method must be called before verify() can be used.
        """
        total_tracks = len(self.tracks)
        for num, track in enumerate(self.tracks, start=1):
            track.set_copy_crc()
            track.set_accuraterip_checksums(num, total_tracks)

    def verify(self, disc):
        """Verify a set of ripped files against a CD with specified TOC."""
        accurip_checksums = disc.accuraterip_data.make_dict()

        print('AccurateRip verification results for tracks:')
        for num, track in enumerate(self.tracks, start=1):
            ar1, ar2 = track._ar1, track._ar2

            conf1, conf2 = 0, 0
            resp1, resp2 = 0, 0

            if ar1 in accurip_checksums[num]:
                conf1 = accurip_checksums[num][ar1]['confidence']
                resp1 = accurip_checksums[num][ar1]['response']

            if ar2 in accurip_checksums[num]:
                conf2 = accurip_checksums[num][ar2]['confidence']
                resp2 = accurip_checksums[num][ar2]['response']

            print(f'{num:2d}: conf1 = {conf1:3d} (resp: {resp1:2d})\t' +
                  f'conf2 = {conf2:3d} (resp: {resp2:2d})')
