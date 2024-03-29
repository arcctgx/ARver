"""Representation of a set of ripped CDDA files."""

from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatch
from os.path import basename
from typing import ClassVar, List, Optional

from arver.audio.checksums import get_checksums
from arver.audio.properties import get_nframes
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
            self.cdda_frames = self._audio_frames // AUDIO_FRAMES_PER_CD_SECTOR
        except (OSError, TypeError) as exc:
            raise AudioFormatError from exc

        self._arv1: Optional[int] = None
        self._arv2: Optional[int] = None
        self._crc32: Optional[int] = None

    def as_table_row(self) -> str:
        """
        Return string formatted as a row suitable for rip info table.

        If file checksums were not calculated prior to method call, they are
        printed as "unknown".
        """
        short_name = _shorten_path(self.path)
        is_cdda = 'yes' if self._is_cd_rip() else 'no'
        length_msf = frames_to_msf(self.cdda_frames)

        arv1 = f'{self._arv1:08x}' if self._arv1 is not None else 'unknown'
        arv2 = f'{self._arv2:08x}' if self._arv2 is not None else 'unknown'
        crc32 = f'{self._crc32:08x}' if self._crc32 is not None else 'unknown'

        return f'{short_name:<30s}    {is_cdda:>4s}    ' + \
               f'{length_msf:>8s}    {self.cdda_frames:>6d}    ' + \
               f'{crc32:>8s}    {arv1:>8s}    {arv2:>8s}'

    def _is_cd_rip(self) -> bool:
        """
        If an audio file was ripped from a CD, its number of frames is
        evenly divisible by the number of audio frames per CD sector.
        """
        return self._audio_frames % AUDIO_FRAMES_PER_CD_SECTOR == 0

    def set_checksums(self, track_no: int, total_tracks: int) -> None:
        """Calculate and set AccurateRip and CRC32 checksums."""
        self._arv1, self._arv2, self._crc32 = get_checksums(self.path, track_no, total_tracks)


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
        """Return string formatted as a row suitable for verification summary table."""
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
        table = [header, underline] + [track.as_table_row() for track in self.tracks]
        return '\n'.join(table)

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

        header = f'{"file name":^30s}    ' + \
            f'{"CDDA":^4s}    {"length":^8s}    {"frames":^6s}    ' + \
            f'{"CRC32":^8s}    {"ARv1":^8s}    {"ARv2":^8s}'.rstrip()

        underline = f'{30*"-"}    {4*"-"}    {8*"-"}    {6*"-"}    ' + \
                    f'{8*"-"}    {8*"-"}    {8*"-"}'

        table = [header, underline] + [track.as_table_row() for track in self.tracks]
        return '\n'.join(table)

    def __len__(self) -> int:
        return len(self.tracks)

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

    def _sanity_check(self, disc: DiscInfo, permissive: bool) -> None:
        """
        Make sure that the disc and rip are matching: the rip must have the
        same number of files as the number of audio tracks on CD, and their
        lenghts must be the same. ValueError is raised when difference is
        detected.

        Mismatch in the number of tracks is always fatal. Differences in track
        lengths can be ignored by enabling permissive mode.
        """
        num_files = len(self)
        num_tracks = len(disc.audio_tracks())

        if num_files != num_tracks:
            print(f'Track number mismatch: {num_files} to verify, but {num_tracks} on disc.')
            if num_files == num_tracks + 1 and disc.pregap is not None:
                print('Make sure the pregap track is not included.')
            raise ValueError

        num_mismatched = 0
        for audio_file, cd_track in zip(self.tracks, disc.audio_tracks()):
            delta = cd_track.frames - audio_file.cdda_frames
            if delta != 0:
                num_mismatched += 1
                diff = abs(delta)
                frames = 'frames' if diff > 1 else 'frame'
                relation = 'shorter' if delta < 0 else 'longer'
                filename = basename(audio_file.path)
                print(f'CD track {cd_track.num} is {diff} {frames} {relation} than "{filename}"')

        if num_mismatched != 0:
            print()

        if not permissive and num_mismatched != 0:
            print('Track length mismatch. Retry in permissive mode to verify anyway.')
            raise ValueError

    def verify(self, disc_info: DiscInfo, permissive: bool) -> DiscVerificationResult:
        """
        Verify a set of ripped files against a CD with specified TOC.

        See doc/data_track.md for a description of handling mixed mode CDs,
        including the distinction between TOC index and rip index.
        """
        self._sanity_check(disc_info, permissive)

        print(f'Verifying {len(self)} tracks:\n')

        if disc_info.accuraterip_data is None:
            raise ValueError('Cannot verify: missing AccurateRip data!')

        checksums = disc_info.accuraterip_data.make_dict()
        results: List[TrackVerificationResult] = []

        mixed_mode = disc_info.type == DiscType.MIXED_MODE
        toc_idx_start = 1 if not mixed_mode else 2

        for toc_idx, track in enumerate(self.tracks, start=toc_idx_start):
            rip_idx = toc_idx if not mixed_mode else toc_idx - 1
            ar1, ar2, crc32 = get_checksums(track.path, rip_idx, len(self))

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
