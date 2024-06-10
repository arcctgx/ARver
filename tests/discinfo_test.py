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

    def test_from_track_lengths(self):
        """
        Test creating DiscInfo object when only track lengths are known.
        The methods for calculating MusicBrainz and AccureteRip disc IDs
        should return the real disc IDs regardless of disc type.
        """
        test_data = [
            {
                'tracks': [75258, 54815, 205880],
                'pregap': 0,
                'data': 0,
                'musicbrainz_id': 'dUmct3Sk4dAt1a98qUKYKC0ZjYU-',
                'accuraterip_id': '003-00084264-001cc184-19117f03'
            },
            {
                'tracks': [279037],
                'pregap': 0,
                'data': 0,
                'musicbrainz_id': '8yz4363CdyKqNa45C30lZWon5jE-',
                'accuraterip_id': '001-000441fd-000883fb-020e8801'
            },
            {
                'tracks': [107450, 71470, 105737, 71600],
                'pregap': 33,
                'data': 0,
                'musicbrainz_id': 'Grk0WAJTlMgchS.Qilu8OSGvxGg-',
                'accuraterip_id': '004-000e26d9-00380804-3e128e04'
            },
            {
                'tracks': [143963],
                'pregap': 32,
                'data': 0,
                'musicbrainz_id': '0VQH.wupXuvBanCl73_bqdIK7zQ-',
                'accuraterip_id': '001-0002329b-00046516-02077f01'
            },
            {
                'tracks': [12617, 27720, 22738, 30185, 24705, 33750, 32475, 30920, 32195, 22880],
                'pregap': 0,
                'data': 52066,
                'musicbrainz_id': '9AQWqQ0eCCwktwPPrIUIYkUw2Uo-',
                'accuraterip_id': '010-00164419-00b9f6e2-9e11600b',
            },
            {
                'tracks': [90778],
                'pregap': 0,
                'data': 164721,
                'musicbrainz_id': 'ZvhSySPNhWlmkC1x3pEYDnMyoho-',
                'accuraterip_id': '001-00041293-00082527-100de602',
            },
            {
                'tracks': [14765, 14932, 12508, 525, 20937, 6025, 19753, 35570, 17777, 15258,
                           23515, 18512, 26168, 13440],
                'pregap': 12375,
                'data': 0,
                'musicbrainz_id': 'DXMhnAITXIb0ieYp7OECBgjr1gs-',
                'accuraterip_id': '014-001ba337-01281b14-cf0c7b0e',
            }
        ] # yapf: disable

        for disc in test_data:
            disc_info = DiscInfo.from_track_lengths(disc['tracks'], disc['pregap'], disc['data'])
            self.assertEqual(disc_info.musicbrainz_id(), disc['musicbrainz_id'])
            self.assertEqual(disc_info.accuraterip_id(), disc['accuraterip_id'])


if __name__ == '__main__':
    unittest.main()
