"""
AccurateRip Disc.
"""

URL_BASE = 'http://www.accuraterip.com/accuraterip/'


class Disc:
    """AccurateRip Disc."""
    def __init__(self, tracks, ar1, ar2, freedb):
        # maybe it should accept cd_data['id'] instead of three IDs?
        self._tracks = tracks
        self._ar1 = ar1
        self._ar2 = ar2
        self._freedb = freedb
        self._full_id = self._dbar_id()
        self.responses = []

    def _dbar_prefix(self):
        return f'{self._ar1[-1]}/{self._ar1[-2]}/{self._ar1[-3]}/'

    def _dbar_id(self):
        return f'dBAR-0{self._tracks:02d}-{self._ar1}-{self._ar2}-{self._freedb}'

    def get_responses(self):
        """Download AccurateRip responses for specified CD."""
        url = URL_BASE + self._dbar_prefix() + self._dbar_id()
        return NotImplementedError


class Response:
    """AccurateRip response decoded from binary format."""
