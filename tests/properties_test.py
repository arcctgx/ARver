"""Tests of getting audio file properties."""

# pylint: disable=missing-function-docstring

import os
import unittest

from arver.checksum.properties import get_nframes

CWD = os.path.abspath(os.path.dirname(__file__))
NOT_AUDIO_PATH = CWD + '/data/not_audio'
SAMPLE_WAV_PATH = CWD + '/data/sample.wav'
SAMPLE_FLAC_PATH = CWD + '/data/sample.flac'
SAMPLE_VORBIS_PATH = CWD + '/data/sample.ogg'


class TestGetNFrames(unittest.TestCase):
    """Test getting the number of audio frames."""

    expected_frames = 44100  # one second of CDDA audio: number of frames same as sampling rate

    def test_nonexistent_file(self):
        self.assertRaises(OSError, get_nframes, 'does_not_exist.flac')

    def test_not_audio(self):
        self.assertRaises(OSError, get_nframes, NOT_AUDIO_PATH)

    def test_unsupported_audio_format(self):
        self.assertRaises(TypeError, get_nframes, SAMPLE_VORBIS_PATH)

    def test_wav(self):
        frames = get_nframes(SAMPLE_WAV_PATH)
        self.assertEqual(frames, self.expected_frames)

    def test_flac(self):
        frames = get_nframes(SAMPLE_FLAC_PATH)
        self.assertEqual(frames, self.expected_frames)
