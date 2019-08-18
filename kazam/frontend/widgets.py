# -*- coding: utf-8 -*-
#
#       widgets.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from gi.repository import Gtk

class _Tile(object):
    def __init__(self):
        self.set_focus_on_click(False)
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.box.set_size_request(62, -1)
        self.add(self.box)

    def create_default(self, label, icon):
        if icon is not None:
            if isinstance(icon, Gtk.Image):
                self.image = icon
            else:
                self.image = Gtk.Image()
            self.box.pack_start(self.image, True, True, 0)

        self.label = Gtk.Label.new(label)
        self.box.pack_start(self.label, True, True, 0)


class TileToggleButton(Gtk.RadioButton, _Tile):
    def __init__(self):
        Gtk.RadioButton.__init__(self)
        self.set_mode(False)
        _Tile.__init__(self)


class ModeButton(TileToggleButton):
    def __init__(self, label, icon):
        TileToggleButton.__init__(self)
        html = "<small>%s</small>" % label
        self.create_default(html, icon)
        self.label.set_use_markup(True)
        self.label.set_justify(Gtk.Justification.CENTER)

    #def do_draw(self, cr):
        #for child in self:
        #    self.propagate_draw(child, cr)
