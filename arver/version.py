"""ARver version string module."""

from arver import APPNAME, VERSION
from arver.audio.properties import get_libsndfile_version


def version_string() -> str:
    """Return full ARver version string, including libsndfile version."""
    number = VERSION.lstrip('v')
    return f'{APPNAME}-{number} ({get_libsndfile_version()})'
