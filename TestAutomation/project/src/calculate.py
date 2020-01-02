# -*- coding: utf-8 -*-
# calculate.py, sugar calculator, by:
#   Reinier Heeres <reinier@heeres.eu>
#   Miguel Alvarez <miguel@laptop.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Change log:
#    2007-07-03: rwh, first version

from gettext import gettext as _
#from numerals import local as _n, standard as _s
import logging
_logger = logging.getLogger('Calculate')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
import base64

#import sugar3.profile
#from sugar3.graphics.xocolor import XoColor

#from shareable_activity import ShareableActivity
#from layout import CalcLayout
#from mathlib import MathLib
#from astparser import AstParser, ParserError, ParseError, RuntimeError
#from svgimage import SVGImage

from decimal import Decimal
#from rational import Rational


def findchar(text, chars, ofs=0):
    '''
    Find a character in set <chars> starting from offset ofs.
    Everything between brackets '()' is ignored.
    '''

    level = 0
    for i in range(ofs, len(text)):
        if text[i] in chars and level == 0:
            return i
        elif text[i] == '(':
            level += 1
        elif text[i] == ')':
            level -= 1

    return -1


def _textview_realize_cb(widget):
    '''Change textview properties once window is created.'''
    win = widget.get_window(Gtk.TextWindowType.TEXT)
    win.set_cursor(Gdk.Cursor.new(Gdk.CursorType.HAND1))
    return False


class Equation:

    def __init__(self, label=None, eqn=None, res=None, col=None, owner=None,
                 eqnstr=None, ml=None):

        if eqnstr is not None:
            self.parse(eqnstr)
        elif eqn is not None:
            self.set(label, eqn, res, col, owner)

        self.ml = ml

    def set(self, label, eqn, res, col, owner):
        """Set equation properties."""

        self.label = label
        self.equation = eqn
        self.result = res
        self.color = col
        self.owner = owner

    def __str__(self):
        if isinstance(self.result, SVGImage):
            svg_data = "<svg>" + base64.b64encode(self.result.get_svg_data())
            return "%s;%s;%s;%s;%s\n" % \
                (self.label, self.equation, svg_data,
                 self.color.to_string(), self.owner)
        else:
            return "%s;%s;%s;%s;%s\n" % \
                (self.label, self.equation, self.result,
                 self.color.to_string(), self.owner)

    def parse(self, str):
        """Parse equation object string representation."""

        str = str.rstrip("\r\n")
        k = str.split(';')
        if len(k) != 5:
            _logger.error(_('Equation.parse() string invalid (%s)'), str)
            return False

        if k[2].startswith("<svg>"):
            k[2] = SVGImage(data=base64.b64decode(k[2][5:]))

        # Should figure out how to use MathLib directly in a non-hacky way
        else:
            try:
                k[2] = Decimal(k[2])
            except Exception:
                pass

        self.set(k[0], k[1], k[2], XoColor(color_string=k[3]), k[4])

    def determine_font_size(self, *tags):
        size = 0
        for tag in tags:
            try:
                size = max(size, tag.get_property('size'))
            except:
                pass
        return size

    def append_with_superscript_tags(self, buf, text, *tags):
        '''Add a text to a Gtk.TextBuffer with superscript tags.'''
        fontsize = self.determine_font_size(*tags)
        _logger.debug('font-size: %d', fontsize)
        tagsuper = buf.create_tag(rise=fontsize / 2)

        ENDSET = list(AstParser.DIADIC_OPS)
        ENDSET.extend((',', '(', ')'))
        ASET = list(AstParser.DIADIC_OPS)
        ofs = 0
        bracket_level = 0
        level = 0
        while ofs <= len(text) and text.find('**', ofs) != -1:
            nextofs = text.find('**', ofs)
            buf.insert_with_tags(buf.get_end_iter(), text[ofs:nextofs], *tags)
            nextofs2 = findchar(text, ENDSET, nextofs + 2)
            for i in range(nextofs, len(text)):
                if text[i] in ['(', '+', '-', ')']:
                    if text[i] == '(':
                        bracket_level = bracket_level + 1
                    elif text[i] == ')':
                        nextofs2 = i + 1
                        bracket_level = bracket_level - 1
                        if bracket_level == 0:
                            break
                    elif text[i] == '+':
                        if level == 0 and bracket_level == 0:
                            nextofs2 = findchar(text, ASET, i)
                            break
                        if bracket_level == 0:
                            nextofs2 = findchar(text, ASET, i + 1)
                            break
                    elif text[i] == '-':
                        if bracket_level == 0:
                            if i == nextofs + 2:
                                nextofs2 = findchar(text, ASET, i + 1)
                                break
                            else:
                                nextofs2 = findchar(text, ASET, i)
                                break

            _logger.debug('nextofs2: %d, char=%c', nextofs2, text[nextofs2])
            if nextofs2 == -1:
                nextofs2 = len(text)
            buf.insert_with_tags(
                buf.get_end_iter(), text[nextofs + 2:nextofs2],
                tagsuper, *tags)
            ofs = nextofs2

        if ofs < len(text):
            buf.insert_with_tags(buf.get_end_iter(), text[ofs:], *tags)

    def create_lasteq_textbuf(self):
        '''
        Return a Gtk.TextBuffer properly formatted for last equation
        Gtk.TextView.
        '''

        is_error = isinstance(self.result, ParserError)
        buf = Gtk.TextBuffer()
        tagsmallnarrow = buf.create_tag(font=CalcLayout.FONT_SMALL_NARROW)
        tagbignarrow = buf.create_tag(font=CalcLayout.FONT_BIG_NARROW)
        tagbigger = buf.create_tag(font=CalcLayout.FONT_BIGGER)
        tagjustright = buf.create_tag(justification=Gtk.Justification.RIGHT)
        tagred = buf.create_tag(foreground='#FF0000')

        # Add label and equation
        if len(self.label) > 0:
            labelstr = '%s:' % self.label
            buf.insert_with_tags(buf.get_end_iter(), labelstr, tagbignarrow)
        eqnoffset = buf.get_end_iter().get_offset()
        eqnstr = '%s\n' % str(self.equation)
        if is_error:
            buf.insert_with_tags(buf.get_end_iter(), eqnstr, tagbignarrow)
        else:
            self.append_with_superscript_tags(buf, eqnstr, tagbignarrow)

        # Add result
        if type(self.result) in (bytes, str):
            resstr = str(self.result)
            resstr = resstr.rstrip('0').rstrip('.') \
                if '.' in resstr else resstr
            buf.insert_with_tags(buf.get_end_iter(), resstr,
                                 tagsmallnarrow, tagjustright)
        elif is_error:
            resstr = str(self.result)
            resstr = resstr.rstrip('0').rstrip('.') \
                if '.' in resstr else resstr
            buf.insert_with_tags(buf.get_end_iter(), resstr, tagsmallnarrow)
            range = self.result.get_range()
            eqnstart = buf.get_iter_at_offset(eqnoffset + range[0])
            eqnend = buf.get_iter_at_offset(eqnoffset + range[1])
            buf.apply_tag(tagred, eqnstart, eqnend)
        elif not isinstance(self.result, SVGImage):
            resstr = self.ml.format_number(self.result)
            resstr = str(resstr).rstrip('0').rstrip('.') \
                if '.' in resstr else resstr
            self.append_with_superscript_tags(buf, resstr, tagbigger,
                                              tagjustright)

        return buf

    def create_history_object(self):
        """
        Create a history object for this equation.
        In case of an SVG result this will be the image, otherwise it will
        return a properly formatted Gtk.TextView.
        """

        if isinstance(self.result, SVGImage):
            return self.result.get_image()

        w = Gtk.TextView()
        w.modify_base(
            Gtk.StateType.NORMAL, Gdk.color_parse(self.color.get_fill_color()))
        w.modify_bg(
            Gtk.StateType.NORMAL,
            Gdk.color_parse(self.color.get_stroke_color()))
        w.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        w.set_border_window_size(Gtk.TextWindowType.LEFT, 4)
        w.set_border_window_size(Gtk.TextWindowType.RIGHT, 4)
        w.set_border_window_size(Gtk.TextWindowType.TOP, 4)
        w.set_border_window_size(Gtk.TextWindowType.BOTTOM, 4)
        w.connect('realize', _textview_realize_cb)
        buf = w.get_buffer()

        tagsmall = buf.create_tag(font=CalcLayout.FONT_SMALL)
        tagsmallnarrow = buf.create_tag(font=CalcLayout.FONT_SMALL_NARROW)
        tagbig = buf.create_tag(font=CalcLayout.FONT_BIG,
                                justification=Gtk.Justification.RIGHT)
        # TODO Fix for old Sugar 0.82 builds, red_float not available
        bright = (
            Gdk.color_parse(self.color.get_fill_color()).red_float +
            Gdk.color_parse(self.color.get_fill_color()).green_float +
            Gdk.color_parse(self.color.get_fill_color()).blue_float) / 3.0
        if bright < 0.5:
            col = Gdk.color_parse('white')
        else:
            col = Gdk.color_parse('black')
        tagcolor = buf.create_tag(foreground=col)

        # Add label, equation and result
        if len(self.label) > 0:
            labelstr = '%s:' % self.label
            buf.insert_with_tags(buf.get_end_iter(), labelstr, tagsmallnarrow)
        eqnstr = '%s\n' % str(self.equation)
        self.append_with_superscript_tags(buf, eqnstr, tagsmall)

        resstr = self.ml.format_number(self.result)
        resstr = str(resstr).rstrip('0').rstrip('.') \
            if '.' in resstr else resstr
        if len(resstr) > 30:
            restag = tagsmall
        else:
            restag = tagbig
        self.append_with_superscript_tags(buf, resstr, restag)

        buf.apply_tag(tagcolor, buf.get_start_iter(), buf.get_end_iter())

        return w

def main():
    win = Gtk.Window(Gtk.WindowType.TOPLEVEL)
    Calculate(win)
    Gtk.main()
    return 0


if __name__ == "__main__":
    main()
