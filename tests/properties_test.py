"""Tests of getting audio file properties."""

# pylint: disable=missing-function-docstring

import os
import unittest

from arver.audio.properties import get_nframes

CWD = os.path.abspath(os.path.dirname(__file__))
SAMPLE_WAV_PATH = CWD + '/data/samples/sample.wav'
SAMPLE_FLAC_PATH = CWD + '/data/samples/sample.flac'


class TestGetNFrames(unittest.TestCase):
    """Test getting the number of audio frames."""

    expected_frames = 44100  # one second of CDDA audio: number of frames same as sampling rate

    def test_wav(self):
        frames = get_nframes(SAMPLE_WAV_PATH)
        self.assertEqual(frames, self.expected_frames)

    def test_flac(self):
        frames = get_nframes(SAMPLE_FLAC_PATH)
        self.assertEqual(frames, self.expected_frames)
