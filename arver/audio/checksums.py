"""Functions for calculating checksums of audio files."""

from typing import Tuple

from arver.audio import _audio  # type: ignore

# pylint: disable=c-extension-no-member


def accuraterip_checksums(path: str, track_no: int, total_tracks: int) -> Tuple[int, int]:
    """
    Calculate AccurateRip v1 and v2 checksums of specified file.
    Return a pair of checksums (v1, v2) as unsigned integers.

    This function supports WAV and FLAC files compliant with CDDA
    standard (16-bit stereo LPCM, 44100 Hz). Underlying C extension
    will raise TypeError for any other audio format, or OSError when
    libsndfile can't load audio samples from the file for any reason.

    The track_no and total_tracks arguments are used to recognize
    if the track is the first or the last one on CD. These two
    tracks are treated specially by AccurateRip checksum algorithm.
    ValueError is raised if the track numbers are not valid.
    """
    return _audio.accuraterip(path, track_no, total_tracks)


def copy_crc(path: str) -> int:
    """
    Calculate CRC32 checksum of an audio file based only on audio
    frames. Return an unsigned integer.

    This function supports WAV and FLAC files compliant with CDDA
    standard (16-bit stereo LPCM, 44100 Hz). Underlying C extension
    will raise TypeError for any other audio format, or OSError when
    libsndfile can't load audio samples from the file for any reason.
    """
    return _audio.crc32(path)
