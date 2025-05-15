#  Copyright (C) 2006, 2008-2009, 2013, 2018-2019, 2021 Rocky Bernstein <rocky@gnu.org>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The CD Input and Control library (pycdio) encapsulates CD-ROM
reading and control. Applications wishing to be oblivious of the OS-
and device-dependent properties of a CD-ROM can use this library."""

import pycdio


class DeviceException(Exception):
    """General device or driver exceptions"""


class DriverError(DeviceException):
    pass


class DriverUnsupportedError(DeviceException):
    pass


class DriverUninitError(DeviceException):
    pass


class DriverNotPermittedError(DeviceException):
    pass


class DriverBadParameterError(DeviceException):
    pass


class DriverBadPointerError(DeviceException):
    pass


class NoDriverError(DeviceException):
    pass


class TrackError(DeviceException):
    pass


def __possibly_raise_exception__(drc, msg=None):
    """Raise a Driver Error exception on error as determined by drc"""
    if drc == pycdio.DRIVER_OP_SUCCESS:
        return
    if drc == pycdio.DRIVER_OP_ERROR:
        raise DriverError
    if drc == pycdio.DRIVER_OP_UNINIT:
        raise DriverUninitError
    if drc == pycdio.DRIVER_OP_UNSUPPORTED:
        raise DriverUnsupportedError
    if drc == pycdio.DRIVER_OP_NOT_PERMITTED:
        raise DriverUnsupportedError
    if drc == pycdio.DRIVER_OP_BAD_PARAMETER:
        raise DriverBadParameterError
    if drc == pycdio.DRIVER_OP_BAD_POINTER:
        raise DriverBadPointerError
    if drc == pycdio.DRIVER_OP_NO_DRIVER:
        raise NoDriverError
    raise DeviceException("unknown exception %d" % drc)


class Device:
    """CD Input and control class for discs/devices"""

    def __init__(self, source=None, driver_id=None, access_mode=None):
        self.cd = None
        if source is not None or driver_id is not None:
            self.open(source, driver_id, access_mode)

    def close(self):
        """close(self)
        Free resources associated with p_cdio.  Call this when done using
        using CD reading/control operations for the current device.
        """
        if self.cd is not None:
            pycdio.close(self.cd)
        else:
            print("***No object to close")
        self.cd = None

    def get_first_track(self):
        """
        get_first_track(self)->Track

        return a Track object of the first track. None is returned
        if there was a problem.
        """
        track = pycdio.get_first_track_num(self.cd)
        if track == pycdio.INVALID_TRACK:
            return None
        return Track(self.cd, track)

    def get_last_session(self):
        """get_last_session(self) -> int
        Get the LSN of the first track of the last session of on the CD.
        An exception is thrown on error."""
        drc, session = pycdio.get_last_session(self.cd)
        __possibly_raise_exception__(drc)
        return session

    def get_last_track(self):
        """
        get_last_track(self)->Track

        return a Track object of the first track. None is returned
        if there was a problem.
        """
        track = pycdio.get_last_track_num(self.cd)
        if track == pycdio.INVALID_TRACK:
            return None
        return Track(self.cd, track)

    def get_num_tracks(self):
        """
        get_num_tracks(self)->int

        Return the number of tracks on the CD.
        A TrackError or IOError exception may be raised on error.
        """
        track = pycdio.get_num_tracks(self.cd)
        if track == pycdio.INVALID_TRACK:
            raise TrackError("Invalid track returned")
        return track

    def get_track(self, track_num):
        """
        get_track(self, track_num)->track

        Return a track object for the given track number.
        """
        return Track(self.cd, track_num)

    def open(self, source=None, driver_id=pycdio.DRIVER_UNKNOWN, access_mode=None):
        """
        open(self, source=None, driver_id=pycdio.DRIVER_UNKNOWN,
             access_mode=None)

        Sets up to read from place specified by source, driver_id and
        access mode. This should be called before using any other routine
        except those that act on a CD-ROM drive by name.

        If None is given as the source, we'll use the default driver device.
        If None is given as the driver_id, we'll find a suitable device driver.

        If device object was, previously opened it is closed first.

        Device is opened so that subsequent operations can be performed.

        """
        if driver_id is None:
            driver_id = pycdio.DRIVER_UNKNOWN
        if self.cd is not None:
            self.close()
        self.cd = pycdio.open_cd(source, driver_id, access_mode)


class Track:
    """CD Input and control track class"""

    def __init__(self, device, track_num):

        if type(track_num) != int:
            raise TrackError("track number parameter is not an integer")
        self.track = track_num

        # See if the device parameter is a string or
        # a device object.
        if type(device) == bytes:
            self.device = Device(device)
        else:
            Device()
            ## FIXME: would like a way to test if device
            ## is a PySwigObject
            self.device = device

    def get_format(self):
        """
        get_format(self)->format

        Get the format (e.g. 'audio', 'mode2', 'mode1') of track.
        """
        return pycdio.get_track_format(self.device, self.track)

    def get_last_lsn(self):
        """
        get_last_lsn(self)->lsn

        Return the ending LSN for a track
        A TrackError or IOError exception may be raised on error.
        """
        lsn = pycdio.get_track_last_lsn(self.device, self.track)
        if lsn == pycdio.INVALID_LSN:
            raise TrackError("Invalid LSN returned")
        return lsn

    def get_lba(self):
        """
        get_lsn(self)->lba

        Return the starting LBA for a track
        A TrackError exception is raised on error.
        """
        lba = pycdio.get_track_lba(self.device, self.track)
        if lba == pycdio.INVALID_LBA:
            raise TrackError("Invalid LBA returned")
        return lba

    def get_lsn(self):
        """
        get_lsn(self)->lsn

        Return the starting LSN for a track
        A TrackError exception is raised on error.
        """
        lsn = pycdio.get_track_lsn(self.device, self.track)
        if lsn == pycdio.INVALID_LSN:
            raise TrackError("Invalid LSN returned")
        return lsn
