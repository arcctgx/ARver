"""Disc info module for ARver."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import cdio
import discid
import musicbrainzngs
import pycdio

from arver import APPNAME, URL, VERSION
from arver.disc.database import AccurateRipDisc, AccurateRipFetcher
from arver.disc.fingerprint import accuraterip_ids, freedb_id, musicbrainz_id
from arver.disc.utils import LEAD_IN_FRAMES, frames_to_msf

PREGAP_TRACK_NUM = -1
ENHANCED_CD_DATA_TRACK_GAP = 11400


@dataclass
class _Track:
    """Representation of a CD track."""
    num: int
    lba: int
    frames: int
    type: str

    def msf(self) -> str:
        """Return track length as a string in MM:SS.FF format."""
        return frames_to_msf(self.frames)

    def __str__(self):
        numstr = f'{self.num:5d}'

        if self.num == PREGAP_TRACK_NUM:
            numstr = f'{"PGAP":>5s}'
        elif self.type != 'audio':
            numstr = f'{"DATA":>5s}'

        return f'{numstr}    {self.msf():>8s}    {self.frames:6d}\n'


class DiscType(Enum):
    """
    Disc types relevant to ARver:

    Audio CD (Red Book): a "normal" Compact Disc. Single session which only
    contains audio tracks.

    Mixed Mode CD (Yellow Book): single session, audio tracks and one data
    track exist together. Data track is first. Commonly used as game CDs in
    the 1990s and 2000s.

    Enhanced CD (Blue Book): multisession, first session only contains audio
    tracks, second session contains one data track. The data track usually
    contains music videos or other bonus materials. "Copy Control" CDs fall
    into this category as well.

    Disc ID: not a physical CD, disc data is obtained by disc ID lookup from
    MusicBrainz. Only Audio CDs can be correctly verified using this method.

    Unsupported CD: any edge case not covered by the types listed above.
    """
    UNSUPPORTED = 0
    AUDIO = 1
    MIXED_MODE = 2
    ENHANCED = 3
    DISC_ID = 4


def _have_disc() -> bool:
    """
    Detect if there is a readable disc in drive.

    Use discid instead of pycdio because it's much simpler. Furthermore,
    on error pycdio prints its own message which can't be silenced. discid
    is a dependency anyway, so it's not a problem.

    discid seems to raise error on CDs with no audio tracks. That's good:
    one edge case less to care about.
    """
    try:
        discid.read()
    except discid.DiscError:
        return False

    return True


def _is_multisession(device: cdio.Device) -> bool:
    """Check if disc has more than one session."""
    return device.get_last_session() > 0


def _is_audio_only(track_list: List[_Track]) -> bool:
    """Check if track list only contains audio tracks."""
    types = {track.type for track in track_list}
    return len(types) == 1 and 'audio' in types


def _get_disc_type(device: cdio.Device, track_list: List[_Track]) -> DiscType:
    """
    Determine disc type based on the following rules:

    No audio tracks -> unsupported disc (this should never happen)
    Single session and only audio tracks -> Audio CD
    Single session and the first track is a data track -> Mixed Mode CD
    Multisession and the last track is a data track -> Enhanced CD
    Anything else -> unsupported disc (no idea what that could be)
    """
    if 'audio' not in [track.type for track in track_list]:
        return DiscType.UNSUPPORTED

    multisession = _is_multisession(device)

    if not multisession and _is_audio_only(track_list):
        return DiscType.AUDIO

    if not multisession and track_list[0].type == 'data':
        return DiscType.MIXED_MODE

    if multisession and track_list[-1].type == 'data':
        return DiscType.ENHANCED

    return DiscType.UNSUPPORTED


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
    frames = track_list[0].lba - LEAD_IN_FRAMES

    if frames > 0:
        pregap = _Track(PREGAP_TRACK_NUM, LEAD_IN_FRAMES, frames, 'audio')

    return pregap


def _fix_last_audio_track(track_list: List[_Track]) -> None:
    """
    Fix length of the last audio track by subtracting the length of gap
    between last audio track and the data track in an enhanced CD. This
    is needed because pycdio includes this gap in sectors count of the
    last audio track.

    Obviously this only makes sense when there is a data track following
    audio tracks, that is in Enhanced CDs.
    """
    for track in reversed(track_list):
        if track.type != 'audio':
            continue

        track.frames -= ENHANCED_CD_DATA_TRACK_GAP
        break


@dataclass
class DiscInfo:
    """
    Representation of Compact Disc properties required for calculation
    of AccurateRip disc IDs and for performing checksum verification.
    """
    pregap: Optional[_Track]
    track_list: List[_Track]
    lead_out: int
    type: DiscType
    accuraterip_data: Optional[AccurateRipDisc] = field(default=None, init=False)

    def _format_tracklist(self):
        str_ = ''
        str_ += 'track     length     frames\n'
        str_ += '-----    --------    ------\n'

        if self.pregap is not None:
            str_ += str(self.pregap)

        for track in self.track_list:
            str_ += str(track)

        return str_.strip()

    def __str__(self):
        str_ = ''
        str_ += f'AccurateRip disc ID: {self.accuraterip_id()}\n'
        str_ += f'MusicBrainz disc ID: {self.musicbrainz_id()}\n'
        str_ += f'Disc type: {self.disc_type()}\n'
        str_ += '\n' + self._format_tracklist()
        return str_

    @classmethod
    def from_cd(cls) -> 'Optional[DiscInfo]':
        """
        Read disc properties from a physical CD in the default device.
        This is the only way to obtain all necessary information to verify
        each supported CD type (i.e. Audio, Mixed Mode and Enhanced).
        """
        if not _have_disc():
            return None

        device = cdio.Device(driver_id=pycdio.DRIVER_DEVICE)
        first_track_num = device.get_first_track().track
        num_tracks = device.get_num_tracks()
        lead_out = device.get_track(pycdio.CDROM_LEADOUT_TRACK).get_lba()

        track_list = []

        for num in range(first_track_num, num_tracks + 1):
            track = device.get_track(num)
            lba = track.get_lba()

            if num < 99:
                frames = track.get_last_lsn() - track.get_lsn() + 1
            else:
                # track.get_last_lsn() throws an exception for track 99. This looks
                # like a bug in libcdio. Track 99 must be the last track on the CD,
                # so we can use the lead out LBA that we already know to calculate
                # the last LSN of track 99.
                track_last_lsn = lead_out - LEAD_IN_FRAMES - 1
                frames = track_last_lsn - track.get_lsn() + 1

            fmt = track.get_format()
            track_list.append(_Track(num, lba, frames, fmt))

        pregap = _get_pregap_track(track_list)

        disc_type = _get_disc_type(device, track_list)
        if disc_type == DiscType.UNSUPPORTED:
            return None

        if disc_type == DiscType.ENHANCED:
            _fix_last_audio_track(track_list)

        return cls(pregap, track_list, lead_out, disc_type)

    @classmethod
    def from_disc_id(cls, disc_id: str) -> 'Optional[DiscInfo]':
        """
        Get disc properties from MusicBrainz by disc ID query. This does not
        provide information about data tracks or the true lead out offset, so
        only Audio CDs can be correctly verified by this method.

        If the disc corresponding to specified disc ID is actually a Mixed
        Mode or Enhanced CD, AccurateRip query may fail, verification may not
        be successful, or resulting confidence values may be lower than what
        would be obtained using a physical CD.
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
        return cls(pregap, track_list, lead_out, DiscType.DISC_ID)

    def audio_tracks(self) -> List[_Track]:
        """Return a list of audio tracks on the CD."""
        return [track for track in self.track_list if track.type == 'audio']

    def _audio_offsets(self) -> List[int]:
        """Return a list of offsets of audio tracks on the CD."""
        return [track.lba for track in self.audio_tracks()]

    def _all_offsets(self) -> List[int]:
        """Return a list of offsets of all tracks on the CD."""
        return [track.lba for track in self.track_list]

    def disc_type(self) -> str:
        """Return a string describing disc type."""
        types = {
            DiscType.UNSUPPORTED: 'Unsupported CD type',
            DiscType.AUDIO: 'Audio CD',
            DiscType.MIXED_MODE: 'Mixed Mode CD',
            DiscType.ENHANCED: 'Enhanced CD',
            DiscType.DISC_ID: 'None (disc ID lookup)'
        }
        return types[self.type]

    def musicbrainz_id(self) -> str:
        """Return MusicBrainz disc ID as string."""
        last_audio_track = self.audio_tracks()[-1]
        sectors = last_audio_track.lba + last_audio_track.frames

        # Calculation of MusicBrainz disc IDs requires track offsets from the
        # first CD session. Audio and Mixed Mode CDs are single-session, so
        # calculation requires all track offsets regardless of track type. In
        # Enhanced CDs the first session only contains audio tracks, so by
        # using just the audio track offsets the second session is omitted.
        if self.type == DiscType.ENHANCED:
            offsets = self._audio_offsets()
        else:
            offsets = self._all_offsets()

        return musicbrainz_id(offsets, sectors)

    def accuraterip_id(self) -> str:
        """Return AccurateRip disc ID as string."""
        num = len(self.audio_tracks())
        freedb = freedb_id(self._all_offsets(), self.lead_out)
        ar1, ar2 = accuraterip_ids(self._audio_offsets(), self.lead_out)
        return f'{num:03d}-{ar1:8s}-{ar2:8s}-{freedb:8s}'

    def fetch_accuraterip_data(self) -> None:
        """
        Download AccurateRip disc data and store AccurateRip responses in
        DiscInfo instance.
        """
        fetcher = AccurateRipFetcher.from_id(self.accuraterip_id())
        self.accuraterip_data = fetcher.fetch()


def get_disc_info(disc_id: Optional[str]) -> Optional[DiscInfo]:
    """
    Helper function for obtaining disc information.
    If disc_id is None read CD TOC from the CD in drive.
    Otherwise get TOC from specified MusicBrainz disc ID.
    """
    if disc_id is None:
        disc_info = DiscInfo.from_cd()
    else:
        disc_info = DiscInfo.from_disc_id(disc_id)

    if disc_info is None:
        if disc_id is None:
            print('Could not read disc. Is there a CD in the drive?')
        else:
            print(f'Could not look up disc ID "{disc_id}", is it correct?')

    return disc_info
