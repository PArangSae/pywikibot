#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Unit tests for checkimages script."""
#
# (C) Pywikibot team, 2015-2020
#
# Distributed under the terms of the MIT license.
#
from scripts import checkimages

from tests.aspects import unittest, TestCase


class TestSettings(TestCase):

    """Test checkimages settings."""

    family = 'commons'
    code = 'commons'
    user = True

    def test_load(self):
        """Test loading settings."""
        b = checkimages.checkImagesBot(self.get_site())
        b.takesettings()
        rv = b.settingsData
        item1 = rv[0]
        self.assertEqual(item1[0], 1)
        self.assertEqual(item1[1], 'a deprecated template')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
