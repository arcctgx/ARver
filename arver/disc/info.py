"""Disc info module for ARver."""

from dataclasses import dataclass
from typing import List

import cdio
import pycdio


@dataclass
class _Track:
    num: int
    lsn: int
    lba: int
    length: int
    fmt: str

    def __str__(self):
        return f'{self.num:2d}\t{self.lsn:6d}\t{self.lba:6d}\t{self.length:6d}\t{self.fmt:>6s}'


@dataclass
class DiscInfo:
    track_list: List[_Track]
    lead_out: int

    @classmethod
    def from_cd(cls):
        device = cdio.Device(driver_id=pycdio.DRIVER_DEVICE)

        first = device.get_first_track().track
        n_tracks = device.get_num_tracks()

        print(f' #\t{"LSN":>6s}\t{"LBA":>6s}\t{"frames":6s}\tformat')
        print(f'--\t{"-"*6}\t{"-"*6}\t{"-"*6}\t{"-"*6}')

        tracklist = []

        for trk in range(first, n_tracks + 1):
            track = device.get_track(trk)
            num = track.track
            lsn = track.get_lsn()  # from lead-in
            lba = track.get_lba()  # from sector zero
            frames = track.get_last_lsn() - track.get_lsn() + 1
            fmt = track.get_format()

            tracklist.append(_Track(num, lsn, lba, frames, fmt))

        for track in tracklist:
            print(track)

        leadout = device.get_track(pycdio.CDROM_LEADOUT_TRACK)
        print(f'aa\t{leadout.get_lsn()}\t{leadout.get_lba()}')

        return cls(tracklist, leadout)

    @classmethod
    def from_discid(cls, discid):
        raise NotImplementedError


if __name__ == '__main__':
    DiscInfo.from_cd()
