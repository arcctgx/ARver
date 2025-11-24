"""Tests of helper functions."""

# pylint: disable=missing-function-docstring

import unittest

from arver.rip.rip import _ceil_div
from arver.utils import frames_to_msf


class TestHelperFunctions(unittest.TestCase):
    """Tests of helper functions."""

    def test_ceiling_division(self):
        self.assertEqual(_ceil_div(0, 588), 0)
        self.assertEqual(_ceil_div(1000, 588), 2)
        self.assertEqual(_ceil_div(2940, 588), 5)

    def test_msf_conversion(self):
        self.assertEqual(frames_to_msf(0), '0:00.00')
        self.assertEqual(frames_to_msf(75), '0:01.00')
        self.assertEqual(frames_to_msf(449999), '99:59.74')
        self.assertEqual(frames_to_msf(450001), '100:00.01')

        with self.assertRaisesRegex(ValueError, 'Negative frames'):
            frames_to_msf(-10)
