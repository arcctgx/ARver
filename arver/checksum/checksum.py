"""Functions for calculating checksums of audio files."""

from typing import Optional, Tuple

from arver.checksum import accuraterip  # type: ignore


def accuraterip_checksums(path, track_no, total_tracks) -> Tuple[int, int]:
    """
    Calculate AccurateRip v1 and v2 checksums of specified file.
    WAV and FLAC formats are supported.

    The track_no and total_tracks arguments are used to recognize
    if the track is the first or the last one on CD. These two
    tracks are treated specially by AccurateRip checksum algorithm.

    Return a pair of checksums (v1, v2) as unsigned integers, or a
    pair of zeros if an error occurred during checksum calculation.
    """
    # pylint: disable=c-extension-no-member
    ar1, ar2 = accuraterip.compute(path, track_no, total_tracks)

    if ar1 is None or ar2 is None:
        return 0x0, 0x0

    return ar1, ar2


def copy_crc(path: str) -> Optional[int]:
    """
    Calculate copy CRC of ripped audio file.
    Returns an unsigned integer on success or None on error.
    """
    # pylint: disable=c-extension-no-member
    try:
        return accuraterip.crc32(path)
    except (OSError, TypeError):
        return None
