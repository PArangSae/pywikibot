# -*- coding: utf-8 -*-
"""Module containing various formatting related utilities."""
#
# (C) Pywikibot team, 2015-2020
#
# Distributed under the terms of the MIT license.
#
import math

from string import Formatter
from typing import Any, Mapping, Sequence

from pywikibot.logging import output
from pywikibot.userinterfaces.terminal_interface_base import colors


class SequenceOutputter:

    """A class formatting a list of items.

    It is possible to customize the appearance by changing
    C{format_string} which is used by C{str.format} with C{index},
    C{width} and C{item}. Each line is joined by the separator and the
    complete text is surrounded by the prefix and the suffix. All three
    are by default a new line. The index starts at 1 and for the width
    it's using the width of the sequence's length written as a decimal
    number. So a length of 100 will result in a with of 3 and a length
    of 99 in a width of 2.

    It is iterating over C{self.sequence} to generate the text. That
    sequence can be any iterator but the result is better when it has
    an order.
    """

    format_string = '  {index:>{width}} - {item}'
    separator = '\n'
    prefix = '\n'
    suffix = '\n'

    def __init__(self, sequence):
        """Create a new instance with a reference to the sequence."""
        super().__init__()
        self.sequence = sequence

    def format_list(self):
        """Create the text with one item on each line."""
        if self.sequence:
            # Width is only defined when the length is greater 0
            width = int(math.log10(len(self.sequence))) + 1
            content = self.separator.join(
                self.format_string.format(index=i, item=item, width=width)
                for i, item in enumerate(self.sequence, start=1))
        else:
            content = ''
        return self.prefix + content + self.suffix

    def output(self):
        """Output the text of the current sequence."""
        output(self.format_list())


class _ColorFormatter(Formatter):

    """Special string formatter which skips colors."""

    colors = set(colors)
    # Dot.product of colors to create all possible combinations of foreground
    # and background colors.
    colors |= {'{0};{1}'.format(c1, c2) for c1 in colors for c2 in colors}

    def get_value(self, key, args, kwargs):
        """Get value, filling in 'color' when it is a valid color."""
        if key == 'color' and kwargs.get('color') in self.colors:
            return '\03{{{0}}}'.format(kwargs[key])
        else:
            return super().get_value(key, args, kwargs)

    def parse(self, format_string: str):
        """Yield results similar to parse but skip colors."""
        previous_literal = ''
        for literal, field, spec, conv in super().parse(format_string):
            if field in self.colors:
                if spec:
                    raise ValueError(
                        'Color field "{0}" in "{1}" uses format spec '
                        'information "{2}"'.format(field, format_string, spec))
                elif conv:
                    raise ValueError(
                        'Color field "{0}" in "{1}" uses conversion '
                        'information "{2}"'.format(field, format_string, conv))
                else:
                    if not literal or literal[-1] != '\03':
                        literal += '\03'
                    if '\03' in literal[:-1]:
                        raise ValueError(r'Literal text in {0} contains '
                                         r'\03'.format(format_string))
                    previous_literal += literal + '{' + field + '}'
            else:
                if '\03' in literal:
                    raise ValueError(r'Literal text in {0} contains '
                                     r'\03'.format(format_string))
                yield previous_literal + literal, field, spec, conv
                previous_literal = ''
        if previous_literal:
            yield previous_literal, None, None, None

    def vformat(self, format_string: str, args: Sequence,
                kwargs: Mapping[str, Any]) -> str:
        """Return the format result but verify no colors are keywords.

        @param format_string: The format template string
        @param args: The positional field values
        @param kwargs: The named field values
        @return: The formatted string
        """
        if self.colors.intersection(kwargs):  # kwargs use colors
            raise ValueError('Keyword argument(s) use valid color(s): '
                             + '", "'.join(self.colors.intersection(kwargs)))
        return super().vformat(format_string, args, kwargs)


def color_format(text: str, *args, **kwargs) -> str:
    r"""
    Do C{str.format} without having to worry about colors.

    It is automatically adding \03 in front of color fields so it's
    unnecessary to add them manually. Any other \03 in the text is
    disallowed.

    You may use a variant {color} by assigning a valid color to a named
    parameter color.

    @param text: The format template string
    @return: The formatted string
    """
    return _ColorFormatter().format(text, *args, **kwargs)
