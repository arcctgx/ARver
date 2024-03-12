"""
Direct tests of C extension module. Only edge cases and exceptions are tested
here. Returned values are verified elsewhere using Python wrapper functions.
"""

# pylint: disable=missing-function-docstring

import os
import unittest

from arver.audio.accuraterip import compute, crc32, nframes

CWD = os.path.abspath(os.path.dirname(__file__))
NOT_AUDIO_PATH = CWD + '/data/samples/not_audio'
SAMPLE_VORBIS_PATH = CWD + '/data/samples/sample.ogg'


class TestExceptionsAccurateRip(unittest.TestCase):
    """Test exceptions raised during calculation of AccurateRip checksums."""

    def test_invalid_total_tracks(self):
        for total_tracks in [-1, 0, 100, 1000, 0xffffffff]:
            with self.assertRaisesRegex(ValueError, 'Invalid total_tracks'):
                compute('file.wav', 1, total_tracks)

    def test_invalid_track_number(self):
        for track, total in [(-1, 1), (0, 10), (99, 10), (1000, 99)]:
            with self.assertRaisesRegex(ValueError, 'Invalid track'):
                compute('file.wav', track, total)

    def test_nonexistent_file(self):
        with self.assertRaisesRegex(OSError, 'No such file or directory'):
            compute('no_such_file.wav', 1, 9)

    def test_not_audio_file(self):
        with self.assertRaisesRegex(OSError, 'File contains data in an unknown format'):
            compute(NOT_AUDIO_PATH, 1, 9)

    def test_unsupported_audio_format(self):
        with self.assertRaisesRegex(TypeError, 'check_fileformat failed'):
            compute(SAMPLE_VORBIS_PATH, 1, 9)


class TestExceptionsCrc32(unittest.TestCase):
    """Test exceptions raised during calculation of CRC32 checksum."""

    def test_nonexistent_file(self):
        with self.assertRaisesRegex(OSError, 'No such file or directory'):
            crc32('no_such_file.wav')

    def test_not_audio_file(self):
        with self.assertRaisesRegex(OSError, 'File contains data in an unknown format'):
            crc32(NOT_AUDIO_PATH)

    def test_unsupported_audio_format(self):
        with self.assertRaisesRegex(TypeError, 'Unsupported audio format'):
            crc32(SAMPLE_VORBIS_PATH)


class TestExceptionsNframes(unittest.TestCase):
    """Test exceptions raised when getting the number of audio frames in a file."""

    def test_nonexistent_file(self):
        with self.assertRaisesRegex(OSError, 'No such file or directory'):
            nframes('does_not_exist.flac')

    def test_not_audio(self):
        with self.assertRaisesRegex(OSError, 'File contains data in an unknown format'):
            nframes(NOT_AUDIO_PATH)

    def test_unsupported_audio_format(self):
        with self.assertRaisesRegex(TypeError, 'Unsupported audio format'):
            nframes(SAMPLE_VORBIS_PATH)
