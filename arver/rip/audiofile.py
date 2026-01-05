"""Representation of a set of ripped CDDA files."""

from fnmatch import fnmatch
from os.path import basename
from typing import List, Optional

from arver.audio.checksums import Checksums, get_checksums
from arver.audio.properties import get_frame_count
from arver.rip import NAME_WIDTH, _shorten_path
from arver.utils import frames_to_msf

AUDIO_FRAMES_PER_CD_SECTOR = 588


class AudioFormatError(Exception):
    """Raised when unsupported audio file (or non-audio file) is read."""


def _ceil_div(dividend: int, divisor: int) -> int:
    """
    Ceiling division: round the quotient up to the next integer, e.g.:
    2940 divided by 588 is 5,
    1000 divided by 588 is 2.
    """
    return (dividend + divisor - 1) // divisor


class AudioFile:
    """Audio file to be verified against AccurateRip checksum."""

    def __init__(self, path: str) -> None:
        self.path: str = path

        try:
            self._audio_frames = get_frame_count(path)
            self.cdda_frames = _ceil_div(self._audio_frames, AUDIO_FRAMES_PER_CD_SECTOR)
        except (OSError, TypeError) as exc:
            raise AudioFormatError from exc

        self._csum: Optional[Checksums] = None

    def as_table_row(self) -> str:
        """
        Return string formatted as a row suitable for rip info table.

        If file checksums were not calculated prior to method call, they are
        printed as "unknown".
        """
        short_name = _shorten_path(self.path)
        is_cdda = 'yes' if self._is_cd_rip() else 'no'
        length_msf = frames_to_msf(self.cdda_frames)

        arv1 = f'{self._csum.arv1:08x}' if self._csum is not None else 'unknown'
        arv2 = f'{self._csum.arv2:08x}' if self._csum is not None else 'unknown'
        crc32 = f'{self._csum.crc:08x}' if self._csum is not None else 'unknown'
        crc32ss = f'{self._csum.crcss:08x}' if self._csum is not None else 'unknown'

        return f'{short_name:<{NAME_WIDTH}s}    {is_cdda:>4s}    ' + \
               f'{length_msf:>8s}    {self.cdda_frames:>6d}    ' + \
               f'{crc32:>8s}    {crc32ss:>8s}    {arv1:>8s}    {arv2:>8s}'

    def _is_cd_rip(self) -> bool:
        """
        If an audio file was ripped from a CD, its number of frames is
        evenly divisible by the number of audio frames per CD sector.
        """
        return self._audio_frames % AUDIO_FRAMES_PER_CD_SECTOR == 0

    def set_checksums(self, track_no: int, total_tracks: int) -> None:
        """Calculate and set AccurateRip and CRC32 checksums."""
        self._csum = get_checksums(self.path, track_no, total_tracks)


class Rip:
    """This class represents a set of ripped audio files to be verified."""

    def __init__(self, paths: List[str], exclude: Optional[List[str]] = None) -> None:
        self._paths: List[str] = paths
        self._have_checksums = False
        self._discard_htoa(exclude)

        self.tracks: List[AudioFile] = []
        for path in self._paths:
            try:
                self.tracks.append(AudioFile(path))
            except AudioFormatError:
                # ignore non-audio or unsupported audio format
                continue

    def _discard_htoa(self, exclude: Optional[List[str]] = None) -> None:
        """
        Discard paths matching HTOA patterns.

        If exclude argument is None, a list of common naming patterns is used.
        The default list is ignored when any exclude patterns are specified.
        """
        htoa_patterns = ['track00.wav', 'track00.cdda.wav', 'track00.flac', 'track00.cdda.flac']

        if exclude is not None:
            htoa_patterns = []
            for pattern in exclude:
                htoa_patterns += [basename(path) for path in self._paths if fnmatch(path, pattern)]

        self._paths = [path for path in self._paths if basename(path) not in htoa_patterns]

    def as_table(self) -> str:
        """
        Format rip information as a table.

        The first call of this method calculates all checksums, so there will
        be a delay before it returns. Subsequent calls will return instantly.
        """
        self._calculate_checksums()

        header = f'{"file name":^{NAME_WIDTH}s}    ' + \
            f'{"CDDA":^4s}    {"length":^8s}    {"frames":^6s}    ' + \
            f'{"CRC32":^8s}    {"CRCSS":^8s}    {"ARv1":^8s}    {"ARv2":^8s}'.rstrip()

        underline = f'{NAME_WIDTH*"-"}    {4*"-"}    {8*"-"}    {6*"-"}    ' + \
                    f'{8*"-"}    {8*"-"}    {8*"-"}    {8*"-"}'

        table = [header, underline] + [track.as_table_row() for track in self.tracks]
        return '\n'.join(table)

    def __len__(self) -> int:
        return len(self.tracks)

    def track_frames(self) -> List[int]:
        """Return the lengths of all tracks in CDDA frames as a list of integers."""
        return [track.cdda_frames for track in self.tracks]

    def _calculate_checksums(self) -> None:
        """
        Iterate file list and calculate copy CRCs and AccurateRip checksums.
        It only makes no sense to calculate checksums once for a given rip, so
        only the first call of this method will perform calculation. Any further
        calls will be no-ops.

        This method must be called at least once before rip information is printed,
        otherwise all checksums are "unknown".
        """
        if self._have_checksums is True:
            return

        for num, track in enumerate(self.tracks, start=1):
            track.set_checksums(num, len(self))

        self._have_checksums = True
