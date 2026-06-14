"""ARver version string module."""

from arver import APPNAME, VERSION
from arver.audio._audio import libsndfile_version
from arver.disc._cdio import libcdio_version


def version_string() -> str:
    """Return full ARver version string, including dependency versions."""
    number = VERSION.lstrip('v')
    return f'{APPNAME}-{number} ({libcdio_version()}, {libsndfile_version()})'
