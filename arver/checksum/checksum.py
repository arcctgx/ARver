"""Functions for calculating checksums of WAV files."""

import binascii
import wave

from typing import Tuple

from arver.checksum import accuraterip  # type: ignore


def accuraterip_checksums(wav_file, track_no, total_tracks) -> Tuple[int, int]:
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
    ar1, ar2 = accuraterip.compute(wav_file, track_no, total_tracks)

    if ar1 is None or ar2 is None:
        return 0x0, 0x0

    return ar1, ar2


def copy_crc(wav_file):
    """
    Calculate copy CRC of ripped WAV file.
    Returns an unsigned integer on success or None on error.
    """
    try:
        with wave.open(wav_file) as wav:
            nframes = wav.getnframes()
            data = wav.readframes(nframes)
            return binascii.crc32(data) & 0xffffffff
    except (OSError, wave.Error):
        return None
