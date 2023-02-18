"""Disc info module for ARver."""

from dataclasses import dataclass
from typing import List

import cdio
import pycdio


@dataclass
class _Track:
    num: int
    # lsn: int
    lba: int
    length: int
    fmt: str

    def __str__(self):
        # return f'{self.num:2d}\t{self.lsn:6d}\t{self.lba:6d}\t{self.length:6d}\t{self.fmt:>6s}'
        return f'{self.num:2d}\t{self.lba:6d}\t{self.length:6d}\t{self.fmt:>6s}'


@dataclass
class DiscInfo:
    """
    Representation of Compact Disc properties required for
    calculation of an AccurateRip disc ID.
    """
    track_list: List[_Track]
    lead_out: int

    def print_table(self) -> None:
        """Print disc information as a track listing."""
        # print(f' #\t{"LSN":>6s}\t{"LBA":>6s}\t{"frames":6s}\tformat')
        # print(f'--\t{"-"*6}\t{"-"*6}\t{"-"*6}\t{"-"*6}')
        print(f' #\t{"LBA":>6s}\t{"frames":6s}\tformat')
        print(f'--\t{"-"*6}\t{"-"*6}\t{"-"*6}')

        for track in self.track_list:
            print(track)

        print(f'AA\t{self.lead_out:6d}')

    @classmethod
    def from_cd(cls):
        """Read disc properties from a physical CD in the default device."""
        device = cdio.Device(driver_id=pycdio.DRIVER_DEVICE)

        first = device.get_first_track().track
        n_tracks = device.get_num_tracks()

        tracklist = []

        for trk in range(first, n_tracks + 1):
            track = device.get_track(trk)
            num = track.track
            # lsn = track.get_lsn()  # from lead-in
            lba = track.get_lba()  # from sector zero
            frames = track.get_last_lsn() - track.get_lsn() + 1
            fmt = track.get_format()

            # tracklist.append(_Track(num, lsn, lba, frames, fmt))
            tracklist.append(_Track(num, lba, frames, fmt))

        lead_out = device.get_track(pycdio.CDROM_LEADOUT_TRACK)

        return cls(tracklist, lead_out.get_lba())

    @classmethod
    def from_discid(cls, discid):
        """
        Get disc properties from MusicBrainz by disc ID. This is useful only
        when the CD is pure Red Book audio CD. MusicBrainz disc ID does not
        encode information about data tracks, but this information is required
        to calculate AccurateRip disc ID.
        """
        raise NotImplementedError


if __name__ == '__main__':
    disc_info = DiscInfo.from_cd()
    disc_info.print_table()
