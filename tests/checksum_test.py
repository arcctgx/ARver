"""Checksum calculation tests."""

import os
import unittest

from arver.checksum.checksum import accuraterip_checksums, copy_crc

CWD = os.path.abspath(os.path.dirname(__file__))
SAMPLE_PATH = CWD + '/data/sample.wav'


class TestAccurateRip(unittest.TestCase):
    """Test calculation of AccurateRip checksums."""

    only_track = (0xf43f9174, 0x0ae7c6f9)
    first_track = (0x9d6c90ec, 0xb775893e)
    middle_track = (0x3c8dd1d2, 0x56bba272)
    last_track = (0x9360d25a, 0xaa2de02d)

    def test_only_track(self):
        result = accuraterip_checksums(SAMPLE_PATH, 1, 1)
        self.assertTupleEqual(result, self.only_track)

    def test_first_track(self):
        result = accuraterip_checksums(SAMPLE_PATH, 1, 99)
        self.assertTupleEqual(result, self.first_track)

    def test_middle_track(self):
        result = accuraterip_checksums(SAMPLE_PATH, 10, 99)
        self.assertTupleEqual(result, self.middle_track)

    def test_last_track(self):
        result = accuraterip_checksums(SAMPLE_PATH, 99, 99)
        self.assertTupleEqual(result, self.last_track)


class TestCopyCRC(unittest.TestCase):
    """Test calculation of CRC32 checksum."""

    crc32 = 0x8ce80129

    def test_copy_crc(self):
        result = copy_crc(SAMPLE_PATH)
        self.assertEqual(result, self.crc32)
