"""Functions for getting properties of supported audio files."""

from arver.audio import _audio


def get_frame_count(path: str) -> int:
    """
    Return the number of frames in a supported audio file. A frame
    is a set of samples, one sample per channel.

    This function supports WAV and FLAC files compliant with CDDA
    standard (16-bit stereo LPCM, 44100 Hz). Underlying C extension
    will raise TypeError for any other audio format, or OSError when
    libsndfile can't load audio samples from the file for any reason.
    """
    return _audio.frame_count(path)
