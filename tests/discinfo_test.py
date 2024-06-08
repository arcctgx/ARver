"""Tests of DiscInfo class."""

import json
import os
import unittest
from unittest.mock import patch

from arver.disc.info import DiscInfo

CWD = os.path.abspath(os.path.dirname(__file__))


class TestDiscInfo(unittest.TestCase):
    """Tests of DiscInfo class."""

    @patch('musicbrainzngs.get_releases_by_discid')
    def test_discid_recalculation(self, mock_get):
        """
        When DiscInfo instance is created from a disc ID its musicbrainz_id()
        method should return the same disc ID. Test DiscID calculation with
        three different types of discs.
        """
        discids = [
            'X_fUy2PVsk5KK7JciFqBc0CetiI-',  # Audio CD
            'RQ9yuzEHF_fzexjCzj46KcdIaHA-',  # Audio CD with pregap and 99 tracks
            'j2wJHXA1xXZj7Wkh_tKm4vLjqBk-',  # Mixed Mode CD
            'icmg5lhDisLpCIHbXmBhXUDlN2I-',  # Enhanced CDs
            'ZvhSySPNhWlmkC1x3pEYDnMyoho-'
        ]

        for id_ in discids:
            disc_data = f'{CWD}/data/discs/{id_}.json'
            with open(disc_data, encoding='utf-8') as disc:
                mock_disc = json.load(disc)
                mock_get.return_value = mock_disc

            disc_info = DiscInfo.from_disc_id(id_)
            self.assertEqual(id_, disc_info.musicbrainz_id())  # type: ignore

    def test_from_track_frames(self):
        """Test creating DiscInfo object when only track lengths are known."""
        test_data = [{
            'track_frames': [75258, 54815, 205880],
            'pregap_frames': 0,
            'data_frames': 0,
            'musicbrainz_id': 'dUmct3Sk4dAt1a98qUKYKC0ZjYU-',
            'accuraterip_id': '003-00084264-001cc184-19117f03'
        }]

        for disc in test_data:
            disc_info = DiscInfo.from_track_frames(disc['track_frames'], disc['pregap_frames'],
                                                   disc['data_frames'])
            self.assertEqual(disc_info.musicbrainz_id(), disc['musicbrainz_id'])
            self.assertEqual(disc_info.accuraterip_id(), disc['accuraterip_id'])


if __name__ == '__main__':
    unittest.main()
