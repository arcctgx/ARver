"""Checksum calculation tests."""

# pylint: disable=missing-function-docstring

import os
import unittest

from arver.audio.checksums import accuraterip_checksums, copy_crc

CWD = os.path.abspath(os.path.dirname(__file__))
SAMPLE_WAV_PATH = CWD + '/data/samples/sample.wav'
SAMPLE_FLAC_PATH = CWD + '/data/samples/sample.flac'
SILENCE_WAV_PATH = CWD + '/data/samples/silence.wav'


class TestAccurateRip(unittest.TestCase):
    """Test calculation of AccurateRip checksums."""

    only_track = (0xf43f9174, 0x0ae7c6f9)
    first_track = (0x9d6c90ec, 0xb775893e)
    middle_track = (0x3c8dd1d2, 0x56bba272)
    last_track = (0x9360d25a, 0xaa2de02d)
    silence = (0x0, 0x0)

    def test_wav_only_track(self):
        result = accuraterip_checksums(SAMPLE_WAV_PATH, 1, 1)
        self.assertTupleEqual(result, self.only_track)

    def test_wav_first_track(self):
        result = accuraterip_checksums(SAMPLE_WAV_PATH, 1, 99)
        self.assertTupleEqual(result, self.first_track)

    def test_wav_middle_track(self):
        result = accuraterip_checksums(SAMPLE_WAV_PATH, 10, 99)
        self.assertTupleEqual(result, self.middle_track)

    def test_wav_last_track(self):
        result = accuraterip_checksums(SAMPLE_WAV_PATH, 99, 99)
        self.assertTupleEqual(result, self.last_track)

    def test_flac_only_track(self):
        result = accuraterip_checksums(SAMPLE_FLAC_PATH, 1, 1)
        self.assertTupleEqual(result, self.only_track)

    def test_flac_first_track(self):
        result = accuraterip_checksums(SAMPLE_FLAC_PATH, 1, 99)
        self.assertTupleEqual(result, self.first_track)

    def test_flac_middle_track(self):
        result = accuraterip_checksums(SAMPLE_FLAC_PATH, 10, 99)
        self.assertTupleEqual(result, self.middle_track)

    def test_flac_last_track(self):
        result = accuraterip_checksums(SAMPLE_FLAC_PATH, 99, 99)
        self.assertTupleEqual(result, self.last_track)

    def test_silence(self):
        for track, total in [(1, 1), (1, 99), (10, 99), (99, 99)]:
            result = accuraterip_checksums(SILENCE_WAV_PATH, track, total)
            self.assertTupleEqual(result, self.silence)


class TestCopyCRC(unittest.TestCase):
    """Test calculation of CRC32 checksum."""

    sample_crc32 = 0x8ce80129
    silence_crc32 = 0x769282bb

    def test_wav(self):
        result = copy_crc(SAMPLE_WAV_PATH)
        self.assertEqual(result, self.sample_crc32)

    def test_flac(self):
        result = copy_crc(SAMPLE_FLAC_PATH)
        self.assertEqual(result, self.sample_crc32)

    def test_silence(self):
        result = copy_crc(SILENCE_WAV_PATH)
        self.assertEqual(result, self.silence_crc32)
