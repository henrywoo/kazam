# -*- coding: utf-8 -*-
#
#       test_app.py
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

import sys
from unittest import TestCase, main

from gi.repository import Gtk

from kazam.app import KazamApp

def refresh_gui():
  while Gtk.events_pending():
      Gtk.main_iteration_do(False)


class KazamAppTest(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        datadir = "../../data"
        dist = ('Ubuntu', '12.10', 'quantal')

        sys.path.insert(0, "..")

        self._tApp = KazamApp(datadir, dist, False, False, False, False)


    def test_maintoolbar(self):
        self.assertEqual(self._tApp.main_mode, 0)
        self._tApp.btn_shot.changed()
        refresh_gui()
        self.assertEqual(self._tApp.main_mode, 1)

if __name__ == '__main__':
    main()
