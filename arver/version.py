"""ARver version string module."""

from arver import APPNAME, VERSION
from arver.checksum.properties import libsndfile_version


def version_string() -> str:
    """Return full ARver version string, including libsndfile version."""
    number = VERSION.lstrip('v')
    return f'{APPNAME}-{number} ({libsndfile_version()})'
