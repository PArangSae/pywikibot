# -*- coding: utf-8 -*-
"""Module containing plural rules of various languages."""
#
# (C) Pywikibot team, 2011-2020
#
# Distributed under the terms of the MIT license.
#
import sys

from typing import Callable, Union

if sys.version_info[:2] >= (3, 9):
    Dict = dict
else:
    from typing import Dict


PluralRule = Dict[str, Union[int, Callable]]

plural_rules = {
    '_default': {'nplurals': 2, 'plural': lambda n: (n != 1)},
    'ar': {'nplurals': 6, 'plural': lambda n:
           0 if (n == 0) else
           1 if (n == 1) else
           2 if (n == 2) else
           3 if (3 <= (n % 100) <= 10) else
           4 if (11 <= (n % 100) <= 99) else
           5},
    'cs': {'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (2 <= n <= 4) else
           2},
    'cy': {'nplurals': 4, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 2) else
           2 if (n != 8 and n != 11) else
           3},
    'ga': {'nplurals': 5, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 2) else
           2 if (n < 7) else
           3 if (n < 11) else
           4},
    'gd': {'nplurals': 4, 'plural': lambda n:
           0 if (n == 1 or n == 11) else
           1 if (n == 2 or n == 12) else
           2 if (2 < n < 20) else
           3},
    'is': {'nplurals': 2, 'plural': lambda n: (n % 10 != 1 or n % 100 == 11)},
    'kw': {'nplurals': 4, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 2) else
           2 if (n == 3) else
           3},
    'lt': {'nplurals': 3, 'plural': lambda n:
           0 if (n % 10 == 1 and n % 100 != 11) else
           1 if (n % 10 >= 2 and (n % 100 < 10 or n % 100 >= 20)) else
           2},
    'lv': {'nplurals': 3, 'plural': lambda n:
           0 if (n % 10 == 1 and n % 100 != 11) else
           1 if (n != 0) else
           2},
    'mk': {'nplurals': 2, 'plural': lambda n:
           0 if n % 10 == 1 else
           1},
    'mnk': {'nplurals': 3, 'plural': lambda n:
            0 if (n == 0) else
            1 if n == 1 else
            2},
    'mt': {'nplurals': 4, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 0 or (1 < (n % 100) < 11)) else
           2 if (10 < (n % 100) < 20) else
           3},
    'pl': {'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (2 <= (n % 10) <= 4) and (n % 100 < 10 or n % 100 >= 20)
           else 2},
    'ro': {'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (n == 0 or (0 < (n % 100) < 20)) else
           2},
    'sk': {'nplurals': 3, 'plural': lambda n:
           0 if (n == 1) else
           1 if (2 <= n <= 4) else
           2},
    'sl': {'nplurals': 4, 'plural': lambda n:
           0 if (n % 100 == 1) else
           1 if (n % 100 == 2) else
           2 if n % 100 in (3, 4) else
           3},
}  # type: Dict[str, PluralRule]

plural_rules.update(
    dict.fromkeys(
        ['ay', 'bo', 'cgg', 'dz', 'fa', 'id', 'ja', 'jbo', 'ka', 'kk', 'km',
         'ko', 'ky', 'lo', 'ms', 'my', 'sah', 'su', 'th', 'tt', 'ug', 'vi',
         'wo', 'zh', 'zh-hans', 'zh-hant', 'zh-tw'],
        {'nplurals': 1, 'plural': 0}))

plural_rules.update(
    dict.fromkeys(
        ['ach', 'ak', 'am', 'arn', 'br', 'fil', 'fr', 'gun', 'ln', 'mfe', 'mg',
         'mi', 'oc', 'pt-br', 'ti', 'tr', 'uz', 'wa'],
        {'nplurals': 2, 'plural': lambda n: (n > 1)}))

plural_rules.update(
    dict.fromkeys(
        ['be', 'bs', 'csb', 'hr', 'ru', 'sr', 'uk'],
        {'nplurals': 3, 'plural': lambda n:
         0 if n % 10 == 1 and n % 100 != 11 else
         1 if (2 <= (n % 10) <= 4) and (n % 100 < 10 or n % 100 >= 20)
         else 2}))


def plural_rule(lang: str) -> PluralRule:
    """Return the plural rule for a given lang."""
    return plural_rules.get(lang, plural_rules['_default'])
