"""Disc info module for ARver."""

from dataclasses import dataclass
from typing import List

import cdio
import pycdio


@dataclass
class _Track:
    num: int
    lba: int
    length: int
    fmt: str

    def __str__(self):
        return f'{self.num:2d}\t{self.lba:6d}\t{self.length:6d}\t{self.fmt:>6s}'


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


@dataclass
class DiscInfo:
    """
    Representation of Compact Disc properties required for calculation of
    AccurateRip disc IDs.

    Information about mixed mode is required because the layout of checksums in
    AccurateRip response is different for these CDs: checksum of the first audio
    track comes second, and the checksum of the last audio track is missing.
    """
    track_list: List[_Track]
    lead_out: int
    mixed_mode: bool

    def print_table(self) -> None:
        """Print disc information as a track listing."""
        print(f' #\t{"LBA":>6s}\t{"frames":6s}\tformat')
        print(f'--\t{"-"*6}\t{"-"*6}\t{"-"*6}')

        for track in self.track_list:
            print(track)

        print(f'AA\t{self.lead_out:6d}')

    @classmethod
    def from_cd(cls):
        """Read disc properties from a physical CD in the default device."""
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

        return cls(track_list, lead_out_lba, mixed_mode)

    @classmethod
    def from_discid(cls, discid):
        """
        Get disc properties from MusicBrainz by disc ID. This is useful only
        when the CD is pure Red Book audio CD. MusicBrainz disc ID does not
        encode information about data tracks, but this information is required
        to calculate AccurateRip disc ID.
        """
        raise NotImplementedError

    def all_offsets(self) -> List[int]:
        """
        Return a list of LBA offsets of all track on the CD regardless of their
        type. They are used for calculating FreeDB disc ID.
        """
        return [track.lba for track in self.track_list]

    def audio_offsets(self) -> List[int]:
        """
        Return a list of LBA offsets of audio tracks on the CD. They are used
        for calculating AccurateRip disc IDs.
        """
        return [track.lba for track in self.track_list if track.fmt == 'audio']


if __name__ == '__main__':
    disc_info = DiscInfo.from_cd()
    disc_info.print_table()
