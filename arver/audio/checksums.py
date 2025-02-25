"""Functions for calculating checksums of audio files."""

from typing import Dict, Tuple

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


def get_frame450_checksums(path: str) -> Dict[int, int]:
    """
    Calculate AccurateRip v1 checksums of a single CD frame (588 samples)
    across all possible sample offsets in a 5-frame window centered on
    frame 450.

    The underlying C extension returns the result as a list of all 5881
    possible (offset, checksum) pairs. These results are converted to a
    dictionary where the key is the sample offset and the value is the
    frame 450 checksum corresponding to that offset. If the checksum in
    a pair has zero value, that pair is not included in the resulting
    dictionary.

    Raises TypeError and OSError in the same conditions as get_checksums().
    MemoryError is additionally raised on an internal failure to create a
    list or a tuple.
    """
    return {
        checksum: offset
        for (offset, checksum) in _audio.f450_checksums(path) if checksum != 0
    } # yapf: disable
