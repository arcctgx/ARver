"""Tests of DiscInfo class."""

import unittest

from arver.disc.info import DiscInfo


class TestDiscInfo(unittest.TestCase):
    """Tests of DiscInfo class."""

    def test_discid_recalculation(self):
        """
        When DiscInfo instance is created from a disc ID its musicbrainz_id()
        method should return the same disc ID. Test DiscID calculation with
        three different types of discs.
        Note: this test will send requests to MusicBrainz.
        """
        discids = [
            'X_fUy2PVsk5KK7JciFqBc0CetiI-',  # Audio CD
            '.wsrLgOecMphb09w1pr.ZwcIrj8-',  # Audio CD with pregap
            'j2wJHXA1xXZj7Wkh_tKm4vLjqBk-',  # Mixed Mode CD
            'icmg5lhDisLpCIHbXmBhXUDlN2I-',  # Enhanced CDs
            'ZvhSySPNhWlmkC1x3pEYDnMyoho-'
        ]

        for id_ in discids:
            disc_info = DiscInfo.from_disc_id(id_)
            self.assertIsNotNone(disc_info)
            self.assertEqual(id_, disc_info.musicbrainz_id())


if __name__ == '__main__':
    unittest.main()
