"""Tests of AccurateRip database interface."""

# pylint: disable=missing-function-docstring
# pylint: disable=protected-access

import os
import struct
import unittest

from arver.disc.database import AccurateRipFetcher

CWD = os.path.abspath(os.path.dirname(__file__))
RESPONSES_DIR = CWD + '/data/responses'


class TestBinaryParser(unittest.TestCase):
    """Test parsing binary AccurateRip responses."""

    def test_wrong_header(self):
        disc_id = '013-00206791-01486a82-a710de0d'
        fetcher = AccurateRipFetcher.from_id(disc_id)

        with open(f'{RESPONSES_DIR}/wrong_header.bin', 'rb') as response:
            fetcher._raw_bytes = response.read()

        with self.assertRaisesRegex(ValueError, 'Unexpected AccurateRip response header'):
            fetcher._parse_raw_bytes()

    def test_truncated_response(self):
        disc_id = '013-00206791-01486a82-a710de0d'
        fetcher = AccurateRipFetcher.from_id(disc_id)

        with open(f'{RESPONSES_DIR}/truncated_response.bin', 'rb') as response:
            fetcher._raw_bytes = response.read()

        with self.assertRaisesRegex(struct.error, 'unpack requires a buffer'):
            fetcher._parse_raw_bytes()
