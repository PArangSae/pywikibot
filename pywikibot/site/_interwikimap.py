# -*- coding: utf-8 -*-
"""Objects representing interwiki map of MediaWiki site."""
#
# (C) Pywikibot team, 2015-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot


class _IWEntry:

    """An entry of the _InterwikiMap with a lazy loading site."""

    def __init__(self, local, url):
        self._site = None
        self.local = local
        self.url = url

    @property
    def site(self):
        if self._site is None:
            try:
                self._site = pywikibot.Site(url=self.url)
            except Exception as e:
                self._site = e
        return self._site


class _InterwikiMap:

    """A representation of the interwiki map of a site."""

    def __init__(self, site):
        """
        Create an empty uninitialized interwiki map for the given site.

        @param site: Given site for which interwiki map is to be created
        @type site: pywikibot.site.APISite
        """
        super().__init__()
        self._site = site
        self._map = None

    def reset(self):
        """Remove all mappings to force building a new mapping."""
        self._map = None

    @property
    def _iw_sites(self):
        """Fill the interwikimap cache with the basic entries."""
        # _iw_sites is a local cache to return a APISite instance depending
        # on the interwiki prefix of that site
        if self._map is None:
            self._map = {iw['prefix']: _IWEntry('local' in iw, iw['url'])
                         for iw in self._site.siteinfo['interwikimap']}
        return self._map

    def __getitem__(self, prefix):
        """
        Return the site, locality and url for the requested prefix.

        @param prefix: Interwiki prefix
        @type prefix: Dictionary key
        @rtype: _IWEntry
        @raises KeyError: Prefix is not a key
        @raises TypeError: Site for the prefix is of wrong type
        """
        if prefix not in self._iw_sites:
            raise KeyError("'{0}' is not an interwiki prefix.".format(prefix))
        if isinstance(self._iw_sites[prefix].site, pywikibot.site.BaseSite):
            return self._iw_sites[prefix]
        elif isinstance(self._iw_sites[prefix].site, Exception):
            raise self._iw_sites[prefix].site
        else:
            raise TypeError('_iw_sites[%s] is wrong type: %s'
                            % (prefix, type(self._iw_sites[prefix].site)))

    def get_by_url(self, url):
        """
        Return a set of prefixes applying to the URL.

        @param url: URL for the interwiki
        @type url: str
        @rtype: set
        """
        return {prefix for prefix, iw_entry in self._iw_sites
                if iw_entry.url == url}
