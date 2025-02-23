"""Offset detection tests."""

# pylint: disable=missing-function-docstring

import unittest

from arver.audio.checksums import get_frame450_checksums

SAMPLE_NEGATIVE = 'tests/data/samples/offset_negative.flac'
SAMPLE_POSITIVE = 'tests/data/samples/offset_positive.flac'
SAMPLE_ZERO = 'tests/data/samples/offset_zero.flac'


class TestOffsetDetectionSector450(unittest.TestCase):
    """
    Test offset detection based of sector 450 checksums using real CD rips.
    The sample data are initial 456 CD sectors of tracks with known sample
    offsets and checksums. 456 CD sectors is the minimum length required
    to calculate all possible offsets in the search radius (from -2940 to
    +2940 audio frames).

    Expected sector 450 checksums were downloaded directly from AccurateRip
    database. The expected offset values were calculated with dBpoweramp
    (the reference implementation).
    """

    def test_negative_offset(self):
        checksums = get_frame450_checksums(SAMPLE_NEGATIVE)
        self.assertEqual(checksums[0x783a76de], -196)

    def test_positive_offset(self):
        checksums = get_frame450_checksums(SAMPLE_POSITIVE)
        self.assertEqual(checksums[0x1ec03108], +694)

    def test_zero_offset(self):
        checksums = get_frame450_checksums(SAMPLE_ZERO)
        self.assertEqual(checksums[0x07d5ca6b], 0)
