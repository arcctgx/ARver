"""Checksum calculation tests."""

# pylint: disable=missing-function-docstring

import os
import unittest

from arver.audio.checksums import get_checksums

CWD = os.path.abspath(os.path.dirname(__file__))
SAMPLE_WAV_PATH = CWD + '/data/samples/sample.wav'
SAMPLE_BE_WAV_PATH = CWD + '/data/samples/sample_be.wav'
SAMPLE_FLAC_PATH = CWD + '/data/samples/sample.flac'
SILENCE_WAV_PATH = CWD + '/data/samples/silence.wav'


class TestAccurateRip(unittest.TestCase):
    """Test calculation of AccurateRip checksums."""

    only_track = {'ar1': 0xf43f9174, 'ar2': 0x0ae7c6f9}
    first_track = {'ar1': 0x9d6c90ec, 'ar2': 0xb775893e}
    middle_track = {'ar1': 0x3c8dd1d2, 'ar2': 0x56bba272}
    last_track = {'ar1': 0x9360d25a, 'ar2': 0xaa2de02d}
    silence = {'ar1': 0x0, 'ar2': 0x0}

    def test_wav_only_track(self):
        result = get_checksums(SAMPLE_WAV_PATH, 1, 1)
        accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
        self.assertEqual(accuraterip, self.only_track)

    def test_wav_first_track(self):
        result = get_checksums(SAMPLE_WAV_PATH, 1, 99)
        accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
        self.assertEqual(accuraterip, self.first_track)

    def test_wav_middle_track(self):
        result = get_checksums(SAMPLE_WAV_PATH, 10, 99)
        accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
        self.assertEqual(accuraterip, self.middle_track)

    def test_wav_last_track(self):
        result = get_checksums(SAMPLE_WAV_PATH, 99, 99)
        accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
        self.assertEqual(accuraterip, self.last_track)

    def test_flac_only_track(self):
        result = get_checksums(SAMPLE_FLAC_PATH, 1, 1)
        accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
        self.assertEqual(accuraterip, self.only_track)

    def test_flac_first_track(self):
        result = get_checksums(SAMPLE_FLAC_PATH, 1, 99)
        accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
        self.assertEqual(accuraterip, self.first_track)

    def test_flac_middle_track(self):
        result = get_checksums(SAMPLE_FLAC_PATH, 10, 99)
        accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
        self.assertEqual(accuraterip, self.middle_track)

    def test_flac_last_track(self):
        result = get_checksums(SAMPLE_FLAC_PATH, 99, 99)
        accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
        self.assertEqual(accuraterip, self.last_track)

    def test_silence(self):
        for track, total in [(1, 1), (1, 99), (10, 99), (99, 99)]:
            result = get_checksums(SILENCE_WAV_PATH, track, total)
            accuraterip = {key: result[key] for key in ('ar1', 'ar2')}
            self.assertEqual(accuraterip, self.silence)


class TestCrc32(unittest.TestCase):
    """
    Test calculation of CRC32 checksums.

    The track number and total tracks are fixed because CRC32 value doesn't
    depend on track's position on the CD, so the exact values don't matter.
    """

    track = 5
    total = 10
    sample = {'crc': 0x8ce80129, 'crcss': 0x2d5000dc}
    silence = {'crc': 0x769282bb, 'crcss': 0x0}

    def test_wav(self):
        result = get_checksums(SAMPLE_WAV_PATH, self.track, self.total)
        crc = {key: result[key] for key in ('crc', 'crcss')}
        self.assertEqual(crc, self.sample)

    def test_wav_big_endian(self):
        result = get_checksums(SAMPLE_BE_WAV_PATH, self.track, self.total)
        crc = {key: result[key] for key in ('crc', 'crcss')}
        self.assertEqual(crc, self.sample)

    def test_flac(self):
        result = get_checksums(SAMPLE_FLAC_PATH, self.track, self.total)
        crc = {key: result[key] for key in ('crc', 'crcss')}
        self.assertEqual(crc, self.sample)

    def test_silence(self):
        result = get_checksums(SILENCE_WAV_PATH, self.track, self.total)
        crc = {key: result[key] for key in ('crc', 'crcss')}
        self.assertEqual(crc, self.silence)
