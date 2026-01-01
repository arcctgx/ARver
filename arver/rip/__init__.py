"""ARver rip package."""

from os.path import basename

NAME_WIDTH = 30


def _shorten_path(path: str, max_length: int = NAME_WIDTH) -> str:
    """Shorten long path to an abbreviated file name of specified maximum length."""
    name = basename(path)
    if len(name) <= max_length:
        return name

    adj = 0 if max_length % 2 != 0 else -1
    midpoint = max_length // 2
    return name[:midpoint + adj] + '~' + name[-midpoint:]
