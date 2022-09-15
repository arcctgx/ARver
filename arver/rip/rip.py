"""Rip module for ARver."""

import os
import wave

from arver.checksum.checksum import copy_crc


CHANNELS = 2
BYTES_PER_SAMPLE = 2
SAMPLES_PER_SECOND = 44100
SAMPLES_PER_SECTOR = 588


def _is_cd_rip(path):
    """
    Determine if specified WAV file has been ripped from a CD.

    WAV files ripped from a CD are 16-bit LPCM stereo with 44.1 kHz frequency.
    Python wave module doesn't provide means to determine if the file is LPCM
    or anything else, so the function doesn't check that.
    """
    try:
        with wave.open(path) as wav:
            params = wav.getparams()
            return params.nchannels == CHANNELS and \
                   params.sampwidth == BYTES_PER_SAMPLE and \
                   params.framerate == SAMPLES_PER_SECOND
    except (OSError, wave.Error):
        return False


def _get_track_sectors(path):
    """Return track length as integer CD sectors or -1 on error."""
    try:
        with wave.open(path) as wav:
            return wav.getnframes() // SAMPLES_PER_SECTOR
    except (OSError, wave.Error):
        return -1


def _get_track_length(path):
    """Return track length as string in mm:ss.ss format or None on error."""
    try:
        with wave.open(path) as wav:
            total_seconds = wav.getnframes() / SAMPLES_PER_SECOND
            minutes = int(total_seconds / 60)
            seconds = total_seconds % 60
            return f'{minutes:02d}:{seconds:05.2f}'
    except (OSError, wave.Error):
        return None


class _WavFile:
    """Class to represent a WAV file ripped from CD."""
    def __init__(self, path):
        self._path = path
        self._file_name = os.path.basename(path)
        self._is_rip = _is_cd_rip(path)
        self._sectors = _get_track_sectors(path)
        self._length = _get_track_length(path)
        self._crc = copy_crc(path)

    def __repr__(self):
        return f'{self._file_name}\t{self._is_rip}\t' + \
               f'{self._sectors:6d}\t{self._length}\t{self._crc:08x}'


def _filter_htoa(paths):
    """TODO"""
    return paths


class Rip:
    """This class represents a set of ripped WAV files to be verified."""
    def __init__(self, paths):
        if not paths:
            raise ValueError

        self.tracks = []
        for path in _filter_htoa(paths):
            self.tracks.append(_WavFile(path))

    def __repr__(self):
        str_ = []
        for track in self.tracks:
            str_.append(repr(track))
        return '\n'.join(str_)

    def verify(self, disc):
        """Verify a set of ripped files against a CD with specified TOC."""
        raise NotImplementedError
