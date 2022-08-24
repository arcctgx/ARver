"""
ARver disc class.
"""

import json

import cdtoc
import mbtoc


class Disc:
    """
    Class representing a Compact Disc to verify.
    """
    def __init__(self, disc_data):
        self._data = disc_data
        self.tracks = disc_data['toc']['tracks']

    def _dbar_prefix(self):
        ar1 = self._data['id']['accuraterip'][0]
        return f'{ar1[-1]}/{ar1[-2]}/{ar1[-3]}/'

    def _dbar_id(self):
        ar1 = self._data['id']['accuraterip'][0]
        ar2 = self._data['id']['accuraterip'][1]
        freedb = self._data['id']['freedb']
        return f'dBAR-0{self.tracks:02d}-{ar1}-{ar2}-{freedb}'

    @classmethod
    def from_cd(cls):
        disc_data = cdtoc._read_disc_info()
        if disc_data:
            return cls(disc_data)
        raise ValueError

    @classmethod
    def from_disc_id(cls, disc_id):
        disc_data = mbtoc._get_disc_info(disc_id)
        if disc_data:
            return cls(disc_data)
        raise ValueError

    def __repr__(self):
        return json.dumps(self._data, indent=2)
