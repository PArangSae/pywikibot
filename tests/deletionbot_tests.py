# -*- coding: utf-8 -*-
"""Tests for scripts/delete.py."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
from contextlib import suppress

import pywikibot
import pywikibot.page

from scripts import delete

from tests.aspects import unittest, ScriptMainTestCase
from tests.utils import empty_sites


class TestDeletionBotWrite(ScriptMainTestCase):

    """Test deletionbot script."""

    family = 'wikipedia'
    code = 'test'

    sysop = True
    write = True

    def test_delete(self):
        """Test deletionbot on the test wiki."""
        site = self.get_site()
        cat = pywikibot.Category(site, 'Pywikibot Delete Test')
        delete.main('-cat:Pywikibot_Delete_Test', '-always')
        self.assertEmpty(list(cat.members()))
        delete.main('-page:User:Unicodesnowman/DeleteTest1', '-always',
                    '-undelete', '-summary=pywikibot unit tests')
        delete.main('-page:User:Unicodesnowman/DeleteTest2', '-always',
                    '-undelete', '-summary=pywikibot unit tests')
        self.assertLength(list(cat.members()), 2)

    def test_undelete_existing(self):
        """Test undeleting an existing page."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ExistingPage')
        if not p1.exists():
            p1.text = 'pywikibot unit test page'
            p1.save('unit test', botflag=True)
        delete.main('-page:User:Unicodesnowman/ExistingPage', '-always',
                    '-undelete', '-summary=pywikibot unit tests')


class TestDeletionBotUser(ScriptMainTestCase):

    """Test deletionbot as a user (not sysop)."""

    family = 'wikipedia'
    code = 'test'

    user = True
    write = True

    def test_delete_mark(self):
        """Test marking User:Unicodesnowman/DeleteMark for deletion."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/DeleteMark')
        if not p1.exists():
            p1.text = 'foo'
            p1.save('unit test', botflag=True)
        delete.main('-page:User:Unicodesnowman/DeleteMark', '-always',
                    '-summary=pywikibot unit test. Do NOT actually delete.')
        self.assertEqual(p1.get(force=True), '{{delete|1=pywikibot unit test. '
                         'Do NOT actually delete.}}\nfoo')
        p1.text = 'foo'
        p1.save('unit test', botflag=True)


class TestDeletionBot(ScriptMainTestCase):

    """Test deletionbot with patching to make it non-write."""

    family = 'wikipedia'
    code = 'test'

    cached = True
    user = True

    delete_args = []
    undelete_args = []

    def setUp(self):
        """Set up unit test."""
        self._original_delete = pywikibot.Page.delete
        self._original_undelete = pywikibot.Page.undelete
        pywikibot.Page.delete = delete_dummy
        pywikibot.Page.undelete = undelete_dummy
        super(TestDeletionBot, self).setUp()

    def tearDown(self):
        """Tear down unit test."""
        pywikibot.Page.delete = self._original_delete
        pywikibot.Page.undelete = self._original_undelete
        super(TestDeletionBot, self).tearDown()

    def test_dry(self):
        """Test dry run of bot."""
        with empty_sites():
            delete.main('-page:Main Page', '-always', '-summary:foo')
            self.assertEqual(self.delete_args,
                             ['[[Main Page]]', 'foo', False, True, True])
        with empty_sites():
            delete.main(
                '-page:FoooOoOooO', '-always', '-summary:foo', '-undelete')
            self.assertEqual(self.undelete_args, ['[[FoooOoOooO]]', 'foo'])


def delete_dummy(self, reason, prompt, mark, quit):
    """Dummy delete method."""
    TestDeletionBot.delete_args = [self.title(as_link=True), reason, prompt,
                                   mark, quit]


def undelete_dummy(self, reason):
    """Dummy undelete method."""
    TestDeletionBot.undelete_args = [self.title(as_link=True), reason]


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
