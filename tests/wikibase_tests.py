# -*- coding: utf-8 -*-
"""Tests for the Wikidata parts of the page module."""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
import copy
import json

from contextlib import suppress
from decimal import Decimal

import pywikibot

from pywikibot import pagegenerators
from pywikibot.page import (
    WikibasePage, ItemPage, PropertyPage, Page, LanguageDict, AliasesDict,
    ClaimCollection, SiteLinkCollection,
)
from pywikibot.site import Namespace, NamespacesDict
from pywikibot.tools import MediaWikiVersion, suppress_warnings

from tests import join_pages_path, mock
from tests.aspects import (
    DeprecationTestCase,
    TestCase,
    unittest,
    WikidataTestCase,
)

from tests.basepage import (
    BasePageMethodsTestBase,
    BasePageLoadRevisionsCachingTestBase,
)


# fetch a page which is very likely to be unconnected, which doesn't have
# a generator, and unit tests may be used to test old versions of pywikibot
def _get_test_unconnected_page(site):
    """Get unconnected page from site for tests."""
    gen = pagegenerators.NewpagesPageGenerator(site=site, total=10,
                                               namespaces=[1, ])
    for page in gen:
        if not page.properties().get('wikibase_item'):
            return page


class WbRepresentationTestCase(WikidataTestCase):

    """Test methods inherited or extended from _WbRepresentation."""

    def _test_hashable(self, representation):
        """Test that the representation is hashable."""
        list_of_dupes = [representation, representation]
        self.assertLength(set(list_of_dupes), 1)


class TestLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                               WikidataTestCase):

    """Test site.loadrevisions() caching."""

    def setUp(self):
        """Setup test."""
        self._page = ItemPage(self.get_repo(), 'Q60')
        super().setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()


class TestDeprecatedAttributes(WikidataTestCase, DeprecationTestCase):

    """Test deprecated lastrevid."""

    def test_lastrevid(self):
        """Test deprecated lastrevid."""
        item = ItemPage(self.get_repo(), 'Q60')
        self.assertFalse(hasattr(item, 'lastrevid'))
        item.get()
        self.assertTrue(hasattr(item, 'lastrevid'))
        self.assertIsInstance(item.lastrevid, int)
        self.assertDeprecation()
        self._reset_messages()

        item.lastrevid = 1
        self.assertTrue(hasattr(item, 'lastrevid'))
        self.assertTrue(hasattr(item, '_revid'))
        self.assertEqual(item.lastrevid, 1)
        self.assertEqual(item._revid, 1)
        self.assertDeprecation()

    def test_lastrevid_del(self):
        """Test del with deprecated lastrevid."""
        item = ItemPage(self.get_repo(), 'Q60')
        item.get()
        self.assertTrue(hasattr(item, 'lastrevid'))
        self.assertTrue(hasattr(item, '_revid'))

        del item.lastrevid
        self.assertFalse(hasattr(item, 'lastrevid'))
        self.assertFalse(hasattr(item, '_revid'))
        self.assertDeprecation()


class TestGeneral(WikidataTestCase):

    """General Wikibase tests."""

    @classmethod
    def setUpClass(cls):
        """Setup test class."""
        super().setUpClass()
        enwiki = pywikibot.Site('en', 'wikipedia')
        cls.mainpage = pywikibot.Page(pywikibot.page.Link('Main Page', enwiki))

    def testWikibase(self):
        """Wikibase tests."""
        repo = self.get_repo()
        item_namespace = repo.namespaces[0]
        self.assertEqual(item_namespace.defaultcontentmodel, 'wikibase-item')
        item = ItemPage.fromPage(self.mainpage)
        self.assertIsInstance(item, ItemPage)
        self.assertEqual(item.getID(), 'Q5296')
        self.assertEqual(item.title(), 'Q5296')
        self.assertIn('en', item.labels)
        self.assertTrue(item.labels['en'].lower().endswith('main page'))
        self.assertIn('en', item.aliases)
        self.assertIn('home page', (a.lower() for a in item.aliases['en']))
        self.assertEqual(item.namespace(), 0)
        item2 = ItemPage(repo, 'q5296')
        self.assertEqual(item2.getID(), 'Q5296')
        item2.get()
        self.assertTrue(item2.labels['en'].lower().endswith('main page'))
        prop = PropertyPage(repo, 'Property:P21')
        self.assertEqual(prop.type, 'wikibase-item')
        self.assertEqual(prop.namespace(), 120)
        claim = pywikibot.Claim(repo, 'p21')
        regex = r' is not type .+\.$'
        with self.assertRaisesRegex(ValueError, regex):
            claim.setTarget(value='test')
        claim.setTarget(ItemPage(repo, 'q1'))
        self.assertEqual(claim._formatValue(), {'entity-type': 'item',
                                                'numeric-id': 1})

    def test_cmp(self):
        """Test WikibasePage comparison."""
        self.assertEqual(ItemPage.fromPage(self.mainpage),
                         ItemPage(self.get_repo(), 'q5296'))


class TestWikibaseCoordinate(WbRepresentationTestCase):

    """Test Wikibase Coordinate data type."""

    dry = True

    def test_Coordinate_WbRepresentation_methods(self):
        """Test inherited or extended methods from _WbRepresentation."""
        repo = self.get_repo()
        coord = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe='moon')
        self._test_hashable(coord)

    def test_Coordinate_dim(self):
        """Test Coordinate dimension."""
        repo = self.get_repo()
        x = pywikibot.Coordinate(site=repo, lat=12.0, lon=13.0, precision=5.0)
        self.assertEqual(x.precisionToDim(), 544434)
        self.assertIsInstance(x.precisionToDim(), int)
        y = pywikibot.Coordinate(site=repo, lat=12.0, lon=13.0, dim=54444)
        self.assertEqual(y.precision, 0.500005084017101)
        self.assertIsInstance(y.precision, float)
        z = pywikibot.Coordinate(site=repo, lat=12.0, lon=13.0)
        regex = r'^No values set for dim or precision$'
        with self.assertRaisesRegex(ValueError, regex):
            z.precisionToDim()

    def test_Coordinate_plain_globe(self):
        """Test setting Coordinate globe from a plain-text value."""
        repo = self.get_repo()
        coord = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe='moon')
        self.assertEqual(coord.toWikibase(),
                         {'latitude': 12.0, 'longitude': 13.0,
                          'altitude': None, 'precision': 0,
                          'globe': 'http://www.wikidata.org/entity/Q405'})

    def test_Coordinate_entity_uri_globe(self):
        """Test setting Coordinate globe from an entity uri."""
        repo = self.get_repo()
        coord = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item='http://www.wikidata.org/entity/Q123')
        self.assertEqual(coord.toWikibase(),
                         {'latitude': 12.0, 'longitude': 13.0,
                          'altitude': None, 'precision': 0,
                          'globe': 'http://www.wikidata.org/entity/Q123'})


class TestWikibaseCoordinateNonDry(WbRepresentationTestCase):

    """
    Test Wikibase Coordinate data type (non-dry).

    These can be moved to TestWikibaseCoordinate once DrySite has been bumped
    to the appropriate version.
    """

    def test_Coordinate_item_globe(self):
        """Test setting Coordinate globe from an ItemPage."""
        repo = self.get_repo()
        coord = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item=ItemPage(repo, 'Q123'))
        self.assertEqual(coord.toWikibase(),
                         {'latitude': 12.0, 'longitude': 13.0,
                          'altitude': None, 'precision': 0,
                          'globe': 'http://www.wikidata.org/entity/Q123'})

    def test_Coordinate_get_globe_item_from_uri(self):
        """Test getting globe item from Coordinate with entity uri globe."""
        repo = self.get_repo()
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item='http://www.wikidata.org/entity/Q123')
        self.assertEqual(q.get_globe_item(), ItemPage(repo, 'Q123'))

    def test_Coordinate_get_globe_item_from_itempage(self):
        """Test getting globe item from Coordinate with ItemPage globe."""
        repo = self.get_repo()
        globe = ItemPage(repo, 'Q123')
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0, globe_item=globe)
        self.assertEqual(q.get_globe_item(), ItemPage(repo, 'Q123'))

    def test_Coordinate_get_globe_item_from_plain_globe(self):
        """Test getting globe item from Coordinate with plain text globe."""
        repo = self.get_repo()
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0, globe='moon')
        self.assertEqual(q.get_globe_item(), ItemPage(repo, 'Q405'))

    def test_Coordinate_get_globe_item_provide_repo(self):
        """Test getting globe item from Coordinate, providing repo."""
        repo = self.get_repo()
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item='http://www.wikidata.org/entity/Q123')
        self.assertEqual(q.get_globe_item(repo), ItemPage(repo, 'Q123'))

    def test_Coordinate_get_globe_item_different_repo(self):
        """Test getting globe item in different repo from Coordinate."""
        repo = self.get_repo()
        test_repo = pywikibot.Site('test', 'wikidata')
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item='http://test.wikidata.org/entity/Q123')
        self.assertEqual(q.get_globe_item(test_repo),
                         ItemPage(test_repo, 'Q123'))

    def test_Coordinate_equality(self):
        """Test Coordinate equality with different globe representations."""
        repo = self.get_repo()
        a = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0.1,
            globe='moon')
        b = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0.1,
            globe_item='http://www.wikidata.org/entity/Q405')
        c = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0.1,
            globe_item=ItemPage(repo, 'Q405'))
        d = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0.1,
            globe_item='http://test.wikidata.org/entity/Q405')
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, a)
        self.assertNotEqual(a, d)
        self.assertNotEqual(b, d)
        self.assertNotEqual(c, d)


class TestWbTime(WbRepresentationTestCase):

    """Test Wikibase WbTime data type."""

    dry = True

    def test_WbTime_WbRepresentation_methods(self):
        """Test inherited or extended methods from _WbRepresentation."""
        repo = self.get_repo()
        t = pywikibot.WbTime(site=repo, year=2010, month=0, day=0, hour=12,
                             minute=43)
        self._test_hashable(t)

    def test_WbTime_timestr(self):
        """Test timestr functions of WbTime."""
        repo = self.get_repo()
        t = pywikibot.WbTime(site=repo, year=2010, month=0, day=0, hour=12,
                             minute=43)
        self.assertEqual(t.toTimestr(), '+00000002010-00-00T12:43:00Z')
        self.assertEqual(t.toTimestr(force_iso=True), '+2010-01-01T12:43:00Z')

        t = pywikibot.WbTime(site=repo, year=2010, hour=12, minute=43)
        self.assertEqual(t.toTimestr(), '+00000002010-01-01T12:43:00Z')
        self.assertEqual(t.toTimestr(force_iso=True), '+2010-01-01T12:43:00Z')

        t = pywikibot.WbTime(site=repo, year=-2010, hour=12, minute=43)
        self.assertEqual(t.toTimestr(), '-00000002010-01-01T12:43:00Z')
        self.assertEqual(t.toTimestr(force_iso=True), '-2010-01-01T12:43:00Z')

    def test_WbTime_fromTimestr(self):
        """Test WbTime creation from UTC date/time string."""
        repo = self.get_repo()
        t = pywikibot.WbTime.fromTimestr('+00000002010-01-01T12:43:00Z',
                                         site=repo)
        self.assertEqual(t, pywikibot.WbTime(site=repo, year=2010, hour=12,
                                             minute=43, precision=14))

    def test_WbTime_zero_month(self):
        """Test WbTime creation from date/time string with zero month."""
        # ensures we support formats in T123888 / T107870
        repo = self.get_repo()
        t = pywikibot.WbTime.fromTimestr('+00000002010-00-00T12:43:00Z',
                                         site=repo)
        self.assertEqual(t, pywikibot.WbTime(site=repo, year=2010, month=0,
                                             day=0, hour=12, minute=43,
                                             precision=14))

    def test_WbTime_timestamp(self):
        """Test timestamp functions of WbTime."""
        repo = self.get_repo()
        timestamp = pywikibot.Timestamp.fromISOformat('2010-01-01T12:43:00Z')
        t = pywikibot.WbTime(site=repo, year=2010, month=0, day=0, hour=12,
                             minute=43)
        self.assertEqual(t.toTimestamp(), timestamp)

        # Roundtrip fails as Timestamp and WbTime interpret month=0 differently
        self.assertNotEqual(
            t, pywikibot.WbTime.fromTimestamp(timestamp, site=repo))

        t = pywikibot.WbTime(site=repo, year=2010, hour=12, minute=43)
        self.assertEqual(t.toTimestamp(), timestamp)

        t = pywikibot.WbTime(site=repo, year=-2010, hour=12, minute=43)
        regex = r'^You cannot turn BC dates into a Timestamp$'
        self.assertRaisesRegex(ValueError, regex, t.toTimestamp)

        t = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                             minute=43, second=0)
        self.assertEqual(t.toTimestamp(), timestamp)
        self.assertEqual(
            t, pywikibot.WbTime.fromTimestamp(timestamp, site=repo))

    def test_WbTime_errors(self):
        """Test WbTime precision errors."""
        repo = self.get_repo()
        regex = r'^no year given$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTime(site=repo, precision=15)
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTime(site=repo, precision='invalid_precision')


class TestWbQuantity(WbRepresentationTestCase):

    """Test Wikibase WbQuantity data type."""

    dry = True

    def test_WbQuantity_WbRepresentation_methods(self):
        """Test inherited or extended methods from _WbRepresentation."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo)
        self._test_hashable(q)

    def test_WbQuantity_integer(self):
        """Test WbQuantity for integer value."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235', 'unit': '1', })
        q = pywikibot.WbQuantity(amount=5, error=(2, 3), site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+5', 'lowerBound': '+2',
                          'upperBound': '+7', 'unit': '1', })
        q = pywikibot.WbQuantity(amount=0, error=(0, 0), site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+0', 'lowerBound': '+0',
                          'upperBound': '+0', 'unit': '1', })
        q = pywikibot.WbQuantity(amount=-5, error=(2, 3), site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '-5', 'lowerBound': '-8',
                          'upperBound': '-3', 'unit': '1', })

    def test_WbQuantity_float_27(self):
        """Test WbQuantity for float value."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=0.044405586, error=0.0, site=repo)
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1', }
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_scientific(self):
        """Test WbQuantity for scientific notation."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount='1.3e-13', error='1e-14', site=repo)
        q_dict = {'amount': '+1.3e-13', 'lowerBound': '+1.2e-13',
                  'upperBound': '+1.4e-13', 'unit': '1', }
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_decimal(self):
        """Test WbQuantity for decimal value."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=Decimal('0.044405586'),
                                 error=Decimal('0.0'), site=repo)
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1', }
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_string(self):
        """Test WbQuantity for decimal notation."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount='0.044405586', error='0', site=repo)
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1', }
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_formatting_bound(self):
        """Test WbQuantity formatting with bounds."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount='0.044405586', error='0', site=repo)
        self.assertEqual('%s' % q,
                         '{\n'
                         '    "amount": "+%(val)s",\n'
                         '    "lowerBound": "+%(val)s",\n'
                         '    "unit": "1",\n'
                         '    "upperBound": "+%(val)s"\n'
                         '}' % {'val': '0.044405586'})
        self.assertEqual('%r' % q,
                         'WbQuantity(amount=%(val)s, '
                         'upperBound=%(val)s, lowerBound=%(val)s, '
                         'unit=1)' % {'val': '0.044405586'})

    def test_WbQuantity_self_equality(self):
        """Test WbQuantity equality."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount='0.044405586', error='0', site=repo)
        self.assertEqual(q, q)

    def test_WbQuantity_fromWikibase(self):
        """Test WbQuantity.fromWikibase() instantiating."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity.fromWikibase({'amount': '+0.0229',
                                               'lowerBound': '0',
                                               'upperBound': '1',
                                               'unit': '1'},
                                              site=repo)
        # note that the bounds are inputted as INT but are returned as FLOAT
        self.assertEqual(q.toWikibase(),
                         {'amount': '+0.0229', 'lowerBound': '+0.0000',
                          'upperBound': '+1.0000', 'unit': '1', })

    def test_WbQuantity_errors(self):
        """Test WbQuantity error handling."""
        regex = r'^no amount given$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbQuantity(amount=None, error=1)

    def test_WbQuantity_entity_unit(self):
        """Test WbQuantity with entity uri unit."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo,
                                 unit='http://www.wikidata.org/entity/Q712226')
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235',
                          'unit': 'http://www.wikidata.org/entity/Q712226', })

    def test_WbQuantity_unit_fromWikibase(self):
        """Test WbQuantity recognising unit from Wikibase output."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity.fromWikibase({
            'amount': '+1234', 'lowerBound': '+1233', 'upperBound': '+1235',
            'unit': 'http://www.wikidata.org/entity/Q712226', },
            site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235',
                          'unit': 'http://www.wikidata.org/entity/Q712226', })


class TestWbQuantityNonDry(WbRepresentationTestCase):

    """
    Test Wikibase WbQuantity data type (non-dry).

    These can be moved to TestWbQuantity once DrySite has been bumped to
    the appropriate version.
    """

    def setUp(self):
        """Override setup to store repo and it's version."""
        super().setUp()
        self.repo = self.get_repo()
        self.version = self.repo.mw_version

    def test_WbQuantity_unbound(self):
        """Test WbQuantity for value without bounds."""
        if self.version < MediaWikiVersion('1.29.0-wmf.2'):
            self.skipTest('Wiki version must be 1.29.0-wmf.2 or newer to '
                          'support unbound uncertainties.')
        q = pywikibot.WbQuantity(amount=1234.5, site=self.repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234.5', 'unit': '1',
                          'upperBound': None, 'lowerBound': None})

    def test_WbQuantity_formatting_unbound(self):
        """Test WbQuantity formatting without bounds."""
        if self.version < MediaWikiVersion('1.29.0-wmf.2'):
            self.skipTest('Wiki version must be 1.29.0-wmf.2 or newer to '
                          'support unbound uncertainties.')
        q = pywikibot.WbQuantity(amount='0.044405586', site=self.repo)
        self.assertEqual('%s' % q,
                         '{\n'
                         '    "amount": "+%(val)s",\n'
                         '    "lowerBound": null,\n'
                         '    "unit": "1",\n'
                         '    "upperBound": null\n'
                         '}' % {'val': '0.044405586'})
        self.assertEqual('%r' % q,
                         'WbQuantity(amount=%(val)s, '
                         'upperBound=None, lowerBound=None, '
                         'unit=1)' % {'val': '0.044405586'})

    def test_WbQuantity_fromWikibase_unbound(self):
        """Test WbQuantity.fromWikibase() instantiating without bounds."""
        if self.version < MediaWikiVersion('1.29.0-wmf.2'):
            self.skipTest('Wiki version must be 1.29.0-wmf.2 or newer to '
                          'support unbound uncertainties.')
        q = pywikibot.WbQuantity.fromWikibase({'amount': '+0.0229',
                                               'unit': '1'},
                                              site=self.repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+0.0229', 'lowerBound': None,
                          'upperBound': None, 'unit': '1', })

    def test_WbQuantity_ItemPage_unit(self):
        """Test WbQuantity with ItemPage unit."""
        if self.version < MediaWikiVersion('1.28-wmf.23'):
            self.skipTest('Wiki version must be 1.28-wmf.23 or newer to '
                          'expose wikibase-conceptbaseuri.')

        q = pywikibot.WbQuantity(amount=1234, error=1,
                                 unit=pywikibot.ItemPage(self.repo, 'Q712226'))
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235',
                          'unit': 'http://www.wikidata.org/entity/Q712226', })

    def test_WbQuantity_equality(self):
        """Test WbQuantity equality with different unit representations."""
        if self.version < MediaWikiVersion('1.28-wmf.23'):
            self.skipTest('Wiki version must be 1.28-wmf.23 or newer to '
                          'expose wikibase-conceptbaseuri.')

        a = pywikibot.WbQuantity(
            amount=1234, error=1,
            unit=pywikibot.ItemPage(self.repo, 'Q712226'))
        b = pywikibot.WbQuantity(
            amount=1234, error=1,
            unit='http://www.wikidata.org/entity/Q712226')
        c = pywikibot.WbQuantity(
            amount=1234, error=1,
            unit='http://test.wikidata.org/entity/Q712226')
        d = pywikibot.WbQuantity(
            amount=1234, error=2,
            unit='http://www.wikidata.org/entity/Q712226')
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(b, c)
        self.assertNotEqual(b, d)

    def test_WbQuantity_get_unit_item(self):
        """Test getting unit item from WbQuantity."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo,
                                 unit='http://www.wikidata.org/entity/Q123')
        self.assertEqual(q.get_unit_item(),
                         ItemPage(repo, 'Q123'))

    def test_WbQuantity_get_unit_item_provide_repo(self):
        """Test getting unit item from WbQuantity, providing repo."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1,
                                 unit='http://www.wikidata.org/entity/Q123')
        self.assertEqual(q.get_unit_item(repo),
                         ItemPage(repo, 'Q123'))

    def test_WbQuantity_get_unit_item_different_repo(self):
        """Test getting unit item in different repo from WbQuantity."""
        repo = self.get_repo()
        test_repo = pywikibot.Site('test', 'wikidata')
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo,
                                 unit='http://test.wikidata.org/entity/Q123')
        self.assertEqual(q.get_unit_item(test_repo),
                         ItemPage(test_repo, 'Q123'))


class TestWbMonolingualText(WbRepresentationTestCase):

    """Test Wikibase WbMonolingualText data type."""

    dry = True

    def test_WbMonolingualText_WbRepresentation_methods(self):
        """Test inherited or extended methods from _WbRepresentation."""
        q = pywikibot.WbMonolingualText(
            text='Test that basics work', language='en')
        self._test_hashable(q)

    def test_WbMonolingualText_string(self):
        """Test WbMonolingualText string."""
        q = pywikibot.WbMonolingualText(text='Test that basics work',
                                        language='en')
        q_dict = {'text': 'Test that basics work', 'language': 'en'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbMonolingualText_unicode(self):
        """Test WbMonolingualText unicode."""
        q = pywikibot.WbMonolingualText(text='Testa det här', language='sv')
        q_dict = {'text': 'Testa det här', 'language': 'sv'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbMonolingualText_equality(self):
        """Test WbMonolingualText equality."""
        q = pywikibot.WbMonolingualText(text='Thou shall test this!',
                                        language='en-gb')
        self.assertEqual(q, q)

    def test_WbMonolingualText_fromWikibase(self):
        """Test WbMonolingualText.fromWikibase() instantiating."""
        q = pywikibot.WbMonolingualText.fromWikibase({'text': 'Test this!',
                                                      'language': 'en'})
        self.assertEqual(q.toWikibase(),
                         {'text': 'Test this!', 'language': 'en'})

    def test_WbMonolingualText_errors(self):
        """Test WbMonolingualText error handling."""
        regex = r'^text and language cannot be empty$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbMonolingualText(text='', language='sv')
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbMonolingualText(text='Test this!', language='')
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbMonolingualText(text=None, language='sv')


class TestWbGeoShapeNonDry(WbRepresentationTestCase):

    """
    Test Wikibase WbGeoShape data type (non-dry).

    These require non dry tests due to the page.exists() call.
    """

    def setUp(self):
        """Setup tests."""
        self.commons = pywikibot.Site('commons', 'commons')
        self.page = Page(self.commons, 'Data:Lyngby Hovedgade.map')
        super().setUp()

    def test_WbGeoShape_WbRepresentation_methods(self):
        """Test inherited or extended methods from _WbRepresentation."""
        q = pywikibot.WbGeoShape(self.page)
        self._test_hashable(q)

    def test_WbGeoShape_page(self):
        """Test WbGeoShape page."""
        q = pywikibot.WbGeoShape(self.page)
        q_val = 'Data:Lyngby Hovedgade.map'
        self.assertEqual(q.toWikibase(), q_val)

    def test_WbGeoShape_page_and_site(self):
        """Test WbGeoShape from page and site."""
        q = pywikibot.WbGeoShape(self.page, self.get_repo())
        q_val = 'Data:Lyngby Hovedgade.map'
        self.assertEqual(q.toWikibase(), q_val)

    def test_WbGeoShape_equality(self):
        """Test WbGeoShape equality."""
        q = pywikibot.WbGeoShape(self.page, self.get_repo())
        self.assertEqual(q, q)

    def test_WbGeoShape_fromWikibase(self):
        """Test WbGeoShape.fromWikibase() instantiating."""
        repo = self.get_repo()
        q = pywikibot.WbGeoShape.fromWikibase(
            'Data:Lyngby Hovedgade.map', repo)
        self.assertEqual(q.toWikibase(), 'Data:Lyngby Hovedgade.map')

    def test_WbGeoShape_error_on_non_page(self):
        """Test WbGeoShape error handling when given a non-page."""
        regex = r'^Page .+? must be a pywikibot\.Page object not a'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape('A string', self.get_repo())

    def test_WbGeoShape_error_on_non_exitant_page(self):
        """Test WbGeoShape error handling of a non-existant page."""
        page = Page(self.commons, 'Non-existant page... really')
        regex = r'^Page \[\[.+?\]\] must exist\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape(page, self.get_repo())

    def test_WbGeoShape_error_on_wrong_site(self):
        """Test WbGeoShape error handling of a page on non-filerepo site."""
        repo = self.get_repo()
        page = Page(repo, 'Q123')
        regex = r'^Page must be on the geo-shape repository site\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape(page, self.get_repo())

    def test_WbGeoShape_error_on_wrong_page_type(self):
        """Test WbGeoShape error handling of a non-map page."""
        non_data_page = Page(self.commons, 'File:Foo.jpg')
        non_map_page = Page(self.commons, 'Data:TemplateData/TemplateData.tab')
        regex = r"^Page must be in 'Data:' namespace and end in '\.map' " + \
                r'for geo-shape\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape(non_data_page, self.get_repo())
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape(non_map_page, self.get_repo())


class TestWbTabularDataNonDry(WbRepresentationTestCase):

    """
    Test Wikibase WbTabularData data type (non-dry).

    These require non dry tests due to the page.exists() call.
    """

    def setUp(self):
        """Setup tests."""
        self.commons = pywikibot.Site('commons', 'commons')
        self.page = Page(self.commons, 'Data:Bea.gov/GDP by state.tab')
        super().setUp()

    def test_WbTabularData_WbRepresentation_methods(self):
        """Test inherited or extended methods from _WbRepresentation."""
        q = pywikibot.WbTabularData(self.page)
        self._test_hashable(q)

    def test_WbTabularData_page(self):
        """Test WbTabularData page."""
        q = pywikibot.WbTabularData(self.page)
        q_val = 'Data:Bea.gov/GDP by state.tab'
        self.assertEqual(q.toWikibase(), q_val)

    def test_WbTabularData_page_and_site(self):
        """Test WbTabularData from page and site."""
        q = pywikibot.WbTabularData(self.page, self.get_repo())
        q_val = 'Data:Bea.gov/GDP by state.tab'
        self.assertEqual(q.toWikibase(), q_val)

    def test_WbTabularData_equality(self):
        """Test WbTabularData equality."""
        q = pywikibot.WbTabularData(self.page, self.get_repo())
        self.assertEqual(q, q)

    def test_WbTabularData_fromWikibase(self):
        """Test WbTabularData.fromWikibase() instantiating."""
        repo = self.get_repo()
        q = pywikibot.WbTabularData.fromWikibase(
            'Data:Bea.gov/GDP by state.tab', repo)
        self.assertEqual(q.toWikibase(), 'Data:Bea.gov/GDP by state.tab')

    def test_WbTabularData_error_on_non_page(self):
        """Test WbTabularData error handling when given a non-page."""
        regex = r'^Page .+? must be a pywikibot\.Page object not a'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData('A string', self.get_repo())

    def test_WbTabularData_error_on_non_exitant_page(self):
        """Test WbTabularData error handling of a non-existant page."""
        page = Page(self.commons, 'Non-existant page... really')
        regex = r'^Page \[\[.+?\]\] must exist\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData(page, self.get_repo())

    def test_WbTabularData_error_on_wrong_site(self):
        """Test WbTabularData error handling of a page on non-filerepo site."""
        repo = self.get_repo()
        page = Page(repo, 'Q123')
        regex = r'^Page must be on the tabular-data repository site\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData(page, self.get_repo())

    def test_WbTabularData_error_on_wrong_page_type(self):
        """Test WbTabularData error handling of a non-map page."""
        non_data_page = Page(self.commons, 'File:Foo.jpg')
        non_map_page = Page(self.commons, 'Data:Lyngby Hovedgade.map')
        regex = r"^Page must be in 'Data:' namespace and end in '\.tab' " + \
                r'for tabular-data\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData(non_data_page, self.get_repo())
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData(non_map_page, self.get_repo())


class TestWbUnknown(WbRepresentationTestCase):

    """Test Wikibase WbUnknown data type."""

    dry = True

    def test_WbUnknown_WbRepresentation_methods(self):
        """Test inherited or extended methods from _WbRepresentation."""
        q_dict = {'text': 'Test that basics work', 'language': 'en'}
        q = pywikibot.WbUnknown(q_dict)
        self._test_hashable(q)

    def test_WbUnknown_string(self):
        """Test WbUnknown string."""
        q_dict = {'text': 'Test that basics work', 'language': 'en'}
        q = pywikibot.WbUnknown(q_dict)
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbUnknown_equality(self):
        """Test WbUnknown equality."""
        q_dict = {'text': 'Thou shall test this!', 'language': 'unknown'}
        q = pywikibot.WbUnknown(q_dict)
        self.assertEqual(q, q)

    def test_WbUnknown_fromWikibase(self):
        """Test WbUnknown.fromWikibase() instantiating."""
        q = pywikibot.WbUnknown.fromWikibase({'text': 'Test this!',
                                              'language': 'en'})
        self.assertEqual(q.toWikibase(),
                         {'text': 'Test this!', 'language': 'en'})


class TestLoadUnknownType(WikidataTestCase):

    """Test unknown datatypes being loaded as WbUnknown."""

    dry = True

    def setUp(self):
        """Setup test."""
        super().setUp()
        wikidata = self.get_repo()
        self.wdp = ItemPage(wikidata, 'Q60')
        self.wdp.id = 'Q60'
        with open(join_pages_path('Q60_unknown_datatype.wd')) as f:
            self.wdp._content = json.load(f)

    def test_load_unknown(self):
        """Ensure unknown value is loaded but raises a warning."""
        with mock.patch.object(pywikibot, 'warning', autospec=True) as warn:
            self.wdp.get()
            unknown_value = self.wdp.claims['P99999'][0].getTarget()
            self.assertIsInstance(unknown_value, pywikibot.WbUnknown)
            warn.assert_called_once_with(
                'foo-unknown-bar datatype is not supported yet.')


class TestItemPageExtensibility(TestCase):

    """Test ItemPage extensibility."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_ItemPage_extensibility(self):
        """Test ItemPage extensibility."""
        class MyItemPage(ItemPage):

            """Dummy ItemPage subclass."""

            pass
        page = pywikibot.Page(self.site, 'foo')
        self.assertIsInstance(MyItemPage.fromPage(page, lazy_load=True),
                              MyItemPage)


class TestItemLoad(WikidataTestCase):

    """
    Test item creation.

    Tests for item creation include:
    1. by Q id
    2. ItemPage.fromPage(page)
    3. ItemPage.fromPage(page_with_props_loaded)
    4. ItemPage.from_entity_uri(site, uri)

    Test various invalid scenarios:
    1. invalid Q ids
    2. invalid pages to fromPage
    3. missing pages to fromPage
    4. unconnected pages to fromPage
    """

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        }
    }

    @classmethod
    def setUpClass(cls):
        """Setup test class."""
        super().setUpClass()
        cls.site = cls.get_site('enwiki')

    def setUp(self):
        """Setup test."""
        super().setUp()
        self.nyc = pywikibot.Page(pywikibot.page.Link('New York City',
                                                      self.site))

    def test_item_normal(self):
        """Test normal wikibase item."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q60')
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})
        self.assertEqual(item.id, 'Q60')
        self.assertFalse(hasattr(item, '_title'))
        self.assertFalse(hasattr(item, '_site'))
        self.assertEqual(item.title(), 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        self.assertFalse(hasattr(item, '_content'))
        item.get()
        self.assertTrue(hasattr(item, '_content'))

    def test_item_lazy_initialization(self):
        """Test that Wikibase items are properly initialized lazily."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q60')
        attrs = ['_content', 'labels', 'descriptions', 'aliases',
                 'claims', 'sitelinks']
        for attr in attrs:
            with self.subTest(attr=attr, note='before loading'):
                # hasattr() loads the attributes; use item.__dict__ for tests
                self.assertNotIn(attr, item.__dict__)

        item.labels  # trigger loading
        for attr in attrs:
            with self.subTest(attr=attr, note='after loading'):
                self.assertIn(attr, item.__dict__)

    def test_load_item_set_id(self):
        """Test setting item.id attribute on empty item."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, '-1')
        self.assertEqual(item._link._title, '-1')
        item.id = 'Q60'
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.getID(), 'Q60')
        self.assertFalse(hasattr(item, '_content'))
        item.get()
        self.assertTrue(hasattr(item, '_content'))
        self.assertIn('en', item.labels)
        self.assertEqual(item.labels['en'], 'New York City')
        self.assertEqual(item.title(), 'Q60')

    def test_reuse_item_set_id(self):
        """
        Test modifying item.id attribute.

        Some scripts are using item.id = 'Q60' semantics, which does work
        but modifying item.id does not currently work, and this test
        highlights that it breaks silently.
        """
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q60')
        item.get()
        self.assertEqual(item.labels['en'], 'New York City')

        # When the id attribute is modified, the ItemPage goes into
        # an inconsistent state.
        item.id = 'Q5296'
        # The title is updated correctly
        self.assertEqual(item.title(), 'Q5296')

        # This del has no effect on the test; it is here to demonstrate that
        # it doesn't help to clear this piece of saved state.
        del item._content
        # The labels are not updated; assertion showing undesirable behaviour:
        self.assertEqual(item.labels['en'], 'New York City')
        # TODO: This is the assertion that this test should be using:
        # self.assertTrue(item.labels['en'].lower().endswith('main page'))

    def test_empty_item(self):
        """
        Test empty wikibase item.

        should not raise an error as the constructor only requires
        the site parameter, with the title parameter defaulted to None.
        """
        wikidata = self.get_repo()
        item = ItemPage(wikidata)
        self.assertEqual(item._link._title, '-1')
        self.assertLength(item.labels, 0)
        self.assertLength(item.descriptions, 0)
        self.assertLength(item.aliases, 0)
        self.assertLength(item.claims, 0)
        self.assertLength(item.sitelinks, 0)

    def test_item_invalid_titles(self):
        """Test invalid titles of wikibase items."""
        wikidata = self.get_repo()

        regex = r"^'.+' is not a valid .+ page title$"
        for title in ['null', 'NULL', 'None',
                      '-2', '1', '0', '+1', 'Q0',
                      'Q0.5', 'Q', 'Q-1', 'Q+1']:
            with self.assertRaisesRegex(pywikibot.InvalidTitle, regex):
                ItemPage(wikidata, title)

        regex = r"^Item's title cannot be empty$"
        with self.assertRaisesRegex(pywikibot.InvalidTitle, regex):
            ItemPage(wikidata, '')

    def test_item_untrimmed_title(self):
        """
        Test intrimmed titles of wikibase items.

        Spaces in the title should not cause an error.
        """
        wikidata = self.get_repo()
        item = ItemPage(wikidata, ' Q60 ')
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item.title(), 'Q60')
        item.get()

    def test_item_missing(self):
        """Test nmissing item."""
        wikidata = self.get_repo()
        # this item has never existed
        item = ItemPage(wikidata, 'Q7')
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.title(), 'Q7')
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        numeric_id = item.getID(numeric=True)
        self.assertIsInstance(numeric_id, int)
        self.assertEqual(numeric_id, 7)
        self.assertFalse(hasattr(item, '_content'))
        regex = r"^Page .+ doesn't exist\.$"
        self.assertRaisesRegex(pywikibot.NoPage, regex, item.get)
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.title(), 'Q7')
        self.assertRaisesRegex(pywikibot.NoPage, regex, item.get)
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        self.assertEqual(item.title(), 'Q7')

    def test_item_never_existed(self):
        """Test non-existent item."""
        wikidata = self.get_repo()
        # this item has not been created
        item = ItemPage(wikidata, 'Q9999999999999999999')
        self.assertFalse(item.exists())
        self.assertEqual(item.getID(), 'Q9999999999999999999')
        regex = r"^Page .+ doesn't exist\.$"
        self.assertRaisesRegex(pywikibot.NoPage, regex, item.get)

    def test_fromPage_noprops(self):
        """Test item from page without properties."""
        page = self.nyc
        item = ItemPage.fromPage(page)
        self.assertEqual(item._link._title, '-1')
        self.assertTrue(hasattr(item, 'id'))
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.title(), 'Q60')
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def test_fromPage_noprops_with_section(self):
        """Test item from page with section."""
        page = pywikibot.Page(self.nyc.site, self.nyc.title() + '#foo')
        item = ItemPage.fromPage(page)
        self.assertEqual(item._link._title, '-1')
        self.assertTrue(hasattr(item, 'id'))
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.title(), 'Q60')
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def test_fromPage_props(self):
        """Test item from page with properties."""
        page = self.nyc
        # fetch page properties
        page.properties()
        item = ItemPage.fromPage(page)
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item.id, 'Q60')
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.title(), 'Q60')
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        self.assertFalse(hasattr(item, '_content'))
        item.get()
        self.assertTrue(hasattr(item, '_content'))
        self.assertTrue(item.exists())
        item2 = ItemPage.fromPage(page)
        self.assertTrue(item is item2)

    def test_fromPage_lazy(self):
        """Test item from page with lazy_load."""
        page = pywikibot.Page(pywikibot.page.Link('New York City', self.site))
        item = ItemPage.fromPage(page, lazy_load=True)
        self.assertEqual(item._defined_by(),
                         {'sites': 'enwiki', 'titles': 'New York City'})
        self.assertEqual(item._link._title, '-1')
        self.assertFalse(hasattr(item, 'id'))
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.title(), 'Q60')
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def test_fromPage_invalid_title(self):
        """Test item from page with invalid title."""
        page = pywikibot.Page(pywikibot.page.Link('[]', self.site))
        regex = r' contains illegal char\(s\) '
        with self.assertRaisesRegex(pywikibot.InvalidTitle, regex):
            ItemPage.fromPage(page)

    def _test_fromPage_noitem(self, link):
        """Helper function to test a page without an associated item.

        It tests two of the ways to fetch an item:
        1. the Page already has props, which should contain a item id if
           present, and that item id is used to instantiate the item, and
        2. the page doesn't have props, in which case the site&titles is
           used to lookup the item id, but that lookup occurs after
           instantiation, during the first attempt to use the data item.
        """
        for props in [True, False]:
            for method in ['title', 'get', 'getID', 'exists']:
                page = pywikibot.Page(link)
                if props:
                    page.properties()

                item = ItemPage.fromPage(page, lazy_load=True)

                self.assertFalse(hasattr(item, 'id'))
                self.assertTrue(hasattr(item, '_title'))
                self.assertTrue(hasattr(item, '_site'))
                self.assertFalse(hasattr(item, '_content'))

                self.assertEqual(item._link._title, '-1')
                # the method 'exists' does not raise an exception
                if method == 'exists':
                    self.assertFalse(item.exists())
                else:
                    regex = r"^Page .+ doesn't exist\.$"
                    with self.assertRaisesRegex(pywikibot.NoPage, regex):
                        getattr(item, method)()

                # The invocation above of a fetching method shouldn't change
                # the local item, but it does! The title changes to '-1'.
                #
                # However when identifying the item for 'en:Test page'
                # (a deleted page), the exception handling is smarter, and no
                # local data is modified in this scenario. This case is
                # separately tested in test_fromPage_missing_lazy.
                if link.title != 'Test page':
                    self.assertEqual(item._link._title, '-1')

                self.assertTrue(hasattr(item, '_content'))

                self.assertFalse(item.exists())

                page = pywikibot.Page(link)
                if props:
                    page.properties()

                # by default, fromPage should always raise the same exception
                regex = r"^Page .+ doesn't exist\.$"
                with self.assertRaisesRegex(pywikibot.NoPage, regex):
                    ItemPage.fromPage(page)

    def test_fromPage_redirect(self):
        """
        Test item from redirect page.

        A redirect should not have a wikidata item.
        """
        link = pywikibot.page.Link('Main page', self.site)
        self._test_fromPage_noitem(link)

    def test_fromPage_missing(self):
        """
        Test item from deleted page.

        A deleted page should not have a wikidata item.
        """
        link = pywikibot.page.Link('Test page', self.site)
        self._test_fromPage_noitem(link)

    def test_fromPage_noitem(self):
        """
        Test item from new page.

        A new created page should not have a wikidata item yet.
        """
        page = _get_test_unconnected_page(self.site)
        link = page._link
        self._test_fromPage_noitem(link)

    def test_fromPage_missing_lazy(self):
        """Test lazy loading of item from nonexistent source page."""
        # this is a deleted page, and should not have a wikidata item
        link = pywikibot.page.Link('Test page', self.site)
        page = pywikibot.Page(link)
        # ItemPage.fromPage should raise an exception when not lazy loading
        # and that exception should refer to the source title 'Test page'
        # not the Item being created.
        with self.assertRaisesRegex(pywikibot.NoPage, 'Test page'):
            ItemPage.fromPage(page, lazy_load=False)

        item = ItemPage.fromPage(page, lazy_load=True)

        # Now verify that delay loading will result in the desired semantics.
        # It should not raise NoPage on the wikibase item which has a title
        # like '-1' or 'Null', as that is useless to determine the cause
        # without a full debug log.
        # It should raise NoPage on the source page, with title 'Test page'
        # as that is what the bot operator needs to see in the log output.
        self.assertRaisesRegex(pywikibot.NoPage, 'Test page', item.get)

    def test_from_entity_uri(self):
        """Test ItemPage.from_entity_uri."""
        repo = self.get_repo()
        entity_uri = 'http://www.wikidata.org/entity/Q124'
        self.assertEqual(ItemPage.from_entity_uri(repo, entity_uri),
                         ItemPage(repo, 'Q124'))

    def test_from_entity_uri_not_a_data_repo(self):
        """Test ItemPage.from_entity_uri with a non-Wikibase site."""
        repo = self.site
        entity_uri = 'http://www.wikidata.org/entity/Q124'
        regex = r' is not a data repository\.$'
        with self.assertRaisesRegex(TypeError, regex):
            ItemPage.from_entity_uri(repo, entity_uri)

    def test_from_entity_uri_wrong_repo(self):
        """Test ItemPage.from_entity_uri with unexpected item repo."""
        repo = self.get_repo()
        entity_uri = 'http://test.wikidata.org/entity/Q124'
        regex = r'^The supplied data repository \(.+\) does not ' + \
                r'correspond to that of the item \(.+\)$'
        with self.assertRaisesRegex(ValueError, regex):
            ItemPage.from_entity_uri(repo, entity_uri)

    def test_from_entity_uri_invalid_title(self):
        """Test ItemPage.from_entity_uri with an invalid item title format."""
        repo = self.get_repo()
        entity_uri = 'http://www.wikidata.org/entity/Nonsense'
        regex = r"^'.+' is not a valid .+ page title$"
        with self.assertRaisesRegex(pywikibot.InvalidTitle, regex):
            ItemPage.from_entity_uri(repo, entity_uri)

    def test_from_entity_uri_no_item(self):
        """Test ItemPage.from_entity_uri with non-existent item."""
        repo = self.get_repo()
        entity_uri = 'http://www.wikidata.org/entity/Q999999999999999999'
        regex = r"^Page .+ doesn't exist\.$"
        with self.assertRaisesRegex(pywikibot.NoPage, regex):
            ItemPage.from_entity_uri(repo, entity_uri)

    def test_from_entity_uri_no_item_lazy(self):
        """Test ItemPage.from_entity_uri with lazy loaded non-existent item."""
        repo = self.get_repo()
        entity_uri = 'http://www.wikidata.org/entity/Q999999999999999999'
        expected_item = ItemPage(repo, 'Q999999999999999999')
        self.assertEqual(
            ItemPage.from_entity_uri(repo, entity_uri, lazy_load=True),
            expected_item)

        self.assertFalse(expected_item.exists())  # ensure actually missing


class TestRedirects(WikidataTestCase):

    """Test redirect and non-redirect items."""

    def test_normal_item(self):
        """Test normal item."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q1')
        self.assertFalse(item.isRedirectPage())
        self.assertTrue(item.exists())
        regex = r'^Page .+ is not a redirect page\.$'
        self.assertRaisesRegex(pywikibot.IsNotRedirectPage, regex,
                               item.getRedirectTarget)

    def test_redirect_item(self):
        """Test redirect item."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q10008448')
        item.get(get_redirect=True)
        target = ItemPage(wikidata, 'Q8422626')
        # tests after get operation
        self.assertTrue(item.isRedirectPage())
        self.assertTrue(item.exists())
        self.assertEqual(item.getRedirectTarget(), target)
        self.assertIsInstance(item.getRedirectTarget(), ItemPage)
        regex = r'^Page .+ is a redirect page\.$'
        self.assertRaisesRegex(pywikibot.IsRedirectPage, regex, item.get)

    def test_redirect_item_without_get(self):
        """Test redirect item without explicit get operation."""
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q10008448')
        self.assertTrue(item.exists())
        self.assertTrue(item.isRedirectPage())
        target = pywikibot.ItemPage(wikidata, 'Q8422626')
        self.assertEqual(item.getRedirectTarget(), target)


class TestPropertyPage(WikidataTestCase):

    """Test PropertyPage."""

    def test_property_empty_property(self):
        """Test creating a PropertyPage without a title and datatype."""
        wikidata = self.get_repo()
        regex = r'^"datatype" is required for new property\.$'
        with self.assertRaisesRegex(TypeError, regex):
            PropertyPage(wikidata)

    def test_property_empty_title(self):
        """Test creating a PropertyPage without a title."""
        wikidata = self.get_repo()
        regex = r"^Property's title cannot be empty$"
        with self.assertRaisesRegex(pywikibot.InvalidTitle, regex):
            PropertyPage(wikidata, title='')

    @suppress_warnings('pywikibot.page.Property.getType is deprecated')
    def test_globe_coordinate(self):
        """Test a coordinate PropertyPage has the correct type."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P625')
        self.assertEqual(property_page.type, 'globe-coordinate')
        self.assertEqual(property_page.getType(), 'globecoordinate')

        claim = pywikibot.Claim(wikidata, 'P625')
        self.assertEqual(claim.type, 'globe-coordinate')
        self.assertEqual(claim.getType(), 'globecoordinate')

    def test_get(self):
        """Test PropertyPage.get() method."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P625')
        property_page.get()
        self.assertEqual(property_page.type, 'globe-coordinate')

    def test_new_claim(self):
        """Test that PropertyPage.newClaim uses cached datatype."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P625')
        property_page.get()
        claim = property_page.newClaim()
        self.assertEqual(claim.type, 'globe-coordinate')

        # Now verify that it isn't fetching the type from the property
        # data in the repo by setting the cache to the incorrect type
        # and checking that it is the cached value that is used.
        property_page._type = 'wikibase-item'
        claim = property_page.newClaim()
        self.assertEqual(claim.type, 'wikibase-item')

    def test_as_target(self):
        """Test that PropertyPage can be used as a value."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P1687')
        claim = property_page.newClaim()
        claim.setTarget(property_page)
        self.assertEqual(claim.type, 'wikibase-property')
        self.assertEqual(claim.target, property_page)


class TestClaim(WikidataTestCase):

    """Test Claim object functionality."""

    def test_claim_eq_simple(self):
        """
        Test comparing two claims.

        If they have the same property and value, they are equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        self.assertEqual(claim1, claim2)
        self.assertEqual(claim2, claim1)

    def test_claim_eq_simple_different_value(self):
        """
        Test comparing two claims.

        If they have the same property and different values,
        they are not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q1'))
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_simple_different_rank(self):
        """
        Test comparing two claims.

        If they have the same property and value and different ranks,
        they are equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim1.setRank('preferred')
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        self.assertEqual(claim1, claim2)
        self.assertEqual(claim2, claim1)

    def test_claim_eq_simple_different_snaktype(self):
        """
        Test comparing two claims.

        If they have the same property and different snaktypes,
        they are not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setSnakType('novalue')
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_simple_different_property(self):
        """
        Test comparing two claims.

        If they have the same value and different properties,
        they are not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim2 = pywikibot.Claim(wikidata, 'P21')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_with_qualifiers(self):
        """
        Test comparing two claims.

        If they have the same property, value and qualifiers, they are equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier1 = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier1.setTarget('foo')
        claim1.addQualifier(qualifier1)
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier2 = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier2.setTarget('foo')
        claim2.addQualifier(qualifier2)
        self.assertEqual(claim1, claim2)
        self.assertEqual(claim2, claim1)

    def test_claim_eq_with_different_qualifiers(self):
        """
        Test comparing two claims.

        If they have the same property and value and different qualifiers,
        they are not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier1 = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier1.setTarget('foo')
        claim1.addQualifier(qualifier1)
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier2 = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier2.setTarget('bar')
        claim2.addQualifier(qualifier2)
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_one_without_qualifiers(self):
        """
        Test comparing two claims.

        If they have the same property and value and one of them has
        no qualifiers while the other one does, they are not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier.setTarget('foo')
        claim1.addQualifier(qualifier)
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_with_different_sources(self):
        """
        Test comparing two claims.

        If they have the same property and value and different sources,
        they are equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        source1 = pywikibot.Claim(wikidata, 'P143', is_reference=True)
        source1.setTarget(pywikibot.ItemPage(wikidata, 'Q328'))
        claim1.addSource(source1)
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        source2 = pywikibot.Claim(wikidata, 'P143', is_reference=True)
        source2.setTarget(pywikibot.ItemPage(wikidata, 'Q48183'))
        claim2.addSource(source2)
        self.assertEqual(claim1, claim2)
        self.assertEqual(claim2, claim1)

    def test_claim_copy_is_equal(self):
        """
        Test making a copy of a claim.

        The copy of a claim should be always equal to the claim.
        """
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P31')
        claim.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier.setTarget('foo')
        source = pywikibot.Claim(wikidata, 'P143', is_reference=True)
        source.setTarget(pywikibot.ItemPage(wikidata, 'Q328'))
        claim.addQualifier(qualifier)
        claim.addSource(source)
        copy = claim.copy()
        self.assertEqual(claim, copy)

    def test_claim_copy_is_equal_qualifier(self):
        """
        Test making a copy of a claim.

        The copy of a qualifier should be always equal to the qualifier.
        """
        wikidata = self.get_repo()
        qualifier = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier.setTarget('foo')
        copy = qualifier.copy()
        self.assertEqual(qualifier, copy)
        self.assertTrue(qualifier.isQualifier)
        self.assertTrue(copy.isQualifier)

    def test_claim_copy_is_equal_source(self):
        """
        Test making a copy of a claim.

        The copy of a source should be always equal to the source.
        """
        wikidata = self.get_repo()
        source = pywikibot.Claim(wikidata, 'P143', is_reference=True)
        source.setTarget(pywikibot.ItemPage(wikidata, 'Q328'))
        copy = source.copy()
        self.assertEqual(source, copy)
        self.assertTrue(source.isReference)
        self.assertTrue(copy.isReference)


class TestClaimSetValue(WikidataTestCase):

    """Test setting claim values."""

    def test_set_website(self):
        """Test setting claim of url type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P856')
        self.assertEqual(claim.type, 'url')
        claim.setTarget('https://en.wikipedia.org/')
        self.assertEqual(claim.target, 'https://en.wikipedia.org/')

    def test_set_WbMonolingualText(self):
        """Test setting claim of monolingualtext type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P1450')
        self.assertEqual(claim.type, 'monolingualtext')
        target = pywikibot.WbMonolingualText(text='Test this!', language='en')
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_WbQuantity(self):
        """Test setting claim of quantity type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P1106')
        self.assertEqual(claim.type, 'quantity')
        target = pywikibot.WbQuantity(
            amount=1234, error=1, unit='http://www.wikidata.org/entity/Q11573')
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_math(self):
        """Test setting claim of math type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P2535')
        self.assertEqual(claim.type, 'math')
        claim.setTarget('a^2 + b^2 = c^2')
        self.assertEqual(claim.target, 'a^2 + b^2 = c^2')

    def test_set_identifier(self):
        """Test setting claim of external-id type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P214')
        self.assertEqual(claim.type, 'external-id')
        claim.setTarget('Any string is a valid identifier')
        self.assertEqual(claim.target, 'Any string is a valid identifier')

    def test_set_date(self):
        """Test setting claim of time type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P569')
        self.assertEqual(claim.type, 'time')
        claim.setTarget(pywikibot.WbTime(
            year=2001, month=1, day=1, site=wikidata))
        self.assertEqual(claim.target.year, 2001)
        self.assertEqual(claim.target.month, 1)
        self.assertEqual(claim.target.day, 1)

    def test_set_incorrect_target_value(self):
        """Test setting claim of the incorrect value."""
        wikidata = self.get_repo()
        date_claim = pywikibot.Claim(wikidata, 'P569')
        regex = r' is not type .+\.$'
        with self.assertRaisesRegex(ValueError, regex):
            date_claim.setTarget('foo')
        url_claim = pywikibot.Claim(wikidata, 'P856')
        with self.assertRaisesRegex(ValueError, regex):
            url_claim.setTarget(pywikibot.WbTime(2001, site=wikidata))
        mono_claim = pywikibot.Claim(wikidata, 'P1450')
        with self.assertRaisesRegex(ValueError, regex):
            mono_claim.setTarget('foo')
        quantity_claim = pywikibot.Claim(wikidata, 'P1106')
        with self.assertRaisesRegex(ValueError, regex):
            quantity_claim.setTarget('foo')


class TestItemBasePageMethods(WikidataTestCase, BasePageMethodsTestBase):

    """Test behavior of ItemPage methods inherited from BasePage."""

    def setUp(self):
        """Setup tests."""
        self._page = ItemPage(self.get_repo(), 'Q60')
        super().setUp()

    def test_basepage_methods(self):
        """Test ItemPage methods inherited from superclass BasePage."""
        self._test_invoke()
        self._test_no_wikitext()

    def test_item_is_hashable(self):
        """Ensure that ItemPages are hashable."""
        list_of_dupes = [self._page, self._page]
        self.assertLength(set(list_of_dupes), 1)


class TestPageMethodsWithItemTitle(WikidataTestCase, BasePageMethodsTestBase):

    """Test behavior of Page methods for wikibase item."""

    def setUp(self):
        """Setup tests."""
        self._page = pywikibot.Page(self.site, 'Q60')
        super().setUp()

    def test_basepage_methods(self):
        """Test Page methods inherited from superclass BasePage with Q60."""
        self._test_invoke()
        self._test_no_wikitext()


class TestLinks(WikidataTestCase):

    """Test cases to test links stored in Wikidata.

    Uses a stored data file for the wikibase item.
    However wikibase creates site objects for each sitelink, and the unit test
    directly creates a Site for 'wikipedia:af' to use in a comparison.
    """

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
        'afwiki': {
            'family': 'wikipedia',
            'code': 'af',
        }
    }

    def setUp(self):
        """Setup Tests."""
        super().setUp()
        self.wdp = ItemPage(self.get_repo(), 'Q60')
        self.wdp.id = 'Q60'
        with open(join_pages_path('Q60_only_sitelinks.wd')) as f:
            self.wdp._content = json.load(f)
        self.wdp.get()

    def test_iterlinks_page_object(self):
        """Test iterlinks for page objects."""
        page = [pg for pg in self.wdp.iterlinks() if pg.site.code == 'af'][0]
        self.assertEqual(page, pywikibot.Page(self.get_site('afwiki'),
                         'New York Stad'))

    def test_iterlinks_filtering(self):
        """Test iterlinks for a given family."""
        wikilinks = list(self.wdp.iterlinks('wikipedia'))
        wvlinks = list(self.wdp.iterlinks('wikivoyage'))

        self.assertLength(wikilinks, 3)
        self.assertLength(wvlinks, 2)


class DataCollectionTestCase(WikidataTestCase):

    """Test case for a Wikibase collection class."""

    collection_class = None

    def _test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        cls = self.collection_class
        result = cls.new_empty(self.get_repo())
        self.assertIsEmpty(result)


class TestLanguageDict(DataCollectionTestCase):

    """Test cases covering LanguageDict methods."""

    collection_class = LanguageDict

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.site = self.get_site()
        self.lang_out = {'en': 'foo'}

    def test_init(self):
        """Test LanguageDict initializer."""
        ld = LanguageDict()
        self.assertLength(ld, 0)
        ld = LanguageDict(self.lang_out)
        self.assertLength(ld, 1)

    def test_setitem(self):
        """Test LanguageDict.__setitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        self.assertIn('en', ld)
        ld[self.site] = 'bar'
        self.assertIn('en', ld)

    def test_getitem(self):
        """Test LanguageDict.__getitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        self.assertEqual(ld['en'], 'foo')
        self.assertEqual(ld[self.site], 'foo')
        self.assertIsNone(ld.get('de'))

    def test_delitem(self):
        """Test LanguageDict.__delitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        ld.pop(self.site)
        self.assertNotIn('en', ld)
        self.assertLength(ld, 0)

    def test_fromJSON(self):
        """Test LanguageDict.fromJSON method."""
        ld = LanguageDict.fromJSON({'en': {'language': 'en', 'value': 'foo'}})
        self.assertIsInstance(ld, LanguageDict)
        self.assertEqual(ld, LanguageDict(self.lang_out))

    def test_toJSON(self):
        """Test LanguageDict.toJSON method."""
        ld = LanguageDict()
        self.assertEqual(ld.toJSON(), {})
        ld = LanguageDict(self.lang_out)
        self.assertEqual(
            ld.toJSON(), {'en': {'language': 'en', 'value': 'foo'}})

    def test_toJSON_diffto(self):
        """Test LanguageDict.toJSON method."""
        ld = LanguageDict({'de': 'foo'})
        diffto = {
            'de': {'language': 'de', 'value': 'bar'},
            'en': {'language': 'en', 'value': 'foo'}}
        self.assertEqual(
            ld.toJSON(diffto=diffto),
            {'de': {'language': 'de', 'value': 'foo'},
             'en': {'language': 'en', 'value': ''}})

    def test_normalizeData(self):
        """Test LanguageDict.normalizeData method."""
        self.assertEqual(
            LanguageDict.normalizeData(self.lang_out),
            {'en': {'language': 'en', 'value': 'foo'}})

    def test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestAliasesDict(DataCollectionTestCase):

    """Test cases covering AliasesDict methods."""

    collection_class = AliasesDict

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.site = self.get_site()
        self.lang_out = {'en': ['foo', 'bar']}

    def test_init(self):
        """Test AliasesDict initializer."""
        ad = AliasesDict()
        self.assertLength(ad, 0)
        ad = AliasesDict(self.lang_out)
        self.assertLength(ad, 1)

    def test_setitem(self):
        """Test AliasesDict.__setitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        self.assertIn('en', ad)
        ad[self.site] = ['baz']
        self.assertIn('en', ad)

    def test_getitem(self):
        """Test AliasesDict.__getitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        self.assertEqual(ad['en'], ['foo', 'bar'])
        self.assertEqual(ad[self.site], ['foo', 'bar'])
        self.assertIsNone(ad.get('de'))

    def test_delitem(self):
        """Test AliasesDict.__delitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        ad.pop(self.site)
        self.assertNotIn('en', ad)
        self.assertLength(ad, 0)

    def test_fromJSON(self):
        """Test AliasesDict.fromJSON method."""
        ad = AliasesDict.fromJSON({'en': [
            {'language': 'en', 'value': 'foo'},
            {'language': 'en', 'value': 'bar'}]})
        self.assertIsInstance(ad, AliasesDict)
        self.assertEqual(ad, AliasesDict(self.lang_out))

    def test_toJSON(self):
        """Test AliasesDict.toJSON method."""
        ad = AliasesDict()
        self.assertEqual(ad.toJSON(), {})
        ad = AliasesDict(self.lang_out)
        self.assertEqual(ad.toJSON(), {'en': [
            {'language': 'en', 'value': 'foo'},
            {'language': 'en', 'value': 'bar'},
        ]})

    def test_toJSON_diffto(self):
        """Test AliasesDict.toJSON method."""
        ad = AliasesDict(self.lang_out)
        diffto = {
            'de': [
                {'language': 'de', 'value': 'foo'},
                {'language': 'de', 'value': 'bar'},
            ],
            'en': [
                {'language': 'en', 'value': 'foo'},
                {'language': 'en', 'value': 'baz'},
            ]}
        self.assertEqual(
            ad.toJSON(diffto=diffto),
            {'de': [{'language': 'de', 'value': 'foo', 'remove': ''},
                    {'language': 'de', 'value': 'bar', 'remove': ''}],
             'en': [{'language': 'en', 'value': 'foo'},
                    {'language': 'en', 'value': 'bar'}]})

    def test_normalizeData(self):
        """Test AliasesDict.normalizeData method."""
        data_in = {'en': [
            {'language': 'en', 'value': 'foo'},
            'bar',
            {'language': 'en', 'value': 'baz', 'remove': ''},
        ]}
        data_out = {'en': [
            {'language': 'en', 'value': 'foo'},
            {'language': 'en', 'value': 'bar'},
            {'language': 'en', 'value': 'baz', 'remove': ''},
        ]}
        self.assertEqual(AliasesDict.normalizeData(data_in), data_out)

    def test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestClaimCollection(DataCollectionTestCase):

    """Test cases covering ClaimCollection methods."""

    collection_class = ClaimCollection

    def test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestSiteLinkCollection(DataCollectionTestCase):

    """Test cases covering SiteLinkCollection methods."""

    collection_class = SiteLinkCollection

    def test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestWriteNormalizeData(TestCase):

    """Test cases for routines that normalize data for writing to Wikidata.

    Exercises ItemPage._normalizeData with data that is not normalized
    and data which is already normalized.
    """

    net = False

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.data_out = {
            'labels': {'en': {'language': 'en', 'value': 'Foo'}},
            'descriptions': {'en': {'language': 'en', 'value': 'Desc'}},
            'aliases': {'en': [
                {'language': 'en', 'value': 'Bah'},
                {'language': 'en', 'value': 'Bar', 'remove': ''},
            ]},
        }

    def test_normalize_data(self):
        """Test _normalizeData() method."""
        data_in = {
            'labels': {'en': 'Foo'},
            'descriptions': {'en': 'Desc'},
            'aliases': {'en': [
                'Bah',
                {'language': 'en', 'value': 'Bar', 'remove': ''},
            ]},
        }

        response = ItemPage._normalizeData(data_in)
        self.assertEqual(response, self.data_out)

    def test_normalized_data(self):
        """Test _normalizeData() method for normalized data."""
        response = ItemPage._normalizeData(
            copy.deepcopy(self.data_out))
        self.assertEqual(response, self.data_out)


class TestPreloadingEntityGenerator(TestCase):

    """Test preloading item generator."""

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        }
    }

    def test_non_item_gen(self):
        """Test PreloadingEntityGenerator with getReferences()."""
        site = self.get_site('wikidata')
        page = pywikibot.Page(site, 'Property:P31')
        ref_gen = page.getReferences(follow_redirects=False, total=5)
        gen = pagegenerators.PreloadingEntityGenerator(ref_gen)
        self.assertTrue(all(isinstance(item, ItemPage) for item in gen))

    def test_foreign_page_item_gen(self):
        """Test PreloadingEntityGenerator with connected pages."""
        site = self.get_site('enwiki')
        page_gen = [pywikibot.Page(site, 'Main Page'),
                    pywikibot.Page(site, 'New York City')]
        gen = pagegenerators.PreloadingEntityGenerator(page_gen)
        self.assertTrue(all(isinstance(item, ItemPage) for item in gen))


class TestNamespaces(WikidataTestCase):

    """Test cases to test namespaces of Wikibase entities."""

    def test_empty_wikibase_page(self):
        """
        Test empty wikibase page.

        As a base class it should be able to instantiate
        it with minimal arguments
        """
        wikidata = self.get_repo()
        page = WikibasePage(wikidata)
        regex = r' object has no attribute '
        self.assertRaisesRegex(AttributeError, regex, page.namespace)
        page = WikibasePage(wikidata, title='')
        self.assertRaisesRegex(AttributeError, regex, page.namespace)

        page = WikibasePage(wikidata, ns=0)
        self.assertEqual(page.namespace(), 0)
        page = WikibasePage(wikidata, entity_type='item')
        self.assertEqual(page.namespace(), 0)

        page = WikibasePage(wikidata, ns=120)
        self.assertEqual(page.namespace(), 120)
        page = WikibasePage(wikidata, title='', ns=120)
        self.assertEqual(page.namespace(), 120)
        page = WikibasePage(wikidata, entity_type='property')
        self.assertEqual(page.namespace(), 120)

        # mismatch in namespaces
        regex = r'^Namespace ".+" is not valid for Wikibase entity type ".+"$'
        with self.assertRaisesRegex(ValueError, regex):
            WikibasePage(wikidata, ns=0, entity_type='property')
        with self.assertRaisesRegex(ValueError, regex):
            WikibasePage(wikidata, ns=120, entity_type='item')

    def test_wikibase_link_namespace(self):
        """Test the title resolved to a namespace correctly."""
        wikidata = self.get_repo()
        # title without any namespace clues (ns or entity_type)
        # should verify the Link namespace is appropriate
        page = WikibasePage(wikidata, title='Q6')
        self.assertEqual(page.namespace(), 0)
        page = WikibasePage(wikidata, title='Property:P60')
        self.assertEqual(page.namespace(), 120)

    def test_wikibase_namespace_selection(self):
        """Test various ways to correctly specify the namespace."""
        wikidata = self.get_repo()

        page = ItemPage(wikidata, 'Q60')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = ItemPage(wikidata, title='Q60')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = WikibasePage(wikidata, title='Q60', ns=0)
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = WikibasePage(wikidata, title='Q60',
                            entity_type='item')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = PropertyPage(wikidata, 'Property:P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = PropertyPage(wikidata, 'P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = WikibasePage(wikidata, title='Property:P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = WikibasePage(wikidata, title='P6', ns=120)
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = WikibasePage(wikidata, title='P6',
                            entity_type='property')
        self.assertEqual(page.namespace(), 120)
        page.get()

    def test_wrong_namespaces(self):
        """Test incorrect namespaces for Wikibase entities."""
        wikidata = self.get_repo()
        # All subclasses of WikibasePage raise a ValueError
        # if the namespace for the page title is not correct
        regex = r': Namespace ".+" is not valid$'
        with self.assertRaisesRegex(ValueError, regex):
            WikibasePage(wikidata, title='Wikidata:Main Page')
        regex = r"^'.+' is not in the namespace "
        with self.assertRaisesRegex(ValueError, regex):
            ItemPage(wikidata, 'File:Q1')
        with self.assertRaisesRegex(ValueError, regex):
            PropertyPage(wikidata, 'File:P60')

    def test_item_unknown_namespace(self):
        """Test unknown namespaces for Wikibase entities."""
        # The 'Invalid:' is not a known namespace, so is parsed to be
        # part of the title in namespace 0
        # TODO: These items have inappropriate titles, which should
        #       raise an error.
        wikidata = self.get_repo()
        regex = r"^'.+' is not a valid item page title$"
        with self.assertRaisesRegex(pywikibot.InvalidTitle, regex):
            ItemPage(wikidata, 'Invalid:Q1')


class TestAlternateNamespaces(WikidataTestCase):

    """Test cases to test namespaces of Wikibase entities."""

    cached = False
    dry = True

    @classmethod
    def setUpClass(cls):
        """Setup test class."""
        super().setUpClass()

        cls.get_repo()._namespaces = NamespacesDict({
            90: Namespace(id=90,
                          case='first-letter',
                          canonical_name='Item',
                          defaultcontentmodel='wikibase-item'),
            92: Namespace(id=92,
                          case='first-letter',
                          canonical_name='Prop',
                          defaultcontentmodel='wikibase-property')
        })

    def test_alternate_item_namespace(self):
        """Test alternate item namespace."""
        item = ItemPage(self.repo, 'Q60')
        self.assertEqual(item.namespace(), 90)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.title(), 'Item:Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})

        item = ItemPage(self.repo, 'Item:Q60')
        self.assertEqual(item.namespace(), 90)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.title(), 'Item:Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})

    def test_alternate_property_namespace(self):
        """Test alternate property namespace."""
        prop = PropertyPage(self.repo, 'P21')
        self.assertEqual(prop.namespace(), 92)
        self.assertEqual(prop.id, 'P21')
        self.assertEqual(prop.title(), 'Prop:P21')
        self.assertEqual(prop._defined_by(), {'ids': 'P21'})

        prop = PropertyPage(self.repo, 'Prop:P21')
        self.assertEqual(prop.namespace(), 92)
        self.assertEqual(prop.id, 'P21')
        self.assertEqual(prop.title(), 'Prop:P21')
        self.assertEqual(prop._defined_by(), {'ids': 'P21'})


class TestOwnClient(TestCase):

    """Test that a data repository family can be its own client."""

    sites = {
        # The main Wikidata is its own client.
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
        # test.wikidata is also
        'wikidatatest': {
            'family': 'wikidata',
            'code': 'test',
        },
    }

    def test_own_client(self, key):
        """Test that a data repository family can be its own client."""
        site = self.get_site(key)

        page = pywikibot.Page(site, 'Wikidata:Main Page')
        item = ItemPage.fromPage(page)
        self.assertEqual(item.site, site)

    def test_page_from_repository_fails(self, key):
        """Test that page_from_repository method fails."""
        site = self.get_site(key)
        dummy_item = 'Q1'
        regex = r'^page_from_repository method is not implemented ' + \
                r'for Wikibase .+\.$'
        with self.assertRaisesRegex(NotImplementedError, regex):
            site.page_from_repository(dummy_item)


class TestUnconnectedClient(TestCase):

    """Test clients not connected to a data repository."""

    sites = {
        # Wikispecies is not supported by Wikidata yet.
        'species': {
            'family': 'species',
            'code': 'species',
            'page_title': 'Main Page',
        },
        # fr.wiktionary is not supported by Wikidata yet.
        'frwikt': {
            'family': 'wiktionary',
            'code': 'fr',
            'page_title': 'and',
        },
    }

    dry = True

    def test_not_supported_family(self, key):
        """Test that family without a data repository causes error."""
        site = self.get_site(key)

        self.wdp = pywikibot.Page(site, self.sites[key]['page_title'])
        regex = r' has no data repository$'
        with self.assertRaisesRegex(pywikibot.WikiBaseError, regex):
            ItemPage.fromPage(self.wdp)
        self.assertRaisesRegex(pywikibot.WikiBaseError, regex,
                               self.wdp.data_item)

    def test_has_data_repository(self, key):
        """Test that site has no data repository."""
        site = self.get_site(key)
        self.assertFalse(site.has_data_repository)

    def test_page_from_repository_fails(self, key):
        """Test that page_from_repository method fails."""
        site = self.get_site(key)
        dummy_item = 'Q1'
        regex = r'^Wikibase is not implemented for .+\.$'
        with self.assertRaisesRegex(pywikibot.UnknownExtension, regex):
            site.page_from_repository(dummy_item)


class TestJSON(WikidataTestCase):

    """Test cases to test toJSON() functions."""

    dry = True

    def setUp(self):
        """Setup test."""
        super().setUp()
        wikidata = self.get_repo()
        self.wdp = ItemPage(wikidata, 'Q60')
        self.wdp.id = 'Q60'
        with open(join_pages_path('Q60.wd')) as f:
            self.wdp._content = json.load(f)
        self.wdp.get()
        del self.wdp._content['id']
        del self.wdp._content['type']
        del self.wdp._content['lastrevid']
        del self.wdp._content['pageid']

    def test_itempage_json(self):
        """Test itempage json."""
        old = json.dumps(self.wdp._content, indent=2, sort_keys=True)
        new = json.dumps(self.wdp.toJSON(), indent=2, sort_keys=True)

        self.assertEqual(old, new)

    def test_json_diff(self):
        """Test json diff."""
        del self.wdp.labels['en']
        self.wdp.aliases['de'].append('New York')
        self.wdp.aliases['de'].append('foo')
        self.wdp.aliases['de'].remove('NYC')
        del self.wdp.aliases['nl']
        del self.wdp.claims['P213']
        del self.wdp.sitelinks['afwiki']
        self.wdp.sitelinks['nlwiki']._badges = set()
        expected = {
            'labels': {
                'en': {
                    'language': 'en',
                    'value': ''
                }
            },
            'aliases': {
                'de': [
                    {'language': 'de', 'value': 'City of New York'},
                    {'language': 'de', 'value': 'The Big Apple'},
                    {'language': 'de', 'value': 'New York'},
                    {'language': 'de', 'value': 'New York'},
                    {'language': 'de', 'value': 'foo'},
                ],
                'nl': [
                    {'language': 'nl', 'value': 'New York', 'remove': ''},
                ],
            },
            'claims': {
                'P213': [
                    {
                        'id': 'Q60$0427a236-4120-7d00-fa3e-e23548d4c02d',
                        'remove': ''
                    }
                ]
            },
            'sitelinks': {
                'afwiki': {
                    'site': 'afwiki',
                    'title': '',
                },
                'nlwiki': {
                    'site': 'nlwiki',
                    'title': 'New York City',
                    'badges': ['']
                }
            }
        }
        diff = self.wdp.toJSON(diffto=self.wdp._content)
        self.assertEqual(diff, expected)


class TestDeprecatedDataSiteMethods(WikidataTestCase, DeprecationTestCase):

    """Test deprecated DataSite get_* methods."""

    cached = True

    def test_get_info(self):
        """Test get_info."""
        data = self.repo.get_info(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('title', data)
        self.assertEqual(data['title'], 'Q60')

    def test_get_labels(self):
        """Test get_labels."""
        data = self.repo.get_labels(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)

    def test_get_aliases(self):
        """Test get_aliases."""
        data = self.repo.get_aliases(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('fr', data)  # T170073

    def test_get_descriptions(self):
        """Test get_descriptions."""
        data = self.repo.get_descriptions(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)

    def test_get_sitelinks(self):
        """Test get_sitelinks."""
        data = self.repo.get_sitelinks(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('enwiki', data)

    def test_get_urls(self):
        """Test get_urls."""
        data = self.repo.get_urls(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('enwiki', data)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
