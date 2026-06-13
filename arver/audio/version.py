"""Functions for getting version strings."""

from arver.audio import _audio


def get_libsndfile_version() -> str:
    """Return libsndfile version string."""
    return _audio.libsndfile_version()
