#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot uploads text from djvu files onto pages in the "Page" namespace.

It is intended to be used for Wikisource.

The following parameters are supported:

    -index:...     name of the index page (without the Index: prefix)
    -djvu:...      path to the djvu file, it shall be:
                   - path to a file name
                   - dir where a djvu file name as index is located
                   optional, by default is current dir '.'
    -pages:<start>-<end>,...<start>-<end>,<start>-<end>
                   Page range to upload;
                   optional, start=1, end=djvu file number of images.
                   Page ranges can be specified as:
                     A-B -> pages A until B
                     A-  -> pages A until number of images
                     A   -> just page A
                     -B  -> pages 1 until B
    -summary:      custom edit summary.
                   Use quotes if edit summary contains spaces.
    -force         overwrites existing text
                   optional, default False
    -always        don't bother asking to confirm any of the changes.

"""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
import os.path

import pywikibot

from pywikibot import i18n

from pywikibot.bot import SingleSiteBot
from pywikibot.proofreadpage import ProofreadPage
from pywikibot.tools.djvu import DjVuFile
from pywikibot.tools import PYTHON_VERSION

if PYTHON_VERSION >= (3, 9):
    Tuple = tuple
else:
    from typing import Tuple


class DjVuTextBot(SingleSiteBot):

    """
    A bot that uploads text-layer from djvu files to Page:namespace.

    Works only on sites with Proofread Page extension installed.
    """

    def __init__(self, djvu, index, pages=None, **kwargs):
        """
        Initializer.

        @param djvu: djvu from where to fetch the text layer
        @type djvu: DjVuFile object
        @param index: index page in the Index: namespace
        @type index: Page object
        @param pages: page interval to upload (start, end)
        @type pages: tuple
        """
        self.available_options.update({
            'force': False,
            'summary': None
        })
        super().__init__(site=index.site, **kwargs)
        self._djvu = djvu
        self._index = index
        self._prefix = self._index.title(with_ns=False)
        self._page_ns = self.site._proofread_page_ns.custom_name

        if not pages:
            self._pages = (1, self._djvu.number_of_images())
        else:
            self._pages = pages

        self.generator = self.gen()

        # Get edit summary message if it's empty.
        if not self.opt.summary:
            self.opt.summary = i18n.twtranslate(self._index.site,
                                                'djvutext-creating')

    def page_number_gen(self):
        """Generate pages numbers from specified page intervals."""
        last = 0
        for start, end in sorted(self._pages):
            start = max(last, start)
            last = end + 1
            yield from range(start, last)

    def gen(self):
        """Generate pages from specified page interval."""
        for page_number in self.page_number_gen():
            title = '{page_ns}:{prefix}/{number}'.format(
                page_ns=self._page_ns,
                prefix=self._prefix,
                number=page_number)
            page = ProofreadPage(self._index.site, title)
            page.page_number = page_number  # remember page number in djvu file
            yield page

    def treat(self, page):
        """Process one page."""
        old_text = page.text

        # Overwrite body of the page with content from djvu
        page.body = self._djvu.get_page(page.page_number)
        new_text = page.text

        summary = self.opt.summary
        if page.exists() and not self.opt.force:
            pywikibot.output(
                'Page {} already exists, not adding!\n'
                'Use -force option to overwrite the output page.'
                .format(page))
        else:
            self.userPut(page, old_text, new_text, summary=summary)


def main(*args: Tuple[str, ...]):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    """
    index = None
    djvu_path = '.'  # default djvu file directory
    pages = '1-'
    options = {}

    # Parse command line arguments.
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        if arg.startswith('-index:'):
            index = arg[7:]
        elif arg.startswith('-djvu:'):
            djvu_path = arg[len('-djvu:'):]
        elif arg.startswith('-pages:'):
            pages = arg[7:]
        elif arg.startswith('-summary:'):
            options['summary'] = arg[len('-summary:'):]
        elif arg == '-force':
            options['force'] = True
        elif arg == '-always':
            options['always'] = True
        else:
            pywikibot.output('Unknown argument ' + arg)

    # index is mandatory.
    if not index:
        pywikibot.bot.suggest_help(missing_parameters=['-index'])
        return

    # If djvu_path is not a file, build djvu_path from dir+index.
    djvu_path = os.path.expanduser(djvu_path)
    djvu_path = os.path.abspath(djvu_path)
    if not os.path.exists(djvu_path):
        pywikibot.error('No such file or directory: ' + djvu_path)
        return
    if os.path.isdir(djvu_path):
        djvu_path = os.path.join(djvu_path, index)

    # Check the djvu file exists and, if so, create the DjVuFile wrapper.
    djvu = DjVuFile(djvu_path)

    if not djvu.has_text():
        pywikibot.error('No text layer in djvu file {}'.format(djvu.file))
        return

    # Parse pages param.
    pages = pages.split(',')
    for interval in range(len(pages)):
        start, sep, end = pages[interval].partition('-')
        start = 1 if not start else int(start)
        if not sep:
            end = start
        else:
            end = int(end) if end else djvu.number_of_images()
        pages[interval] = (start, end)

    site = pywikibot.Site()
    if not site.has_extension('ProofreadPage'):
        pywikibot.error('Site {} must have ProofreadPage extension.'
                        .format(site))
        return

    index_page = pywikibot.Page(site, index, ns=site.proofread_index_ns)

    if not index_page.exists():
        raise pywikibot.NoPage(index)

    pywikibot.output('uploading text from {} to {}'
                     .format(djvu.file, index_page.title(as_link=True)))

    bot = DjVuTextBot(djvu, index_page, pages, **options)
    bot.run()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        pywikibot.error('Fatal error:', exc_info=True)
