# -*- coding: utf-8 -*-
"""Tests for the User page."""
#
# (C) Pywikibot team, 2016-2020
#
# Distributed under the terms of the MIT license.
#
from contextlib import suppress

import pywikibot

from pywikibot import Page, Timestamp, User
from pywikibot.exceptions import AutoblockUser
from pywikibot.tools import suppress_warnings

from tests import patch
from tests.aspects import DefaultSiteTestCase, TestCase, unittest


class TestUserClass(TestCase):

    """Test User class."""

    family = 'wikipedia'
    code = 'de'

    def _tests_unregistered_user(self, user, prop='invalid'):
        """Proceed user tests."""
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(with_ns=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertFalse(user.is_thankable)
        self.assertIn(prop, user.getprops())

    def test_anonymous_user(self):
        """Test registered user."""
        user = User(self.site, '123.45.67.89')
        self._tests_unregistered_user(user)
        self.assertTrue(user.isAnonymous())

    def test_unregistered_user(self):
        """Test unregistered user."""
        user = User(self.site, 'This user name is not registered yet')
        self._tests_unregistered_user(user, prop='missing')
        self.assertFalse(user.isAnonymous())

    def test_invalid_user(self):
        """Test invalid user."""
        user = User(self.site, 'Invalid char\x9f in Name')
        self._tests_unregistered_user(user)
        self.assertFalse(user.isAnonymous())

    def test_registered_user(self):
        """Test registered user."""
        user = User(self.site, 'Xqt')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(with_ns=False), user.username)
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsInstance(user.registration(), pywikibot.Timestamp)
        self.assertGreater(user.editCount(), 0)
        self.assertFalse(user.isBlocked())
        # self.assertTrue(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('userid', user.getprops())
        self.assertEqual(user.getprops()['userid'], 287832)
        self.assertEqual(user.pageid, 6927779)
        self.assertEqual(user.getUserPage(),
                         pywikibot.Page(self.site, 'Benutzer:Xqt'))
        self.assertEqual(user.getUserPage(subpage='pwb'),
                         pywikibot.Page(self.site, 'Benutzer:Xqt/pwb'))
        self.assertEqual(user.getUserTalkPage(),
                         pywikibot.Page(self.site, 'Benutzer Diskussion:Xqt'))
        self.assertEqual(user.getUserTalkPage(subpage='pwb'),
                         pywikibot.Page(self.site,
                                        'Benutzer Diskussion:Xqt/pwb'))
        self.assertTrue(user.is_thankable)
        contribs = user.contributions(total=10)
        self.assertLength(list(contribs), 10)
        self.assertTrue(all(isinstance(contrib, tuple)
                            for contrib in contribs))
        self.assertTrue(all('user' in contrib
                            and contrib['user'] == user.username
                            for contrib in contribs))
        self.assertIn('user', user.groups())
        self.assertIn('edit', user.rights())

    def test_registered_user_without_timestamp(self):
        """Test registered user when registration timestamp is None."""
        user = User(self.site, 'Ulfb')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertIsNone(user.getprops()['registration'])
        self.assertGreater(user.editCount(), 0)
        self.assertEqual(user.gender(), 'male')
        self.assertIn('userid', user.getprops())
        self.assertTrue(user.is_thankable)

    def test_female_user(self):
        """Test female user."""
        user = User(self.site, 'Catrin')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertGreater(user.editCount(), 0)
        self.assertEqual(user.gender(), 'female')
        self.assertIn('userid', user.getprops())
        self.assertTrue(user.is_thankable)

    def test_bot_user(self):
        """Test bot user."""
        user = User(self.site, 'Xqbot')
        self.assertIn('bot', user.groups())
        self.assertFalse(user.is_thankable)

    def test_autoblocked_user(self):
        """Test autoblocked user."""
        with patch.object(pywikibot, 'output') as p:
            user = User(self.site, '#1242976')
        p.assert_called_once_with(
            'This is an autoblock ID, you can only use to unblock it.')
        self.assertEqual('#1242976', user.username)
        with suppress_warnings('pywikibot.page.User.name is deprecated'):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(with_ns=False), user.username[1:])
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertIn('invalid', user.getprops())
        self.assertTrue(user._isAutoblock)
        self.assertRaisesRegex(AutoblockUser, 'This is an autoblock ID',
                               user.getUserPage)
        self.assertRaisesRegex(AutoblockUser, 'This is an autoblock ID',
                               user.getUserTalkPage)

    def test_autoblocked_user_with_namespace(self):
        """Test autoblocked user."""
        # Suppress output: This is an autoblock ID, you can only use to unblock
        with patch.object(pywikibot, 'output'):
            user = User(self.site, 'User:#1242976')
        self.assertEqual('#1242976', user.username)
        with suppress_warnings('pywikibot.page.User.name is deprecated'):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(with_ns=False), user.username[1:])
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertIn('invalid', user.getprops())
        self.assertTrue(user._isAutoblock)
        self.assertRaisesRegex(AutoblockUser, 'This is an autoblock ID',
                               user.getUserPage)
        self.assertRaisesRegex(AutoblockUser, 'This is an autoblock ID',
                               user.getUserTalkPage)


class TestUserMethods(DefaultSiteTestCase):

    """Test User methods with bot user."""

    user = True

    def test_contribution(self):
        """Test the User.usercontribs() method."""
        mysite = self.get_site()
        user = User(mysite, mysite.user())
        uc = list(user.contributions(total=10))
        if not uc:
            self.skipTest('User {0} has no contributions on site {1}.'
                          .format(mysite.user(), mysite))
        self.assertLessEqual(len(uc), 10)
        last = uc[0]
        for contrib in uc:
            self.assertIsInstance(contrib, tuple)
            self.assertLength(contrib, 4)
            p, i, t, c = contrib
            self.assertIsInstance(p, Page)
            self.assertIsInstance(i, int)
            self.assertIsInstance(t, Timestamp)
            self.assertIsInstance(c, str)
        self.assertEqual(last, user.last_edit)

    def test_logevents(self):
        """Test the User.logevents() method."""
        mysite = self.get_site()
        user = User(mysite, mysite.user())
        le = list(user.logevents(total=10))
        if not le:
            self.skipTest('User {0} has no logevents on site {1}.'
                          .format(mysite.user(), mysite))
        self.assertLessEqual(len(le), 10)
        last = le[0]
        self.assertTrue(all(event.user() == user.username for event in le))
        self.assertEqual(last, user.last_event)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
