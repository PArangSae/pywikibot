# -*- coding: utf-8 -*-
"""FilePage tests."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
import os
import re

from contextlib import suppress

import pywikibot

from tests import join_images_path

from tests.aspects import unittest, TestCase


class TestShareFiles(TestCase):

    """Test file_is_shared, exists, fileUrl/get_file_url with shared files."""

    sites = {
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'itwiki': {
            'family': 'wikipedia',
            'code': 'it',
        },
        'testwiki': {
            'family': 'wikipedia',
            'code': 'test',
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
        },
    }

    cached = True

    def test_fileUrl_versus_get_file_url(self):
        """Test fileUrl() is equivalent to get_file_url()."""
        title = 'File:Sepp Maier 1.JPG'
        commons = self.get_site('commons')
        commons_file = pywikibot.FilePage(commons, title)
        self.assertEqual(commons_file.fileUrl(), commons_file.get_file_url())
        itwp = self.get_site('itwiki')
        itwp_file = pywikibot.FilePage(itwp, title)
        self.assertEqual(itwp_file.fileUrl(), itwp_file.get_file_url())

    def testSharedOnly(self):
        """Test file_is_shared() on file page with shared file only."""
        title = 'File:Sepp Maier 1.JPG'

        commons = self.get_site('commons')
        itwp = self.get_site('itwiki')
        itwp_file = pywikibot.FilePage(itwp, title)
        for using in itwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.FilePage(commons, title)

        self.assertFalse(itwp_file.exists())
        self.assertTrue(commons_file.exists())

        self.assertTrue(itwp_file.file_is_shared())
        self.assertTrue(commons_file.file_is_shared())
        self.assertTrue(commons_file.get_file_url())

        self.assertIn('/wikipedia/commons/', itwp_file.get_file_url())
        with self.assertRaisesRegex(
                pywikibot.NoPage,
                (r'Page \[\[(wikipedia:|)it:%s\]\] doesn\'t exist.' % title)):
            itwp_file.get()

    def testLocalOnly(self):
        """Test file_is_shared() on file page with local file only."""
        title = 'File:Untitled (Three Forms), stainless steel sculpture by ' \
                '--James Rosati--, 1975-1976, --Honolulu Academy of Arts--.JPG'

        commons = self.get_site('commons')
        enwp = self.get_site('enwiki')
        enwp_file = pywikibot.FilePage(enwp, title)
        for using in enwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.FilePage(commons, title)

        self.assertTrue(enwp_file.latest_file_info.url)
        self.assertTrue(enwp_file.exists())
        self.assertFalse(commons_file.exists())

        self.assertFalse(enwp_file.file_is_shared())

        page_doesnt_exist_exc_regex = re.escape(
            "Page [[commons:{}]] doesn't exist.".format(title))
        with self.assertRaisesRegex(
                pywikibot.NoPage,
                page_doesnt_exist_exc_regex):
            commons_file.file_is_shared()

        with self.assertRaisesRegex(
                pywikibot.NoPage,
                page_doesnt_exist_exc_regex):
            commons_file.get_file_url()

        with self.assertRaisesRegex(
                pywikibot.NoPage,
                page_doesnt_exist_exc_regex):
            commons_file.get()

    def testOnBoth(self):
        """Test file_is_shared() on file page with local and shared file."""
        title = 'File:Pulsante spam.png'

        commons = self.get_site('commons')
        itwp = self.get_site('itwiki')
        itwp_file = pywikibot.FilePage(itwp, title)
        for using in itwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.FilePage(commons, title)

        self.assertTrue(itwp_file.get_file_url())
        self.assertTrue(itwp_file.exists())
        self.assertTrue(commons_file.exists())

        self.assertFalse(itwp_file.file_is_shared())
        self.assertTrue(commons_file.file_is_shared())

    def testNonFileLocal(self):
        """Test file page, without local file, existing on the local wiki."""
        title = 'File:Sepp Maier 1.JPG'

        commons = self.get_site('commons')
        testwp = self.get_site('testwiki')
        testwp_file = pywikibot.FilePage(testwp, title)

        self.assertTrue(testwp_file.latest_file_info.url)
        self.assertTrue(testwp_file.exists())
        self.assertTrue(testwp_file.file_is_shared())

        commons_file = pywikibot.FilePage(commons, title)
        self.assertEqual(testwp_file.get_file_url(),
                         commons_file.get_file_url())


class TestFilePage(TestCase):

    """Test FilePage.latest_revision_info.

    These tests cover exceptions for all properties and methods
    in FilePage that rely on site.loadimageinfo.

    """

    family = 'wikipedia'
    code = 'test'

    file_name = 'File:Albert Einstein Head.jpg'

    cached = True

    def test_file_info_with_no_page(self):
        """FilePage:latest_file_info raises NoPage for non existing pages."""
        site = self.get_site()
        image = pywikibot.FilePage(site, 'File:NoPage')
        self.assertFalse(image.exists())

        with self.assertRaisesRegex(
                pywikibot.NoPage,
                (r'Page \[\[(wikipedia\:|)test:File:NoPage\]\] '
                 r"doesn't exist\.")):
            image = image.latest_file_info

    def test_file_info_with_no_file(self):
        """FilePage:latest_file_info raises PagerelatedError if no file."""
        site = self.get_site()
        image = pywikibot.FilePage(site, 'File:Test with no image')
        self.assertTrue(image.exists())
        with self.assertRaisesRegex(
                pywikibot.PageRelatedError,
                (r'loadimageinfo: Query on '
                 r'\[\[(wikipedia\:|)test:File:Test with no image\]\]'
                 r' returned no imageinfo')):
            image = image.latest_file_info


class TestFilePageLatestFileInfo(TestCase):

    """Test FilePage.latest_file_info.

    These tests cover properties and methods in FilePage that rely
    on site.loadimageinfo.

    """

    family = 'commons'
    code = 'commons'

    file_name = 'File:Albert Einstein Head.jpg'

    cached = True

    def setUp(self):
        """Create File page."""
        super().setUp()
        self.image = pywikibot.FilePage(self.site, self.file_name)

    def test_get_file_url(self):
        """Get File url."""
        self.assertTrue(self.image.exists())
        self.assertEqual(self.image.get_file_url(),
                         'https://upload.wikimedia.org/wikipedia/commons/'
                         'd/d3/Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.url,
                         'https://upload.wikimedia.org/wikipedia/commons/'
                         'd/d3/Albert_Einstein_Head.jpg')

    def test_get_file_url_thumburl_from_width(self):
        """Get File thumburl from width."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(
            self.image.get_file_url(url_width=100, url_param='1000px'),
            'https://upload.wikimedia.org/wikipedia/commons/thumb/'
            'd/d3/Albert_Einstein_Head.jpg/100px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 100)
        self.assertEqual(self.image.latest_file_info.thumbheight, 133)

    def test_get_file_url_thumburl_from_heigth(self):
        """Get File thumburl from height."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(
            self.image.get_file_url(url_height=100, url_param='1000px'),
            'https://upload.wikimedia.org/wikipedia/commons/thumb/'
            'd/d3/Albert_Einstein_Head.jpg/75px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 75)
        self.assertEqual(self.image.latest_file_info.thumbheight, 100)

    def test_get_file_url_thumburl_from_url_param(self):
        """Get File thumburl from height."""
        self.assertTrue(self.image.exists())
        # url_param has no precedence over height/width.
        self.assertEqual(
            self.image.get_file_url(url_param='100px'),
            'https://upload.wikimedia.org/wikipedia/commons/thumb/'
            'd/d3/Albert_Einstein_Head.jpg/100px-Albert_Einstein_Head.jpg')
        self.assertEqual(self.image.latest_file_info.thumbwidth, 100)
        self.assertEqual(self.image.latest_file_info.thumbheight, 133)


class TestFilePageDownload(TestCase):

    """Test download of FilePage to local file."""

    family = 'commons'
    code = 'commons'

    cached = True

    def test_successful_download(self):
        """Test successful_download."""
        page = pywikibot.FilePage(self.site, 'File:Albert Einstein.jpg')
        filename = join_images_path('Albert Einstein.jpg')
        status_code = page.download(filename)
        self.assertTrue(status_code)
        os.unlink(filename)

    def test_not_existing_download(self):
        """Test not existing download."""
        page = pywikibot.FilePage(self.site,
                                  'File:Albert Einstein.jpg_notexisting')
        filename = join_images_path('Albert Einstein.jpg')

        with self.assertRaisesRegex(
                pywikibot.NoPage,
                re.escape('Page [[commons:File:Albert Einstein.jpg '
                          "notexisting]] doesn't exist.")):
            page.download(filename)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
