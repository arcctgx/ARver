"""
Functions for getting properties of supported audio files,
or of libsndfile library itself.
"""

# pylint: disable=c-extension-no-member

from arver.checksum import accuraterip


def get_nframes(path: str) -> int:
    """
    Return the number of frames in a supported audio file, or None
    on error. A frame is a set of samples, one sample per channel.

    This function supports WAV and FLAC files compliant with CDDA
    standard (16-bit stereo LPCM, 44100 Hz). Underlying C extension
    will raise TypeError for any other audio format, or OSError when
    libsndfile can't load audio samples from the file for any reason.
    """
    return accuraterip.nframes(path)


def libsndfile_version() -> str:
    """Return libsndfile version string."""
    return accuraterip.libsndfile_version()
