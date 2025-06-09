"""Tests of helper functions."""

# pylint: disable=missing-function-docstring

import unittest

from arver.rip.rip import _ceil_div


class TestHelperFunctions(unittest.TestCase):
    """Tests of helper functions."""

    def test_ceiling_division(self):
        self.assertEqual(_ceil_div(0, 588), 0)
        self.assertEqual(_ceil_div(1000, 588), 2)
        self.assertEqual(_ceil_div(2940, 588), 5)
