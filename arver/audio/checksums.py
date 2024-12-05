"""Functions for calculating checksums of audio files."""

from typing import Dict

from arver.audio import _audio  # type: ignore

# pylint: disable=c-extension-no-member


def get_checksums(path: str, track_no: int, total_tracks: int) -> Dict[str, int]:
    """
    Calculate AccurateRip and CRC32 checksums of specified file.
    Return a dictionary of checksums (ARv1, ARv2, CRC32, skip
    silence CRC32) stored as unsigned integers. The following
    example demonstrates the dictionary structure and key names:

    {
        "ar1": 1015927250,
        "ar2": 1455137394,
        "crc": 2364014889,
        "crcss": 760217820
    }

    This function supports WAV and FLAC files compliant with CDDA
    standard (16-bit stereo LPCM, 44100 Hz). Underlying C extension
    will raise TypeError for any other audio format, or OSError when
    libsndfile can't load audio samples from the file for any reason.

    The track_no and total_tracks arguments are used to recognize
    if the track is the first or the last one on CD. These two
    tracks are treated specially by AccurateRip checksum algorithm.
    ValueError is raised if the track numbers are not valid. These
    arguments don't matter for CRC32 calculation.
    """
    return _audio.checksums(path, track_no, total_tracks)
