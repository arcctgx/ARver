"""Functions for getting version strings."""

# pylint: disable=c-extension-no-member

from arver.audio import _audio  # type: ignore


def get_libsndfile_version() -> str:
    """Return libsndfile version string."""
    return _audio.libsndfile_version()
