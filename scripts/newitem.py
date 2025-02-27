#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script creates new items on Wikidata based on certain criteria.

* When was the (Wikipedia) page created?
* When was the last edit on the page?
* Does the page contain interwikis?

This script understands various command-line arguments:

-lastedit         The minimum number of days that has passed since the page was
                  last edited.

-pageage          The minimum number of days that has passed since the page was
                  created.

-touch            Do a null edit on every page which has a wikibase item.
                  Be careful, this option can trigger edit rates or captchas
                  if your account is not autoconfirmed.

"""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
from datetime import timedelta
from textwrap import fill

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import NoRedirectPageBot, WikidataBot
from pywikibot.exceptions import (LockedPage, NoCreateError, NoPage,
                                  PageNotSaved)
from pywikibot.tools import PYTHON_VERSION

if PYTHON_VERSION >= (3, 9):
    Set = set
else:
    from typing import Set


DELETION_TEMPLATES = ('Q4847311', 'Q6687153', 'Q21528265')


class NewItemRobot(WikidataBot, NoRedirectPageBot):

    """A bot to create new items."""

    treat_missing_item = True

    def __init__(self, generator, **kwargs) -> None:
        """Only accepts options defined in available_options."""
        self.available_options.update({
            'always': True,
            'lastedit': 7,
            'pageage': 21,
            'touch': 'newly',  # Can be False, newly (pages linked to newly
                               # created items) or True (touch all pages)
        })

        super().__init__(**kwargs)
        self.generator = generator
        self._skipping_templates = {}

    def setup(self) -> None:
        """Setup ages."""
        super().setup()

        self.pageAgeBefore = self.repo.server_time() - timedelta(
            days=self.opt.pageage)
        self.lastEditBefore = self.repo.server_time() - timedelta(
            days=self.opt.lastedit)
        pywikibot.output('Page age is set to {} days so only pages created'
                         '\nbefore {} will be considered.\n'
                         .format(self.opt.pageage,
                                 self.pageAgeBefore.isoformat()))
        pywikibot.output(
            'Last edit is set to {} days so only pages last edited'
            '\nbefore {} will be considered.\n'
            .format(self.opt.lastedit, self.lastEditBefore.isoformat()))

    @staticmethod
    def _touch_page(page) -> None:
        try:
            pywikibot.output('Doing a null edit on the page.')
            page.touch()
        except (NoCreateError, NoPage):
            pywikibot.error('Page {0} does not exist.'.format(
                page.title(as_link=True)))
        except LockedPage:
            pywikibot.error('Page {0} is locked.'.format(
                page.title(as_link=True)))
        except PageNotSaved:
            pywikibot.error('Page {0} not saved.'.format(
                page.title(as_link=True)))

    def _callback(self, page, exc) -> None:
        if exc is None and self.opt.touch:
            self._touch_page(page)

    def get_skipping_templates(self, site) -> Set[pywikibot.Page]:
        """Get templates which leads the page to be skipped.

        If the script is used for multiple sites, hold the skipping templates
        as attribute.
        """
        if site in self._skipping_templates:
            return self._skipping_templates[site]

        skipping_templates = set()
        pywikibot.output('Retrieving skipping templates for site {}...'
                         .format(site))
        for item in DELETION_TEMPLATES:
            template = site.page_from_repository(item)

            if template is None:
                continue

            skipping_templates.add(template)
            # also add redirect templates
            skipping_templates.update(
                template.getReferences(follow_redirects=False,
                                       with_template_inclusion=False,
                                       filter_redirects=True,
                                       namespaces=site.namespaces.TEMPLATE))
        self._skipping_templates[site] = skipping_templates
        return skipping_templates

    def skip_templates(self, page) -> str:
        """Check whether the page is to be skipped due to skipping template.

        @param page: treated page
        @type page: pywikibot.Page
        @return: the template which leads to skip
        """
        skipping_templates = self.get_skipping_templates(page.site)
        for template, _ in page.templatesWithParams():
            if template in skipping_templates:
                return template.title(with_ns=False)
        return ''

    def skip_page(self, page) -> bool:
        """Skip pages which are unwanted to treat."""
        if page.editTime() > self.lastEditBefore:
            pywikibot.output(
                'Last edit on {page} was on {page.latest_revision.timestamp}.'
                '\nToo recent. Skipping.'.format(page=page))
            return True

        if page.oldest_revision.timestamp > self.pageAgeBefore:
            pywikibot.output(
                'Page creation of {page} on {page.oldest_revision.timestamp} '
                'is too recent. Skipping.'.format(page=page))
            return True

        if page.isCategoryRedirect():
            pywikibot.output('{} is a category redirect. Skipping.'
                             .format(page))
            return True

        if page.langlinks():
            # FIXME: Implement this
            pywikibot.output(
                'Found language links (interwiki links) for {}.\n'
                "Haven't implemented that yet so skipping."
                .format(page))
            return True

        template = self.skip_templates(page)
        if template:
            pywikibot.output('%s contains {{%s}}. Skipping.'
                             % (page, template))
            return True

        return super(NewItemRobot, self).skip_page(page)

    def treat_page_and_item(self, page, item) -> None:
        """Treat page/item."""
        if item and item.exists():
            pywikibot.output('{0} already has an item: {1}.'
                             .format(page, item))
            if self.opt.touch is True:
                self._touch_page(page)
            return

        self.create_item_for_page(
            page, callback=lambda _, exc: self._callback(page, exc))


def main(*args) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen = pagegenerators.GeneratorFactory()

    options = {}
    for arg in local_args:
        if arg.startswith(('-pageage:', '-lastedit:')):
            key, val = arg.split(':', 1)
            options[key[1:]] = int(val)
        elif gen.handleArg(arg):
            pass
        else:
            options[arg[1:].lower()] = True

    generator = gen.getCombinedGenerator(preload=True)
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return

    bot = NewItemRobot(generator, **options)
    if not bot.site.logged_in():
        bot.site.login()
    user = pywikibot.User(bot.site, bot.site.username())
    if bot.opt.touch == 'newly' and 'autoconfirmed' not in user.groups():
        pywikibot.warning(fill(
            'You are logged in as {}, an account that is '
            'not in the autoconfirmed group on {}. Script '
            'will not touch pages linked to newly created '
            'items to avoid triggering edit rates or '
            'captchas. Use -touch param to force this.'
            .format(user.username, bot.site.sitename)))
        bot.opt.touch = False
    bot.run()


if __name__ == '__main__':
    main()
