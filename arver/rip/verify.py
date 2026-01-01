"""Rip verification module."""

from dataclasses import dataclass, field
from enum import Enum
from os.path import basename
from typing import TYPE_CHECKING, ClassVar, List

from arver.audio.checksums import get_checksums
from arver.rip import NAME_WIDTH, _shorten_path

if TYPE_CHECKING:
    from arver.disc.info import DiscInfo
    from arver.rip.rip import Rip


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
        results = {
            _Status.SUCCESS: 'OK',
            _Status.FAILED: 'FAILED',
            _Status.NODATA: 'N/A',
        }
        return results[self.status]

    def as_table_row(self) -> str:
        """Return string formatted as a row suitable for verification summary table."""
        short_name = _shorten_path(self.path)
        status = self._status_string()
        confidence = str(self.confidence) if self.confidence != -1 else '--'
        response = str(self.response) if self.response != -1 else '--'

        return f'{short_name:<{NAME_WIDTH}s}    {status:>6s}    {self.checksum:08x}    ' \
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
        header = f'{"file name":^{NAME_WIDTH}s}    {"result":>6s}    ' \
            f'{"checksum":8s}    {"type":4s}    ' \
            f'{"conf":4s}    {"resp":4s}'.rstrip()
        underline = f'{NAME_WIDTH*"-"}    {6*"-"}    {8*"-"}    {4*"-"}    {4*"-"}    {4*"-"}'
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


@dataclass
class Verifier:
    """
    Compares checksums of local files with the checksums downloaded from
    AccurateRip database, and provides a verification summary.

    The whole point of ARver.
    """

    rip: 'Rip'
    disc: 'DiscInfo'
    _permissive: bool = field(default=False, init=False)
    _use_arv1: bool = field(default=False, init=False)

    def _sanity_check(self) -> None:
        """
        Make sure that the disc and rip are matching: the rip must have the
        same number of files as the number of audio tracks on CD, and their
        lenghts must be the same. ValueError is raised when difference is
        detected.

        Mismatch in the number of tracks is always fatal. Differences in track
        lengths can be ignored by enabling permissive mode.
        """
        num_files = len(self.rip)
        num_tracks = len(self.disc.audio_tracks())

        if num_files != num_tracks:
            print(f'Track number mismatch: {num_files} to verify, but {num_tracks} on disc.')
            if num_files == num_tracks + 1 and self.disc.pregap is not None:
                print('Make sure the pregap track is not included.')
            raise ValueError

        num_mismatched = 0
        for audio_file, cd_track in zip(self.rip.tracks, self.disc.audio_tracks()):
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

        if not self._permissive and num_mismatched != 0:
            print('Track length mismatch. Retry in permissive mode to verify anyway.')
            raise ValueError

    def enable_permissive_mode(self) -> None:
        """Switch verification to permissive mode."""
        self._permissive = True

    def enable_arv1_only_mode(self) -> None:
        """Switch verification to ARv1-only mode."""
        self._use_arv1 = True

    def verify(self) -> DiscVerificationResult:
        """
        Verify a set of ripped files against a CD with specified TOC.

        See doc/data_track.md for a description of handling mixed mode CDs,
        including the distinction between TOC index and rip index.
        """
        self._sanity_check()

        print(f'Verifying {len(self.rip)} tracks:\n')

        if self.disc.accuraterip_data is None:
            raise ValueError('Cannot verify: missing AccurateRip data!')

        checksums = self.disc.accuraterip_data.make_dict()
        results: List[TrackVerificationResult] = []

        toc_idx_start = 1 if not self.disc.is_mixed_mode() else 2

        for toc_idx, track in enumerate(self.rip.tracks, start=toc_idx_start):
            rip_idx = toc_idx if not self.disc.is_mixed_mode() else toc_idx - 1
            csum = get_checksums(track.path, rip_idx, len(self.rip))

            print(f'Track {toc_idx}:')
            print(f'\tPath: {track.path}')
            print(f'\tCRC32: {csum.crc:08x} (skip silence: {csum.crcss:08x})')

            if len(checksums[toc_idx]) == 0:
                results.append(
                    TrackVerificationResult(track.path, csum.arv2, 'ARv2', -1, -1, _Status.NODATA))
                print('\tAccurateRip: no checksums available for this track')
                continue

            if csum.arv2 in checksums[toc_idx] and not self._use_arv1:
                conf = checksums[toc_idx][csum.arv2]['confidence']
                resp = checksums[toc_idx][csum.arv2]['response']
                print(f'\tAccurateRip: {csum.arv2:08x} (ARv2), confidence {conf}, response {resp}')
                results.append(
                    TrackVerificationResult(track.path, csum.arv2, 'ARv2', conf, resp,
                                            _Status.SUCCESS))
                continue

            if csum.arv1 in checksums[toc_idx]:
                conf = checksums[toc_idx][csum.arv1]['confidence']
                resp = checksums[toc_idx][csum.arv1]['response']
                print(f'\tAccurateRip: {csum.arv1:08x} (ARv1), confidence {conf}, response {resp}')
                results.append(
                    TrackVerificationResult(track.path, csum.arv1, 'ARv1', conf, resp,
                                            _Status.SUCCESS))
                continue

            if self._use_arv1:
                print(f'\tAccurateRip: {csum.arv1:08x} (ARv1) - no match!')
                results.append(
                    TrackVerificationResult(track.path, csum.arv1, 'ARv1', -1, -1, _Status.FAILED))
            else:
                print(f'\tAccurateRip: {csum.arv2:08x} (ARv2) - no match!')
                results.append(
                    TrackVerificationResult(track.path, csum.arv2, 'ARv2', -1, -1, _Status.FAILED))

        return DiscVerificationResult(results)
