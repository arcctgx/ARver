"""Representation of a set of ripped CDDA files."""

from dataclasses import dataclass
from enum import Enum
from os.path import basename
from typing import ClassVar, List, Optional

from arver.checksum.checksum import accuraterip_checksums, copy_crc
from arver.checksum.properties import get_nframes
from arver.disc.info import DiscInfo, DiscType
from arver.disc.utils import frames_to_msf

AUDIO_FRAMES_PER_CD_SECTOR = 588


class AudioFormatError(Exception):
    """Raised when unsupported audio file (or non-audio file) is read."""


def _shorten_path(path: str, max_length: int = 30) -> str:
    """Shorten long path to an abbreviated file name of specified maximum length."""
    name = basename(path)
    if len(name) <= max_length:
        return name

    adj = 0 if max_length % 2 != 0 else -1
    midpoint = max_length // 2
    return name[:midpoint + adj] + '~' + name[-midpoint:]


class AudioFile:
    """Audio file to be verified against AccurateRip checksum."""

    def __init__(self, path: str) -> None:
        self.path: str = path

        try:
            self._audio_frames = get_nframes(path)
        except (OSError, TypeError) as exc:
            raise AudioFormatError from exc

        self._arv1: Optional[int] = None
        self._arv2: Optional[int] = None
        self._crc32: Optional[int] = None

    def __str__(self) -> str:
        short_name = _shorten_path(self.path)
        is_cdda = 'yes' if self._is_cd_rip() else 'no'
        cdda_frames = self._audio_frames // AUDIO_FRAMES_PER_CD_SECTOR
        length_msf = frames_to_msf(cdda_frames)

        arv1 = f'{self._arv1:08x}' if self._arv1 is not None else 'unknown'
        arv2 = f'{self._arv2:08x}' if self._arv2 is not None else 'unknown'
        crc32 = f'{self._crc32:08x}' if self._crc32 is not None else 'unknown'

        return f'{short_name:<30s}    {is_cdda:>4s}    ' + \
               f'{length_msf:>8s}    {cdda_frames:>6d}    ' + \
               f'{crc32:>8s}    {arv1:>8s}    {arv2:>8s}'

    def _is_cd_rip(self) -> bool:
        """
        If an audio file was ripped from a CD, its number of frames is
        evenly divisible by the number of audio frames per CD sector.
        """
        return self._audio_frames % AUDIO_FRAMES_PER_CD_SECTOR == 0

    def set_copy_crc(self) -> None:
        """Calculate and set copy CRC."""
        self._crc32 = copy_crc(self.path)

    def set_accuraterip_checksums(self, track_no: int, total_tracks: int) -> None:
        """Calculate and set both types of AccurateRip checksums."""
        self._arv1, self._arv2 = accuraterip_checksums(self.path, track_no, total_tracks)


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
    """This class represents a set of ripped audio files to be verified."""

    def __init__(self, paths: List[str]) -> None:
        self._paths: List[str] = paths
        self._discard_htoa()

        self.tracks: List[AudioFile] = []
        for path in self._paths:
            try:
                self.tracks.append(AudioFile(path))
            except AudioFormatError:
                # ignore non-audio or unsupported audio format
                continue

    def _discard_htoa(self) -> None:
        """Discard paths where file names match commonly used HTOA naming patterns."""
        htoa_patterns = ['track00.wav', 'track00.cdda.wav', 'track00.flac', 'track00.cdda.flac']
        self._paths = [path for path in self._paths if basename(path) not in htoa_patterns]

    def __str__(self) -> str:
        header = f'{"file name":^30s}    ' + \
            f'{"CDDA":^4s}    {"length":^8s}    {"frames":^6s}    ' + \
            f'{"CRC":^8s}    {"ARv1":^8s}    {"ARv2":^8s}'.rstrip()

        underline = f'{30*"-"}    {4*"-"}    {8*"-"}    {6*"-"}    ' + \
                    f'{8*"-"}    {8*"-"}    {8*"-"}'

        str_ = [header, underline]
        for track in self.tracks:
            str_.append(str(track))
        return '\n'.join(str_)

    def __len__(self) -> int:
        return len(self.tracks)

    def calculate_checksums(self) -> None:
        """
        Iterate file list and calculate copy CRCs and AccurateRip checksums.
        This method must be called before __str__() can be used, otherwise
        all printed checksums will be "unknown".
        """
        for num, track in enumerate(self.tracks, start=1):
            track.set_copy_crc()
            track.set_accuraterip_checksums(num, len(self))

    def verify(self, disc_info: DiscInfo) -> DiscVerificationResult:
        """
        Verify a set of ripped files against a CD with specified TOC.

        See doc/data_track.md for a description of handling mixed mode CDs,
        including the distinction between TOC index and rip index.
        """
        print(f'Verifying {len(self)} tracks:\n')

        if disc_info.accuraterip_data is None:
            raise ValueError('Cannot verify: missing AccurateRip data!')

        checksums = disc_info.accuraterip_data.make_dict()
        results: List[TrackVerificationResult] = []

        mixed_mode = disc_info.type == DiscType.MIXED_MODE
        toc_idx_start = 1 if not mixed_mode else 2

        for toc_idx, track in enumerate(self.tracks, start=toc_idx_start):
            rip_idx = toc_idx if not mixed_mode else toc_idx - 1
            ar1, ar2 = accuraterip_checksums(track.path, rip_idx, len(self))
            crc32 = copy_crc(track.path)

            print(f'Track {toc_idx}:')
            print(f'\tPath: {track.path}')
            print(f'\tCopy CRC: {crc32:08x}')

            if len(checksums[toc_idx]) == 0:
                results.append(
                    TrackVerificationResult(track.path, ar2, 'ARv2', -1, -1, _Status.NODATA))
                print('\tAccurateRip: no checksums available for this track')
                continue

            if ar2 in checksums[toc_idx]:
                conf = checksums[toc_idx][ar2]['confidence']
                resp = checksums[toc_idx][ar2]['response']
                print(f'\tAccurateRip: {ar2:08x} (ARv2), confidence {conf}, response {resp}')
                results.append(
                    TrackVerificationResult(track.path, ar2, 'ARv2', conf, resp, _Status.SUCCESS))
                continue

            if ar1 in checksums[toc_idx]:
                conf = checksums[toc_idx][ar1]['confidence']
                resp = checksums[toc_idx][ar1]['response']
                print(f'\tAccurateRip: {ar1:08x} (ARv1), confidence {conf}, response {resp}')
                results.append(
                    TrackVerificationResult(track.path, ar1, 'ARv1', conf, resp, _Status.SUCCESS))
                continue

            print(f'\tAccurateRip: {ar2:08x} (ARv2) - no match!')
            results.append(TrackVerificationResult(track.path, ar2, 'ARv2', -1, -1, _Status.FAILED))

        return DiscVerificationResult(results)
