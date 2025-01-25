"""Functions for calculating checksums of audio files."""

from typing import List, Tuple

from arver.audio import _audio  # type: ignore

# pylint: disable=c-extension-no-member


def get_checksums(path: str, track_no: int, total_tracks: int) -> Tuple[int, int, int]:
    """
    Calculate AccurateRip and CRC32 checksums of specified file.
    Return a triple of checksums (v1, v2, crc32) as unsigned integers.

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


def get_frame450_checksums(path: str) -> List[Tuple[int, int]]:
    """
    Calculate AccurateRip v1 checksums of a single CD frame (588 samples)
    across all possible sample offsets in a 5-frame window centered on
    frame 450.

    The result is a list of 5881 (offset, checksum) pairs. If the track
    is too short for calculating a checksum for a specific offset, the
    checksum for that offset is zero.

    Raises TypeError and OSError in the same conditions as get_checksums().
    OSError is additionally raised on an internal failure to create a list
    or a tuple.
    """
    return _audio.f450_checksums(path)
