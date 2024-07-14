"""
Direct tests of C extension module. Only edge cases and exceptions are tested
here. Returned values are verified elsewhere using Python wrapper functions.
"""

# pylint: disable=c-extension-no-member
# pylint: disable=missing-function-docstring

import os
import unittest

from arver.audio import _audio  # type: ignore

CWD = os.path.abspath(os.path.dirname(__file__))
NOT_AUDIO_PATH = CWD + '/data/samples/not_audio'
SAMPLE_VORBIS_PATH = CWD + '/data/samples/sample.ogg'
CORRUPTED_AUDIO_PATH = CWD + '/data/samples/corrupted.flac'


class TestExceptionsChecksums(unittest.TestCase):
    """Test exceptions raised during calculation of AccurateRip and CRC32 checksums."""

    def test_invalid_total_tracks(self):
        for total_tracks in [-1, 0, 100, 1000, 0xffffffff]:
            with self.assertRaisesRegex(ValueError, 'Invalid total_tracks'):
                _audio.checksums('file.wav', 1, total_tracks)

    def test_invalid_track_number(self):
        for track, total in [(-1, 1), (0, 10), (99, 10), (1000, 99)]:
            with self.assertRaisesRegex(ValueError, 'Invalid track'):
                _audio.checksums('file.wav', track, total)

    def test_nonexistent_file(self):
        with self.assertRaisesRegex(OSError, 'No such file or directory'):
            _audio.checksums('no_such_file.wav', 1, 9)

    def test_not_audio_file(self):
        with self.assertRaisesRegex(OSError, '(unknown format|Format not recognised)'):
            _audio.checksums(NOT_AUDIO_PATH, 1, 9)

    def test_unsupported_audio_format(self):
        with self.assertRaisesRegex(TypeError, 'Unsupported audio format'):
            _audio.checksums(SAMPLE_VORBIS_PATH, 1, 9)

    def test_corrupted_audio(self):
        with self.assertRaisesRegex(OSError, 'Failed to load audio samples'):
            _audio.checksums(CORRUPTED_AUDIO_PATH, 1, 9)


class TestExceptionsNframes(unittest.TestCase):
    """Test exceptions raised when getting the number of audio frames in a file."""

    def test_nonexistent_file(self):
        with self.assertRaisesRegex(OSError, 'No such file or directory'):
            _audio.nframes('does_not_exist.flac')

    def test_not_audio(self):
        with self.assertRaisesRegex(OSError, '(unknown format|Format not recognised)'):
            _audio.nframes(NOT_AUDIO_PATH)

    def test_unsupported_audio_format(self):
        with self.assertRaisesRegex(TypeError, 'Unsupported audio format'):
            _audio.nframes(SAMPLE_VORBIS_PATH)
