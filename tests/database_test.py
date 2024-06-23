"""Tests of AccurateRip database interface."""

# pylint: disable=missing-function-docstring
# pylint: disable=protected-access

import json
import os
import struct
import unittest

from arver.disc.database import AccurateRipDisc, AccurateRipFetcher

CWD = os.path.abspath(os.path.dirname(__file__))
RESPONSES_DIR = CWD + '/data/responses'


def _load_json_disc_data(disc_id: str) -> dict:
    """
    Load dictionary in format compatible with AccurateRipDisc.make_dict() from
    a JSON file. Convert outer keys (track numbers) and inner keys (checksum
    values) from strings to integers. This is a workaround for a limitation of
    JSON serialization.

    An alternative would be to use a Python pickle instead of JSON (but it's not
    human-readable, so would be too hard to maintain), or to serialize to YAML
    instead of JSON (but that would require another dependency only used in
    the tests).
    """
    path = f'{RESPONSES_DIR}/dBAR-{disc_id}.json'
    with open(path, encoding='utf-8') as disc:
        raw = json.load(disc)

    converted = {}
    for track, checksums in raw.items():
        converted[int(track)] = {int(k): v for k, v in checksums.items()}

    return converted


def _parse_binary_disc_data(disc_id: str) -> AccurateRipDisc:
    fetcher = AccurateRipFetcher.from_id(disc_id)

    path = f'{RESPONSES_DIR}/dBAR-{disc_id}.bin'
    with open(path, 'rb') as response:
        fetcher._raw_bytes = response.read()

    return fetcher._parse_raw_bytes()


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

    def test_single_track_response(self):
        disc_id = '001-000441fd-000883fb-020e8801'

        actual = _parse_binary_disc_data(disc_id).make_dict()
        expected = _load_json_disc_data(disc_id)

        self.assertEqual(actual, expected)

    def test_multi_track_response(self):
        disc_id = '013-00206791-01486a82-a710de0d'

        actual = _parse_binary_disc_data(disc_id).make_dict()
        expected = _load_json_disc_data(disc_id)

        self.assertEqual(actual, expected)

    def test_discard_zero_confidence_checksums(self):
        disc_id = '099-009fc8d0-224410e4-6308d763'

        actual = _parse_binary_disc_data(disc_id).make_dict()
        expected = _load_json_disc_data(disc_id)

        self.assertEqual(actual, expected)

    def test_mixed_mode_cd_response(self):
        disc_id = '042-00b15696-110290c9-b6115d2b'

        actual = _parse_binary_disc_data(disc_id).make_dict()
        expected = _load_json_disc_data(disc_id)

        self.assertEqual(actual, expected)
