#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test pagegenerators module."""
#
# (C) Pywikibot team, 2009-2020
#
# Distributed under the terms of the MIT license.
import calendar
import datetime
import logging
import sys

from contextlib import suppress
from typing import Optional

import pywikibot
from pywikibot import pagegenerators, date

from pywikibot.exceptions import ServerError, UnknownExtension

from pywikibot.pagegenerators import (
    PagesFromTitlesGenerator,
    PreloadingGenerator,
    CategorizedPageGenerator,
    WikibaseItemFilterPageGenerator,
)

from pywikibot.tools import has_module, suppress_warnings

from tests import join_data_path, mock
from tests.aspects import (
    unittest,
    TestCase,
    DeprecationTestCase,
    WikidataTestCase,
    DefaultSiteTestCase,
    RecentChangesTestCase,
)
from tests.thread_tests import GeneratorIntersectTestCase


en_wp_page_titles = (
    # just a bunch of randomly selected titles for English Wikipedia tests
    'Eastern Sayan',
    'The Addams Family (pinball)',
    'Talk:Nowy Sącz',
    'Talk:Battle of Węgierska Górka',
    'Template:!',
    'Template:Template',
)

en_wp_nopage_titles = (
    'Cities in Burkina Faso',
    'Talk:Hispanic (U.S. Census)',
    'Talk:Stołpce',
    'Template:!/Doc',
    'Template:!/Meta',
    'Template:Template/Doc',
    'Template:Template/Meta',
)


class TestDryPageGenerators(TestCase):

    """Test pagegenerators methods."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    titles = en_wp_page_titles + en_wp_nopage_titles

    def setUp(self):
        """Setup test."""
        super().setUp()
        self.site = self.get_site()

    def assertFunction(self, obj):
        """Assert function test."""
        self.assertTrue(hasattr(pagegenerators, obj))
        self.assertTrue(hasattr(getattr(pagegenerators, obj), '__call__'))

    def test_module_import(self):
        """Test module import."""
        self.assertIn('pywikibot.pagegenerators', sys.modules)

    def test_PagesFromTitlesGenerator(self):
        """Test PagesFromTitlesGenerator."""
        self.assertFunction('PagesFromTitlesGenerator')
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        self.assertPageTitlesEqual(gen, self.titles)

    def test_NamespaceFilterPageGenerator(self):
        """Test NamespaceFilterPageGenerator."""
        self.assertFunction('NamespaceFilterPageGenerator')
        site = self.site
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 0, site)
        self.assertLength(tuple(gen), 3)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 1, site)
        self.assertLength(tuple(gen), 4)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 10, site)
        self.assertLength(tuple(gen), 6)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, (1, 10), site)
        self.assertLength(tuple(gen), 10)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        gen = pagegenerators.NamespaceFilterPageGenerator(
            gen, ('Talk', 'Template'), site)
        self.assertLength(tuple(gen), 10)

    def test_RegexFilterPageGenerator(self):
        """Test RegexFilterPageGenerator."""
        self.assertFunction('RegexFilterPageGenerator')
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, '/doc')
        self.assertPageTitlesEqual(gen,
                                   ('Template:!/Doc', 'Template:Template/Doc'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, '/doc',
                                                      quantifier='none')
        self.assertLength(tuple(gen), 11)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'])
        self.assertPageTitlesEqual(gen,
                                   ('Template:!/Doc',
                                    'Template:!/Meta',
                                    'Template:Template/Doc',
                                    'Template:Template/Meta'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'],
                                                      quantifier='none')
        self.assertLength(tuple(gen), 9)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'],
                                                      quantifier='all')
        self.assertPageTitlesEqual(gen, [])
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(
            gen, ['Template', '/meta'], quantifier='all')
        self.assertPageTitlesEqual(gen, ('Template:Template/Meta', ))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(
            gen, ['template', '/meta'], quantifier='any')
        self.assertPageTitlesEqual(gen,
                                   ('Template:Template',
                                    'Template:!/Meta',
                                    'Template:Template/Doc',
                                    'Template:Template/Meta'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                      site=self.site)
        gen = pagegenerators.RegexFilterPageGenerator(
            gen, ['template', '/meta'], quantifier='any',
            ignore_namespace=False)
        self.assertLength(tuple(gen), 6)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                      site=self.site)
        gen = pagegenerators.RegexFilterPageGenerator(
            gen, ['template', '/meta'], quantifier='all',
            ignore_namespace=False)
        self.assertPageTitlesEqual(gen,
                                   ('Template:!/Meta',
                                    'Template:Template/Meta'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                      site=self.site)
        gen = pagegenerators.RegexFilterPageGenerator(
            gen, ['template', '/meta'], quantifier='none',
            ignore_namespace=False)
        self.assertLength(tuple(gen), 7)

    def test_RegexBodyFilterPageGenerator(self):
        """Test RegexBodyFilterPageGenerator."""
        self.assertFunction('RegexBodyFilterPageGenerator')
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                      site=self.site)
        pages = []
        for p in gen:
            p.text = 'This is the content of {} as a sample'.format(p.title())
            pages.append(p)
        gen = pagegenerators.RegexBodyFilterPageGenerator(iter(pages), '/doc')
        self.assertPageTitlesEqual(gen,
                                   ('Template:!/Doc', 'Template:Template/Doc'))
        gen = pagegenerators.RegexBodyFilterPageGenerator(iter(pages), 'This')
        self.assertPageTitlesEqual(gen, self.titles)
        gen = pagegenerators.RegexBodyFilterPageGenerator(iter(pages), 'talk',
                                                          quantifier='none')
        self.assertLength(tuple(gen), 9)


class BasetitleTestCase(TestCase):

    """Class providing base_title attribute."""

    family = 'wikisource'
    code = 'en'

    base_title = ('Page:06-24-1920 -The Story of the Jones County '
                  'Calf Case.pdf/{}')

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.site = self.get_site()
        self.titles = [self.base_title.format(i) for i in range(1, 11)]


class TestPagesFromPageidGenerator(BasetitleTestCase):

    """Test PagesFromPageidGenerator method."""

    def test_PagesFromPageidGenerator(self):
        """Test PagesFromPageidGenerator."""
        gen_pages = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                            self.site)
        pageids = [page.pageid for page in gen_pages]
        gen = pagegenerators.PagesFromPageidGenerator(pageids, self.site)
        self.assertPageTitlesEqual(gen, self.titles)


class TestCategoryFilterPageGenerator(BasetitleTestCase):

    """Test CategoryFilterPageGenerator method."""

    category_list = ['Category:Validated']

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.catfilter_list = [pywikibot.Category(self.site, cat)
                               for cat in self.category_list]

    def test_CategoryFilterPageGenerator(self):
        """Test CategoryFilterPageGenerator."""
        site = self.site
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        gen = pagegenerators.CategoryFilterPageGenerator(
            gen, self.catfilter_list)
        self.assertLength(tuple(gen), 10)


class TestQualityFilterPageGenerator(BasetitleTestCase):

    """Test QualityFilterPageGenerator methods."""

    cached = True

    base_title = 'Page:Popular Science Monthly Volume 1.djvu/{}'

    def test_QualityFilterPageGenerator(self):
        """Test QualityFilterPageGenerator."""
        site = self.site
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        gen = pagegenerators.QualityFilterPageGenerator(gen, [0])
        self.assertLength(tuple(gen), 7)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        gen = pagegenerators.QualityFilterPageGenerator(gen, [4])
        self.assertLength(tuple(gen), 3)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, site)
        self.assertLength(tuple(gen), 10)


class EdittimeFilterPageGeneratorTestCase(TestCase):

    """Test EdittimeFilterPageGenerator."""

    family = 'wikipedia'
    code = 'en'

    titles = en_wp_page_titles

    def test_first_edit(self):
        """Test first edit."""
        expect = (
            'The Addams Family (pinball)',
            'Talk:Nowy Sącz',
            'Template:Template',
        )
        gen = PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, first_edit_end=datetime.datetime(2006, 1, 1))
        self.assertPageTitlesEqual(gen, titles=expect, site=self.site)

        gen = PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, first_edit_start=datetime.datetime(2006, 1, 1))
        opposite_pages = list(gen)
        self.assertTrue(all(isinstance(p, pywikibot.Page)
                            for p in opposite_pages))
        self.assertTrue(all(p.title not in expect for p in opposite_pages))

    def test_last_edit(self):
        """Test last edit."""
        two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
        nine_days_ago = datetime.datetime.now() - datetime.timedelta(days=9)

        gen = PagesFromTitlesGenerator(['Wikipedia:Sandbox'], self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, last_edit_start=two_days_ago)
        self.assertLength(list(gen), 1)

        gen = PagesFromTitlesGenerator(['Wikipedia:Sandbox'], self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, last_edit_end=two_days_ago)
        self.assertIsEmpty(list(gen))

        gen = PagesFromTitlesGenerator(['Template:Side box'], self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, last_edit_end=nine_days_ago)
        self.assertLength(list(gen), 1)

        gen = PagesFromTitlesGenerator(['Template:Side box'], self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, last_edit_start=nine_days_ago)
        self.assertIsEmpty(list(gen))


class RedirectFilterPageGeneratorTestCase(TestCase):

    """Test RedirectFilterPageGenerator."""

    family = 'wikipedia'
    code = 'en'

    def test_redirect_filter(self):
        """Test RedirectFilterPageGenerator."""
        from pywikibot.pagegenerators import RedirectFilterPageGenerator
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-randomredirect:3')
        gf.handleArg('-page:Main_Page')
        gen = gf.getCombinedGenerator()
        pages = list(gen)
        gen = RedirectFilterPageGenerator(pages, no_redirects=True)
        self.assertLength(list(gen), 1)
        gen = RedirectFilterPageGenerator(pages, no_redirects=False)
        self.assertLength(list(gen), 3)


class SubpageFilterGeneratorTestCase(TestCase):

    """Test SubpageFilterGenerator."""

    family = 'wikipedia'
    code = 'test'

    def test_subpage_filter(self):
        """Test SubpageFilterGenerator."""
        site = self.get_site()
        test_cat = pywikibot.Category(site, 'Subpage testing')

        gen = CategorizedPageGenerator(test_cat)
        gen = pagegenerators.SubpageFilterGenerator(gen, 0)
        expect_0 = ('/home/test',)
        self.assertPageTitlesEqual(gen, titles=expect_0, site=site)

        gen = CategorizedPageGenerator(test_cat)
        gen = pagegenerators.SubpageFilterGenerator(gen, 3)
        expect_3 = (
            '/home/test',
            'User:Sn1per/ProtectTest1/test',
            'User:Sn1per/ProtectTest1/test/test',
        )
        self.assertPageTitlesEqual(gen, titles=expect_3, site=site)


class PetScanPageGeneratorTestCase(TestCase):

    """Test PetScanPageGenerator."""

    family = 'wikipedia'
    code = 'test'

    def test_petscan(self):
        """Test PetScanPageGenerator."""
        site = self.get_site()
        gen = pagegenerators.PetScanPageGenerator(['Pywikibot Protect Test'],
                                                  True, None, site)
        try:
            self.assertPageTitlesEqual(gen, titles=(
                'User:Sn1per/ProtectTest1', 'User:Sn1per/ProtectTest2'),
                site=site)
        except ServerError as e:
            self.skipTest(e)

        gen = pagegenerators.PetScanPageGenerator(['Pywikibot Protect Test'],
                                                  False, None, site)
        self.assertPageTitlesEqual(gen, titles=('User:Sn1per/ProtectTest1',
                                                'User:Sn1per/ProtectTest2'),
                                   site=site)

        gen = pagegenerators.PetScanPageGenerator(
            ['Pywikibot PetScan Test',
             'Pywikibot Category That Needs&ToBe!Encoded',
             'Test'], True, None, site)
        self.assertPageTitlesEqual(gen, titles=('User:Sn1per/PetScanTest1', ),
                                   site=site)


class TestRepeatingGenerator(RecentChangesTestCase):

    """Test RepeatingGenerator."""

    def test_RepeatingGenerator(self):
        """Test RepeatingGenerator."""
        with suppress_warnings(category=DeprecationWarning):
            gen = pagegenerators.RepeatingGenerator(
                self.site.recentchanges,
                key_func=lambda x: x['revid'],
                sleep_duration=10,
                reverse=True,
                namespaces=[0],
                total=self.length)
        items = list(gen)
        self.assertLength(items, self.length)
        timestamps = [pywikibot.Timestamp.fromISOformat(item['timestamp'])
                      for item in items]
        self.assertEqual(sorted(timestamps), timestamps)
        self.assertTrue(all(item['ns'] == 0 for item in items))
        self.assertLength({item['revid'] for item in items}, self.length)


class TestTextfilePageGenerator(DefaultSiteTestCase):

    """Test loading pages from a textfile."""

    dry = True

    title_columns = {
        'case-sensitive': 0,
        'first-letter': 1,
    }

    expected_titles = (
        ('file', 'File'),
        ('bracket', 'Bracket'),
        ('MediaWiki:Test', 'MediaWiki:Test'),
        ('under score', 'Under score'),
        ('Upper case', 'Upper case'),
    )

    def test_brackets(self):
        """Test TextfilePageGenerator with brackets."""
        filename = join_data_path('pagelist-brackets.txt')
        site = self.get_site()
        titles = list(pagegenerators.TextfilePageGenerator(filename, site))
        self.assertLength(titles, self.expected_titles)
        expected_titles = [
            expected_title[self.title_columns[site.namespaces[page.namespace()]
                                              .case]]
            for expected_title, page in zip(self.expected_titles, titles)]
        self.assertPageTitlesEqual(titles, expected_titles)

    def test_lines(self):
        """Test TextfilePageGenerator with newlines."""
        filename = join_data_path('pagelist-lines.txt')
        site = self.get_site()
        titles = list(pagegenerators.TextfilePageGenerator(filename, site))
        self.assertLength(titles, self.expected_titles)
        expected_titles = [
            expected_title[self.title_columns[site.namespaces[page.namespace()]
                                              .case]]
            for expected_title, page in zip(self.expected_titles, titles)]
        self.assertPageTitlesEqual(titles, expected_titles)


class TestYearPageGenerator(DefaultSiteTestCase):

    """Test the year page generator."""

    def test_basic(self):
        """Test YearPageGenerator."""
        site = self.get_site()
        # Some languages are missing (T85681)
        if (site.lang not in date.formats['YearBC']
                or site.lang not in date.formats['YearAD']):
            self.skipTest(
                'Date formats for this language are missing from date.py')
        start = -20
        end = 2026

        i = 0
        for page in pagegenerators.YearPageGenerator(start, end, site):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(date.formatYear(site.lang, start + i),
                             page.title())
            self.assertNotEqual(page.title(), '0')
            i += 1
            if start + i == 0:
                i += 1
        self.assertEqual(start + i - 1, end)


class TestDayPageGenerator(DefaultSiteTestCase):

    """Test the day page generator."""

    def _run_test(self, start_month=1, end_month=12, year=2000):
        """Test method for DayPageGenerator."""
        params = {
            'start_month': start_month,
            'end_month': end_month,
            'site': self.site,
        }
        if year != 2000:
            params['year'] = year
        # use positional parameter
        gen1 = pagegenerators.DayPageGenerator(
            start_month, end_month, self.site, year)
        # use keyworded parameter and default for year
        gen2 = pagegenerators.DayPageGenerator(**params)

        for page in gen1:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.isAutoTitle)

        expected = []
        for month in range(start_month, end_month + 1):
            for day in range(1, calendar.monthrange(year, month)[1] + 1):
                expected.append(date.format_date(month, day, self.site))

        self.assertPageTitlesEqual(gen2, expected)

    def test_basic(self):
        """General test for day page generator."""
        self._run_test()

    def test_year_2001(self):
        """Test for day page generator of year 2001."""
        self._run_test(2, year=2001)

    def test_year_2100(self):
        """Test for day page generator of year 2100."""
        self._run_test(end_month=2, year=2100)

    def test_start_0(self):
        """Test for day page generator with startMonth 0."""
        self.assertRaises(calendar.IllegalMonthError, self._run_test, 0)

    def test_end_13(self):
        """Test for day page generator with endMonth 13."""
        self.assertRaises(calendar.IllegalMonthError, self._run_test, 12, 13)


class TestPreloadingGenerator(DefaultSiteTestCase):

    """Test preloading generator on lists."""

    def test_basic(self):
        """Test PreloadingGenerator with a list of pages."""
        mainpage = self.get_mainpage()
        links = [page for page in self.site.pagelinks(mainpage, total=20)
                 if page.exists()]
        count = 0
        for page in PreloadingGenerator(links, groupsize=20):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertLength(page._revisions, 1)
            self.assertIsNotNone(page._revisions[page._revid].text)
            self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
        self.assertLength(links, count)

    def test_low_step(self):
        """Test PreloadingGenerator with a list of pages."""
        mainpage = self.get_mainpage()
        links = [page for page in self.site.pagelinks(mainpage, total=20)
                 if page.exists()]
        count = 0
        for page in PreloadingGenerator(links, groupsize=10):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertLength(page._revisions, 1)
            self.assertIsNotNone(page._revisions[page._revid].text)
            self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
        self.assertLength(links, count)

    def test_order(self):
        """Test outcome is following same order of input."""
        mainpage = self.get_mainpage()
        links = [page for page in self.site.pagelinks(mainpage, total=20)
                 if page.exists()]
        count = 0
        for page in PreloadingGenerator(links, groupsize=10):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertLength(page._revisions, 1)
            self.assertIsNotNone(page._revisions[page._revid].text)
            self.assertFalse(hasattr(page, '_pageprops'))
            self.assertEqual(page, links[count])
            count += 1
        self.assertLength(links, count)


class TestDequePreloadingGenerator(DefaultSiteTestCase):

    """Test preloading generator on lists."""

    def test_deque_preloading(self):
        """Test pages being added to a DequePreloadingGenerator."""
        mainpage = self.get_mainpage()

        pages = pywikibot.tools.DequeGenerator([mainpage])
        gen = pagegenerators.DequePreloadingGenerator(pages)
        pages_out = []
        for page in gen:
            pages_out.append(page)
            # Add a page to the generator
            if not page.isTalkPage():
                pages.extend([page.toggleTalkPage()])

        self.assertTrue(all(isinstance(page,
                                       pywikibot.Page) for page in pages_out))
        self.assertIn(mainpage, pages_out)
        self.assertIn(mainpage.toggleTalkPage(), pages_out)
        self.assertLength(pages_out, 2)
        self.assertTrue(pages_out[1].isTalkPage())


class TestPreloadingEntityGenerator(WikidataTestCase):

    """Test preloading item generator."""

    def test_non_item_gen(self):
        """Test TestPreloadingEntityGenerator with ReferringPageGenerator."""
        site = self.get_site()
        instance_of_page = pywikibot.Page(site, 'Property:P31')
        ref_gen = pagegenerators.ReferringPageGenerator(instance_of_page,
                                                        total=5)
        gen = pagegenerators.PreloadingEntityGenerator(ref_gen)
        self.assertTrue(all(isinstance(item,
                                       pywikibot.ItemPage) for item in gen))


class WikibaseItemFilterPageGeneratorTestCase(TestCase):

    """Test WikibaseItemFilterPageGenerator."""

    family = 'wikipedia'
    code = 'en'

    def test_filter_pages_with_item(self):
        """Test WikibaseItemFilterPageGenerator on pages with item."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-page:Main_Page')
        gen = gf.getCombinedGenerator()
        pages = list(gen)
        gen = WikibaseItemFilterPageGenerator(pages, has_item=True)
        self.assertLength(list(gen), 1)
        gen = WikibaseItemFilterPageGenerator(pages, has_item=False)
        self.assertLength(list(gen), 0)

    def test_filter_pages_without_item(self):
        """Test WikibaseItemFilterPageGenerator on pages without item."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-page:Talk:Main_Page')
        gen = gf.getCombinedGenerator()
        pages = list(gen)
        gen = WikibaseItemFilterPageGenerator(pages, has_item=True)
        self.assertLength(list(gen), 0)
        gen = WikibaseItemFilterPageGenerator(pages, has_item=False)
        self.assertLength(list(gen), 1)


class DryFactoryGeneratorTest(TestCase):

    """Dry tests for pagegenerators.GeneratorFactory."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_one_namespace(self):
        """Test one namespace."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:2')
        self.assertEqual(gf.namespaces, {2})

    def test_two_namespaces(self):
        """Test two namespaces."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:2')
        gf.handleArg('-ns:Talk')
        self.assertEqual(gf.namespaces, {2, 1})

    def test_two_named_namespaces(self):
        """Test two named namespaces."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:Talk,File')
        self.assertEqual(gf.namespaces, {1, 6})

    def test_two_numeric_namespaces(self):
        """Test two namespaces delimited by colon."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:1,6')
        self.assertEqual(gf.namespaces, {1, 6})

    def test_immutable_namespaces_on_read(self):
        """Test immutable namespaces on read."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:1,6')
        self.assertEqual(gf.namespaces, {1, 6})
        self.assertIsInstance(gf.namespaces, frozenset)
        with self.assertRaises(AssertionError):
            gf.handleArg('-ns:0')
        self.assertEqual(gf.namespaces, {1, 6})

    def test_unsupported_quality_level_filter(self):
        """Test unsupported option."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        self.assertRaises(UnknownExtension, gf.handleArg, '-ql:2')

    def test_one_excluded_namespaces(self):
        """Test one excluded namespaces."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:not:2')
        ns = set(range(16))
        ns.remove(2)
        self.assertTrue(ns.issubset(gf.namespaces))

    def test_two_excluded_namespaces(self):
        """Test two excluded namespaces."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:not:2')
        gf.handleArg('-ns:not:Talk')
        ns = set(range(16))
        ns.remove(2)
        ns.remove(1)
        self.assertTrue(ns.issubset(gf.namespaces))

    def test_two_excluded_named_namespaces(self):
        """Test two excluded named namespaces."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:not:Talk,File')
        ns = set(range(16))
        ns.remove(1)
        ns.remove(6)
        self.assertTrue(ns.issubset(gf.namespaces))

    def test_two_excluded_numeric_namespaces(self):
        """Test two excluded namespaces delimited by colon."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:not:1,6')
        ns = set(range(16))
        ns.remove(1)
        ns.remove(6)
        self.assertTrue(ns.issubset(gf.namespaces))

    def test_mixed_namespaces_with_exclusion(self):
        """Test mixed namespaces with exclusion."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:not:2,File')
        gf.handleArg('-ns:not:3,4,5')
        gf.handleArg('-ns:6,7')
        ns = set(range(16))
        for i in range(2, 6):
            ns.remove(i)
        self.assertTrue(ns.issubset(gf.namespaces))

    def test_given_namespaces_with_exclusion(self):
        """Test mixed namespaces with exclusion."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-ns:1,2,3,4,5')
        gf.handleArg('-ns:not:User')
        self.assertEqual(gf.namespaces, {1, 3, 4, 5})

    def test_invalid_arg(self):
        """Test invalid / non-generator arguments."""
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        self.assertFalse(gf.handleArg('-foobar'))
        self.assertFalse(gf.handleArg('barbaz'))
        self.assertFalse(gf.handleArg('-ì'))
        self.assertFalse(gf.handleArg('ì'))


class TestItemClaimFilterPageGenerator(WikidataTestCase):

    """Test item claim filter page generator generator."""

    def _simple_claim_test(self, prop: str, claim, qualifiers: Optional[dict],
                           valid: bool, negate: bool = False):
        """
        Test given claim on sample (India) page.

        @param prop: the property to check
        @param claim: the claim the property should contain
        @param qualifiers: qualifiers to check or None
        @param valid: true if the page should be yielded by the generator,
            false otherwise
        @param negate: true to swap the filters' behavior
        """
        item = pywikibot.ItemPage(self.get_repo(), 'Q668')
        gen = pagegenerators.ItemClaimFilterPageGenerator([item], prop, claim,
                                                          qualifiers, negate)
        pages = set(gen)
        if valid:
            self.assertLength(pages, 1)
        else:
            self.assertIsEmpty(pages)

    def _get_council_page(self):
        """Return United Nations Security Council Wikidata page."""
        site = self.get_site()
        return pywikibot.Page(site, 'Q37470')

    def test_valid_qualifiers(self):
        """Test ItemClaimFilterPageGenerator using valid qualifiers."""
        qualifiers = {
            'P580': pywikibot.WbTime(1950, 1, 1, precision=9,
                                     site=self.get_site()),
            'P582': '1951',
        }
        self._simple_claim_test('P463', self._get_council_page(), qualifiers,
                                True)

    def test_invalid_qualifiers(self):
        """Test ItemClaimFilterPageGenerator with invalid qualifiers."""
        qualifiers = {
            'P580': 1950,
            'P582': pywikibot.WbTime(1960, 1, 1, precision=9,
                                     site=self.site),
        }
        self._simple_claim_test('P463', self._get_council_page(), qualifiers,
                                False)

    def test_nonexisting_qualifiers(self):
        """
        Test ItemClaimFilterPageGenerator on sample page.

        The item does not have the searched qualifiers.
        """
        qualifiers = {
            'P370': pywikibot.WbTime(1950, 1, 1, precision=9,
                                     site=self.get_site()),
            'P232': pywikibot.WbTime(1960, 1, 1, precision=9,
                                     site=self.get_site()),
        }
        self._simple_claim_test('P463', self._get_council_page(), qualifiers,
                                False)

    def test_no_qualifiers(self):
        """Test ItemClaimFilterPageGenerator without qualifiers."""
        self._simple_claim_test('P474', '+91', None, True)
        self._simple_claim_test('P463', 'Q37470', None, True)
        self._simple_claim_test('P1334', '28,97.4,0.1', None, True)
        self._simple_claim_test('P1334', '28,96,0.01', None, False)

    def test_negative_filter(self):
        """Test negative ItemClaimFilterPageGenerator."""
        self._simple_claim_test('P463', 'Q37470', None, False, True)
        self._simple_claim_test('P463', 'Q37471', None, True, True)

    def test_item_from_page(self):
        """Test ItemPage can be obtained form Page."""
        site = pywikibot.Site('en', 'wikipedia')
        page = pywikibot.Page(site, 'India')
        gen = pagegenerators.ItemClaimFilterPageGenerator(
            [page], 'P463', self._get_council_page())
        pages = set(gen)
        self.assertEqual(pages.pop(), page)


class TestFactoryGenerator(DefaultSiteTestCase):

    """Test pagegenerators.GeneratorFactory."""

    def test_combined_generator(self):
        """Test getCombinedGenerator with generator parameter."""
        gf = pagegenerators.GeneratorFactory()
        gen = gf.getCombinedGenerator(gen='ABC')
        self.assertEqual(tuple(gen), ('A', 'B', 'C'))

    def test_intersect_generator(self):
        """Test getCombinedGenerator with generator parameter."""
        gf = pagegenerators.GeneratorFactory()
        gf.handleArg('-intersect')
        gf.gens = ['Python 3.7-dev']
        gen = gf.getCombinedGenerator(gen='Pywikibot 3.0.dev')
        self.assertEqual(''.join(gen), 'Pyot 3.dev')

    def test_ns(self):
        """Test namespace option."""
        gf = pagegenerators.GeneratorFactory()
        gf.handleArg('-ns:1')
        gen = gf.getCombinedGenerator()
        self.assertIsNone(gen)

    def test_allpages_default(self):
        """Test allpages generator."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-start:!'))
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertLessEqual(len(pages), 10)
        for page in pages:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)

    def test_allpages_ns(self):
        """Test allpages generator with namespace argument."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-start:!'))
        gf.handleArg('-limit:10')
        gf.handleArg('-ns:1')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertLessEqual(len(pages), 10)
        self.assertPagesInNamespaces(gen, 1)

    def test_regexfilter_default(self):
        """Test allpages generator with titleregex filter."""
        gf = pagegenerators.GeneratorFactory()
        # Matches titles with the same two or more continuous characters
        self.assertTrue(gf.handleArg('-start'))
        self.assertTrue(gf.handleArg('-titleregex:(.)\\1+'))
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = list(gen)
        self.assertLessEqual(len(pages), 10)
        for page in pages:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertRegex(page.title().lower(), '(.)\\1+')

    def test_regexfilter_ns_after(self):
        """Test allpages generator with titleregex and namespace filter."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-start'))
        self.assertTrue(gf.handleArg('-titleregex:.*'))
        gf.handleArg('-ns:1')
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        pages = list(gen)
        self.assertLessEqual(len(pages), 10)
        self.assertPagesInNamespaces(pages, 1)

    def test_regexfilter_ns_before(self):
        """Test allpages generator with namespace and titleregex filter."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-start'))
        gf.handleArg('-ns:1')
        self.assertTrue(gf.handleArg('-titleregex:.*'))
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = list(gen)
        self.assertLessEqual(len(pages), 10)
        self.assertPagesInNamespaces(pages, 1)

    def test_regexfilternot_default(self):
        """Test allpages generator with titleregexnot filter."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-start'))
        # matches titles with less than 11 characters
        self.assertTrue(gf.handleArg('-titleregexnot:.{11,}'))
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = list(gen)
        self.assertLessEqual(len(pages), 10)
        for page in pages:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertNotRegex(page.title().lower(), '.{11,}')

    def test_regexfilternot_ns_after(self):
        """Test allpages generator with titleregexnot and namespace filter."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-start'))
        self.assertTrue(gf.handleArg('-titleregexnot:zzzz'))
        gf.handleArg('-ns:1')
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        pages = list(gen)
        self.assertLessEqual(len(pages), 10)
        self.assertPagesInNamespaces(pages, 1)

    def test_regexfilternot_ns_before(self):
        """Test allpages generator with namespace and titleregexnot filter."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-start'))
        gf.handleArg('-ns:1')
        self.assertTrue(gf.handleArg('-titleregexnot:zzzz'))
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = list(gen)
        self.assertLessEqual(len(pages), 10)
        self.assertPagesInNamespaces(pages, 1)

    def test_allpages_with_two_ns(self):
        """Test that allpages fails with two ns as parameter."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-start'))
        gf.handleArg('-ns:3,1')
        # allpages only accepts a single namespace, and will raise a
        # TypeError if self.namespaces contains more than one namespace.
        self.assertRaises(
            TypeError,
            'allpages module does not support multiple namespaces',
            gf.getCombinedGenerator)

    def test_prefixing_default(self):
        """Test prefixindex generator."""
        gf = pagegenerators.GeneratorFactory()
        self.assertTrue(gf.handleArg('-prefixindex:a'))
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertLessEqual(len(pages), 10)
        for page in pages:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.title().lower().startswith('a'))

    def test_prefixing_ns(self):
        """Test prefixindex generator with namespace filter."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-prefixindex:a')
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, 1)

    def test_recentchanges_timespan(self):
        """Test recentchanges generator with offset and duration params."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-recentchanges:120,70')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertRaises(ValueError, gf.handleArg, '-recentchanges:3,2,1')
        self.assertRaises(ValueError, gf.handleArg, '-recentchanges:12,-12')
        self.assertRaises(
            ValueError, gf.handleArg, '-recentchanges:visualeditor,3,2,1')
        self.assertRaises(
            ValueError, gf.handleArg, '-recentchanges:"mobile edit,-10,20"')

    def test_recentchanges_rctag(self):
        """Test recentchanges generator with recent changes tag."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-recentchanges:visualeditor')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespacesAll(gen, {0, 1, 2}, skip=True)

    def test_recentchanges_default(self):
        """Test recentchanges generator with default namespace setting."""
        if self.site.family.name in ('wpbeta', 'wsbeta'):
            self.skipTest('Skipping {} due to too many autoblocked users'
                          .format(self.site))
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-recentchanges:50')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespacesAll(gen, {0, 1, 2}, skip=True)

    def test_recentchanges_ns(self):
        """Test recentchanges generator with namespace."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-recentchanges:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, 1)

    def test_recentchanges_ns_multi(self):
        """Test recentchanges generator with multiple namespaces."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-ns:3')
        gf.handleArg('-recentchanges:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, {1, 3})

    def test_pageid(self):
        """Test pageid parameter."""
        # Get reference pages and their pageids.
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        self.assertTrue(gf.handleArg('-random'))
        gf.handleArg('-limit:10')
        gen = gf.getCombinedGenerator()
        pages = list(gen)
        self.assertLength(pages, 10)
        # pipe-separated used as test reference.
        pageids = '|'.join(str(page.pageid) for page in pages)

        # Get by pageids.
        gf = pagegenerators.GeneratorFactory(site=self.get_site())
        gf.handleArg('-pageid:{}'.format(pageids))
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages_from_pageid = list(gen)
        self.assertLength(pages_from_pageid, 10)
        for page_a, page_b in zip(pages, pages_from_pageid):
            self.assertIsInstance(page_a, pywikibot.Page)
            self.assertIsInstance(page_b, pywikibot.Page)
            self.assertTrue(page_a, page_b)

    def test_pagegenerator(self):
        """Test page generator."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-page:Main Page')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)

    def test_random_generator_default(self):
        """Test random generator."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-random:1')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertLength(pages, 1)

    def test_random_generator_ns(self):
        """Test random generator with namespace."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-random:1')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, 1)

    def test_random_generator_ns_multi(self):
        """Test random generator with multiple namespaces."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-ns:3')
        gf.handleArg('-random:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, {1, 3})

    def test_randomredirect_generator_default(self):
        """Test random generator."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-randomredirect:1')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertLength(pages, 1)

    def test_randomredirect_generator_ns(self):
        """Test random generator with namespace."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-randomredirect:1')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, 1)

    def test_randomredirect_generator_ns_multi(self):
        """Test random generator with multiple namespaces."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-ns:3')
        gf.handleArg('-randomredirect:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, {1, 3})

    def test_pages_with_property_generator(self):
        """Test the pages_with_property_generator method."""
        mysite = self.get_site()
        if mysite.mw_version < '1.21':
            self.skipTest('requires v1.21+')
        for item in ('defaultsort', 'disambiguation', 'displaytitle',
                     'hiddencat', 'invalid_property'):
            if item in mysite.get_property_names():
                gf = pagegenerators.GeneratorFactory()
                gf.handleArg('-property:{0}'.format(item))
                gf.handleArg('-limit:10')
                gen = gf.getCombinedGenerator()
                self.assertIsNotNone(gen)
                pages = list(gen)
                self.assertLessEqual(len(pages), 10)
                for page in pages:
                    self.assertIsInstance(page, pywikibot.Page)
                    if item == 'disambiguation':
                        self.assertTrue(page.isDisambig())
            else:
                with self.assertRaises(NotImplementedError):
                    mysite.pages_with_property(item)
                    self.fail(
                        'NotImplementedError not raised for {0}'.format(item))

    def test_empty_generator(self):
        """Test empty generator."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gen = gf.getCombinedGenerator()
        self.assertIsNone(gen)

    def test_positionalargument(self):
        """Test page generator with positional argument."""
        gf1 = pagegenerators.GeneratorFactory(site=self.site,
                                              positional_arg_name='page')
        gf1.handleArg('Main Page')
        gen1 = gf1.getCombinedGenerator()
        self.assertIsNotNone(gen1)
        gf2 = pagegenerators.GeneratorFactory(site=self.site)
        gf2.handleArg('-page:Main Page')
        gen2 = gf2.getCombinedGenerator()
        self.assertIsNotNone(gen2)
        self.assertEqual(list(gen1), list(gen2))

    def test_positionalargument_with_colon(self):
        """Test page generator with positional argument with colon."""
        gf1 = pagegenerators.GeneratorFactory(site=self.site,
                                              positional_arg_name='page')
        gf1.handleArg('Project:Main Page')
        gen1 = gf1.getCombinedGenerator()
        self.assertIsNotNone(gen1)
        gf2 = pagegenerators.GeneratorFactory(site=self.site)
        gf2.handleArg('-page:Project:Main Page')
        gen2 = gf2.getCombinedGenerator()
        self.assertIsNotNone(gen2)
        self.assertEqual(list(gen1), list(gen2))

    def test_linter_generator_ns_valid_cat(self):
        """Test generator of pages with lint errors."""
        if not self.site.has_extension('Linter'):
            self.skipTest('The site {0} does not use Linter extension'
                          .format(self.site))
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-limit:3')
        gf.handleArg('-linter:obsolete-tag')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = list(gen)
        self.assertLessEqual(len(pages), 5)
        for page in pages:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page._lintinfo['category'], 'obsolete-tag')
        self.assertPagesInNamespaces(pages, {1})

    def test_linter_generator_invalid_cat(self):
        """Test generator of pages with lint errors."""
        if not self.site.has_extension('Linter'):
            self.skipTest('The site {0} does not use Linter extension'
                          .format(self.site))
        gf = pagegenerators.GeneratorFactory(site=self.site)
        self.assertRaises(AssertionError, gf.handleArg, '-linter:dummy')

    def test_linter_generator_show(self):
        """Test generator of pages with lint errors."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        if self.site.has_extension('Linter'):
            with self.assertRaises(SystemExit) as cm:
                gf.handleArg('-linter:show')
            self.assertEqual(cm.exception.code, 0)
        else:
            self.assertRaises(UnknownExtension, gf.handleArg, '-linter:show')

    def test_querypage_generator_with_valid_page(self):
        """Test generator of pages with lint errors."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-querypage:Ancientpages')
        gf.handleArg('-limit:5')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = list(gen)
        self.assertLessEqual(len(pages), 5)
        for page in pages:
            self.assertIsInstance(page, pywikibot.Page)

    def test_querypage_generator_with_invalid_page(self):
        """Test generator of pages with lint errors."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        self.assertRaises(AssertionError, gf.handleArg, '-querypage:dummy')

    def test_querypage_generator_with_no_page(self):
        """Test generator of pages with lint errors."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        with self.assertRaises(SystemExit) as cm:
            gf.handleArg('-querypage')
        self.assertEqual(cm.exception.code, 0)


class TestFactoryGeneratorNewpages(TestCase):

    """Test pagegenerators.GeneratorFactory for newpages."""

    # Detached from TestFactoryGenerator due to T159029

    sites = {
        'eswiki': {
            'family': 'wikipedia',
            'code': 'es',
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
        },
        'ruwikt': {
            'family': 'wiktionary',
            'code': 'ru',
        },
        'meta': {
            'family': 'meta',
            'code': 'meta',
        },
        'frsource': {
            'family': 'wikisource',
            'code': 'fr',
        },
        'devoy': {
            'family': 'wikivoyage',
            'code': 'de',
        },
    }

    def test_newpages_default(self, key):
        """Test newpages generator."""
        site = self.get_site(key)
        gf = pagegenerators.GeneratorFactory(site=site)
        gf.handleArg('-newpages:60')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertLessEqual(len(pages), 60)

        newpages_url = self.site.base_url(
            self.site.path() + '?title=Special:NewPages&uselang=en')
        failure_message = 'No new pages returned by -newpages. ' \
            'If this is the only failure, check whether {url} contains any ' \
            'pages. If not, create a new page on the site to make the test ' \
            'pass again.'.format(url=newpages_url)

        self.assertIsNotEmpty(pages, msg=failure_message)

    def test_newpages_ns_default(self, key):
        """Test newpages generator with limit argument."""
        site = self.get_site(key)
        gf = pagegenerators.GeneratorFactory(site=site)
        gf.handleArg('-newpages:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, 0)

    def test_newpages_ns(self, key):
        """Test newpages generator with limit argument and namespace filter."""
        site = self.get_site(key)
        gf = pagegenerators.GeneratorFactory(site=site)
        gf.handleArg('-ns:1')
        gf.handleArg('-newpages:10')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertPagesInNamespaces(gen, 1)


class TestWantedFactoryGenerator(DefaultSiteTestCase):

    """Test pagegenerators.GeneratorFactory for wanted pages."""

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.gf = pagegenerators.GeneratorFactory(site=self.site)

    def _generator_with_tests(self):
        """Test generator."""
        gen = self.gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = list(gen)
        self.assertLessEqual(len(pages), 5)
        yield from pages

    def test_wanted_pages(self):
        """Test wantedpages generator."""
        self.gf.handleArg('-wantedpages:5')
        for page in self._generator_with_tests():
            self.assertIsInstance(page, pywikibot.Page)

    def test_wanted_files(self):
        """Test wantedfiles generator."""
        self.gf.handleArg('-wantedfiles:5')
        for page in self._generator_with_tests():
            self.assertIsInstance(page, pywikibot.FilePage)

    def test_wanted_templates(self):
        """Test wantedtemplates generator."""
        self.gf.handleArg('-wantedtemplates:5')
        for page in self._generator_with_tests():
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 10)

    def test_wanted_categories(self):
        """Test wantedcategories generator."""
        self.gf.handleArg('-wantedcategories:5')
        for page in self._generator_with_tests():
            self.assertIsInstance(page, pywikibot.Category)


class TestFactoryGeneratorWikibase(WikidataTestCase):

    """Test pagegenerators.GeneratorFactory on Wikibase site."""

    def test_onlyif(self):
        """Test -onlyif without qualifiers."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-page:Q15745378')
        self.assertTrue(gf.handleArg(
            '-onlyif:P1476=International Journal of Minerals\\, '
            'Metallurgy\\, and Materials'))
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertLength(set(gen), 1)

    def test_onlyifnot(self):
        """Test -onlyifnot without qualifiers."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-page:Q15745378')
        gf.handleArg('-onlyifnot:P1476=International Journal of Minerals\\, '
                     'Metallurgy\\, and Materials')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertIsEmpty(set(gen))

    def test_onlyif_qualifiers(self):
        """Test -onlyif with qualifiers."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-page:Q668')
        gf.handleArg('-onlyif:P47=Q837,P805=Q3088768')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertLength(set(gen), 1)

    def test_searchitem(self):
        """Test -searchitem."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-searchitem:abc')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        self.assertIsNotNone(next(gen))

    def test_searchitem_language(self):
        """Test -searchitem with custom language specified."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-searchitem:pl:abc')
        gf.handleArg('-limit:1')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        # alphabet, also known as ABC
        page1 = next(gen)
        self.assertEqual(page1.title(), 'Q9779')

        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-searchitem:en:abc')
        gf.handleArg('-limit:2')
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        # American Broadcasting Company
        page1 = next(gen)
        self.assertEqual(page1.title(), 'Q169889')
        # alphabet, also known as ABC
        page2 = next(gen)
        self.assertEqual(page2.title(), 'Q9779')

    def test_get_category_site(self):
        """Test the getCategory method."""
        # With default site
        gf = pagegenerators.GeneratorFactory()
        cat = gf.getCategory('foo')[0]
        self.assertEqual(cat.site, pywikibot.Site())
        # With a user-specified site
        fa_wikisource = pywikibot.Site('fa', 'wikisource')
        gf = pagegenerators.GeneratorFactory(fa_wikisource)
        cat = gf.getCategory('foo')[0]
        self.assertEqual(cat.site, fa_wikisource)


class TestLogeventsFactoryGenerator(DefaultSiteTestCase,
                                    DeprecationTestCase):

    """Test GeneratorFactory with pagegenerators.LogeventsPageGenerator."""

    @classmethod
    def setUpClass(cls):
        """Setup test class."""
        super().setUpClass()
        site = pywikibot.Site()
        newuser_logevents = list(site.logevents(logtype='newusers', total=1))
        if len(newuser_logevents) == 0:
            raise unittest.SkipTest('No newuser logs found to test with.')

    user = True

    def test_logevents_parse(self):
        """Test wrong logevents option."""
        factory = pagegenerators.GeneratorFactory
        gf = factory()
        self.assertFalse(gf.handleArg('-log'))
        self.assertFalse(gf.handleArg('-log:text_here'))
        self.assertRaises(NotImplementedError,
                          gf.handleArg, '-logevents:anyevent')
        # test that old format log option is not handled by any handler method.
        gf_mock = mock.create_autospec(gf)
        self.assertFalse(factory.handleArg(gf_mock, '-anotherlog'))
        self.assertFalse(gf_mock.method_calls)

    def test_logevents_with_start_timestamp(self):
        """Test -logevents which uses timestamp for start."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        # We limit the results to 1 as running this on large websites like
        # Wikipedia will give an insane number of results as it asks for all
        # logevents since beginning till now.
        self.assertTrue(gf.handleArg('-limit:1'))
        self.assertTrue(gf.handleArg('-logevents:newusers,,21000101'))
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertIsNotEmpty(pages)
        self.assertTrue(all(isinstance(item, pywikibot.User)
                            for item in pages))

    def test_logevents_with_start_and_end_timestamp(self):
        """Test -logevents which uses timestamps for start and end."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        self.assertTrue(gf.handleArg('-logevents:newusers,,21000101,20990101'))
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertIsEmpty(pages)

    def test_logevents_with_total(self):
        """Test -logevents which uses total."""
        gf = pagegenerators.GeneratorFactory(site=self.site)
        self.assertTrue(gf.handleArg('-logevents:newusers,,1'))
        gen = gf.getCombinedGenerator()
        self.assertIsNotNone(gen)
        pages = set(gen)
        self.assertLength(pages, 1)
        self.assertTrue(all(isinstance(item, pywikibot.User)
                            for item in pages))


class PageGeneratorIntersectTestCase(GeneratorIntersectTestCase,
                                     RecentChangesTestCase):

    """Page intersect_generators test cases."""

    def test_intersect_newpages_twice(self):
        """Test newpages intersection."""
        site = self.get_site()
        self.assertEqualItertools(
            [pagegenerators.NewpagesPageGenerator(site=site, total=10),
             pagegenerators.NewpagesPageGenerator(site=site, total=10)])

    def test_intersect_newpages_and_recentchanges(self):
        """Test intersection betweem newpages and recentchanges."""
        site = self.get_site()
        self.assertEqualItertools(
            [pagegenerators.NewpagesPageGenerator(site=site, total=50),
             pagegenerators.RecentChangesPageGenerator(site=site, total=200)])


class EnWikipediaPageGeneratorIntersectTestCase(GeneratorIntersectTestCase,
                                                RecentChangesTestCase):

    """Page intersect_generators test cases."""

    family = 'wikipedia'
    code = 'en'

    def test_intersect_newpages_csd(self):
        """Test intersection between newpages and sd candidates."""
        site = self.get_site()
        self.assertEqualItertools([
            pagegenerators.NewpagesPageGenerator(site=site, total=10),
            pagegenerators.CategorizedPageGenerator(
                pywikibot.Category(
                    site, 'Category:Candidates_for_speedy_deletion'))]
        )


class EventStreamsPageGeneratorTestCase(RecentChangesTestCase):

    """Test case for Live Recent Changes pagegenerator."""

    @classmethod
    def setUpClass(cls):
        """Setup test class."""
        super().setUpClass()
        cls.client = 'sseclient'
        if not has_module(cls.client):
            raise unittest.SkipTest('{0} is not available'.format(cls.client))

    def test_RC_pagegenerator_result(self):
        """Test RC pagegenerator."""
        lgr = logging.getLogger(self.client)
        lgr.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        lgr.addHandler(ch)

        site = self.get_site()
        pagegenerator = pagegenerators.LiveRCPageGenerator(site,
                                                           total=self.length)
        entries = list(pagegenerator)
        self.assertLength(entries, self.length)

        testentry = entries[0]
        self.assertEqual(testentry.site, site)
        self.assertTrue(hasattr(testentry, '_rcinfo'))

        rcinfo = testentry._rcinfo
        self.assertEqual(rcinfo['server_name'], site.hostname())
        self.assertEqual(rcinfo['wiki'], site.dbName())

        for key in ['type', 'namespace', 'title', 'comment',
                    'timestamp', 'user', 'bot']:
            self.assertIn(key, rcinfo.keys())


class TestUnconnectedPageGenerator(DefaultSiteTestCase):

    """Test UnconnectedPageGenerator."""

    cached = True

    def test_unconnected_with_repo(self):
        """Test UnconnectedPageGenerator."""
        if not self.site.data_repository():
            self.skipTest('Site is not using a Wikibase repository')
        with suppress_warnings(
                'pywikibot.pagegenerators.UnconnectedPageGenerator is '
                'deprecated', DeprecationWarning):
            upgen = pagegenerators.UnconnectedPageGenerator(self.site, 3)
        self.assertDictEqual(
            upgen.request._params, {
                'gqppage': ['UnconnectedPages'],
                'prop': ['info', 'imageinfo', 'categoryinfo'],
                'inprop': ['protection'],
                'iilimit': ['max'],
                'iiprop': ['timestamp', 'user', 'comment', 'url', 'size',
                           'sha1', 'metadata'],
                'generator': ['querypage'], 'action': ['query'],
                'indexpageids': [True], 'continue': [True]})
        self.assertLessEqual(len(tuple(upgen)), 3)

    def test_unconnected_without_repo(self):
        """Test that it raises a ValueError on sites without repository."""
        if self.site.data_repository():
            self.skipTest('Site is using a Wikibase repository')
        with self.assertRaises(ValueError):
            for page in pagegenerators.UnconnectedPageGenerator(self.site,
                                                                total=5):
                assert False  # this shouldn't be reached


class TestLinksearchPageGenerator(TestCase):

    """Tests for pagegenerators.LinksearchPageGenerator."""

    family = 'wikipedia'
    code = 'en'

    def test_weblink(self):
        """Test -weblink."""
        cases = (('wikipedia.org', 'http://wikipedia.org'),
                 ('en.wikipedia.org', 'http://en.wikipedia.org'),
                 ('https://fr.wikipedia.org', 'https://fr.wikipedia.org'),
                 ('ftp://*', 'ftp://'))

        for search, expected in cases:
            gf = pagegenerators.GeneratorFactory(site=self.site)
            gf.handleArg('-weblink:{}'.format(search))
            gf.handleArg('-ns:2')
            gf.handleArg('-limit:1')
            gen = gf.getCombinedGenerator()
            genlist = list(gen)
            self.assertLength(genlist, 1)

            page = genlist[0]
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 2)
            self.assertIn(expected, page.text)

    def test_double_opposite_protocols(self):
        """Test LinksearchPageGenerator with two opposite protocols."""
        self.assertRaises(ValueError, pagegenerators.LinksearchPageGenerator,
                          'http://w.wiki', protocol='https', site=self.site)

    def test_double_same_protocols(self):
        """Test LinksearchPageGenerator with two same protocols."""
        gen = pagegenerators.LinksearchPageGenerator('https://w.wiki',
                                                     protocol='https',
                                                     site=self.site,
                                                     total=1)
        self.assertIsInstance(gen, pywikibot.data.api.PageGenerator)
        self.assertLength(list(gen), 1)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
