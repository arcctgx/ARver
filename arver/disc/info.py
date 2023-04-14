"""Disc info module for ARver."""

import sys

from dataclasses import dataclass
from typing import List, Optional

import cdio
import discid
import musicbrainzngs
import pycdio

from arver import APPNAME, VERSION, URL
from arver.disc.id import freedb_id, musicbrainz_id, accuraterip_ids
from arver.disc.utils import frames_to_msf, LEAD_IN_FRAMES

PREGAP_TRACK_NUM = -1


@dataclass
class _Track:
    num: int
    offset: int
    frames: int
    type: str

    def msf(self) -> str:
        """Return track length in MM:SS.FF format."""
        return frames_to_msf(self.frames)

    def __str__(self):
        numstr = f'{self.num:5d}'

        if self.num == PREGAP_TRACK_NUM:
            numstr = f'{"PGAP":>5s}'
        elif self.type != 'audio':
            numstr = f'{"DATA":>5s}'

        return f'{numstr}  {self.offset:6d}  {self.msf():>8s}  {self.frames:6d}  {self.type:>6s}'


def _have_disc() -> bool:
    """
    Detect if there is a readable disc in drive.

    Use discid instead of pycdio because it's much simpler. Furthermore,
    on error pycdio prints its own message which can't be silenced. discid
    is a dependency anyway, so it's not a problem.
    """
    try:
        discid.read()
    except discid.DiscError:
        return False

    return True


def _is_mixed_mode(device: cdio.Device) -> bool:
    """
    Determine if the disc is a mixed-mode (Yellow Book) CD.
    Assume mixed mode CD is single-session with a leading data track.
    """
    first_track = device.get_first_track()
    first_session_lsn = first_track.get_lsn()
    last_session_lsn = device.get_last_session()
    multisession = first_session_lsn != last_session_lsn

    if not multisession and first_track.get_format() == 'data':
        return True
    return False


def _calculate_track_lengths(offset_list: List[int], sectors: int) -> List[int]:
    """
    Return a list of track lengths expressed in CD frames.
    Implementation assumes arguments are obtained by MusicBrainz DiscID query.
    Names of arguments follow respective dictionary keys in MB response.
    """
    shifted = offset_list[1:] + [sectors]
    return [shf - off for shf, off in zip(shifted, offset_list)]


def _get_pregap_track(track_list: List[_Track]) -> Optional[_Track]:
    """
    If the first track doesn't begin immediately after lead in, return a
    pregap track object. Otherwise return None.

    Note that existence of a pregap track doesn't mean it contains any audio.
    Short pregap tracks containing about half a second of silence are quite
    common, but audio data hidden in track one pregap (HTOA) is very rare.
    """
    pregap = None
    frames = track_list[0].offset - LEAD_IN_FRAMES

    if frames > 0:
        pregap = _Track(PREGAP_TRACK_NUM, LEAD_IN_FRAMES, frames, 'audio')

    return pregap


@dataclass
class DiscInfo:
    """
    Representation of Compact Disc properties required for calculation of
    AccurateRip disc IDs.

    Information about mixed mode is required because the layout of checksums in
    AccurateRip response is different for these CDs: checksum of the first audio
    track comes second, and the checksum of the last audio track is missing.
    """
    pregap: Optional[_Track]
    track_list: List[_Track]
    lead_out: int
    mixed_mode: bool

    def print_table(self) -> None:
        """Print disc information as a track listing."""
        print(f'{"track":^5s}  {"offset":^6s}  {"length":^8s}  {"frames":6s}  {"type":^6s}')
        print(f'{"-"*5}  {"-"*6}  {"-"*8}  {"-"*6}  {"-"*6}')

        if self.pregap:
            print(self.pregap)

        for track in self.track_list:
            print(track)

        print(f'{"OUT":>5s}  {self.lead_out:6d}')

    @classmethod
    def from_cd(cls) -> 'Optional[DiscInfo]':
        """Read disc properties from a physical CD in the default device."""
        if not _have_disc():
            return None

        device = cdio.Device(driver_id=pycdio.DRIVER_DEVICE)
        first_track_num = device.get_first_track().track
        num_tracks = device.get_num_tracks()
        lead_out_lba = device.get_track(pycdio.CDROM_LEADOUT_TRACK).get_lba()
        mixed_mode = _is_mixed_mode(device)

        track_list = []

        for num in range(first_track_num, num_tracks + 1):
            track = device.get_track(num)
            lba = track.get_lba()  # relative to sector zero: LBA = LSN + 150
            frames = track.get_last_lsn() - track.get_lsn() + 1
            fmt = track.get_format()
            track_list.append(_Track(num, lba, frames, fmt))

        pregap = _get_pregap_track(track_list)
        return cls(pregap, track_list, lead_out_lba, mixed_mode)

    @classmethod
    def from_discid(cls, disc_id: str) -> 'Optional[DiscInfo]':
        """
        Get disc properties from MusicBrainz by disc ID. This is useful only
        when the CD is pure Red Book audio CD. MusicBrainz disc ID does not
        encode information about data tracks, but this information is required
        to calculate AccurateRip disc ID.
        """
        musicbrainzngs.set_useragent(APPNAME, VERSION, URL)

        try:
            response = musicbrainzngs.get_releases_by_discid(disc_id)
        except musicbrainzngs.ResponseError:
            return None

        lead_out = int(response['disc']['sectors'])
        offsets = response['disc']['offset-list']
        lengths = _calculate_track_lengths(offsets, lead_out)

        track_list = []
        for num, track_data in enumerate(zip(offsets, lengths), start=1):
            track_list.append(_Track(num, *track_data, 'audio'))

        pregap = _get_pregap_track(track_list)
        return cls(pregap, track_list, lead_out, False)

    def _audio_tracks(self) -> List[_Track]:
        """Return a list of audio tracks on the CD."""
        return [track for track in self.track_list if track.type == 'audio']

    def _audio_offsets(self) -> List[int]:
        """Return a list of offsets of audio tracks on the CD."""
        return [track.offset for track in self._audio_tracks()]

    def _all_offsets(self) -> List[int]:
        """Return a list of offsets of all tracks on the CD."""
        return [track.offset for track in self.track_list]

    def musicbrainz_id(self) -> str:
        """Return MusicBrianz disc ID as string."""
        last_audio_track = self._audio_tracks()[-1]
        sectors = last_audio_track.offset + last_audio_track.frames
        return musicbrainz_id(self._audio_offsets(), sectors)

    def accuraterip_id(self) -> str:
        """Return AccurateRip disc ID as string."""
        num = len(self._audio_tracks())
        freedb = freedb_id(self._all_offsets(), self.lead_out)
        ar1, ar2 = accuraterip_ids(self._audio_offsets(), self.lead_out)
        return f'{num:03d}-{ar1:8s}-{ar2:8s}-{freedb:8s}'


if __name__ == '__main__':
    disc_info = DiscInfo.from_cd()
    # disc_info = DiscInfo.from_discid('.wsrLgOecMphb09w1pr.ZwcIrj8-')

    if disc_info is None:
        print('Failed to read disc. Is there a CD in drive?')
        sys.exit(1)

    print('AccurateRip disc ID:', disc_info.accuraterip_id())
    print('MusicBrainz disc ID:', disc_info.musicbrainz_id())
    print()
    disc_info.print_table()
