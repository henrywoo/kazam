# -*- coding: utf-8 -*-
#
#       window_webcam.py
#
#       Copyright 2014 David Klasinc <bigwhale@lubica.net>
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
import logging
logger = logging.getLogger("Window Webcam")

from gi.repository import Gtk, GObject, Gdk, GdkX11

from kazam.backend.prefs import *


class WebcamWindow(GObject.GObject):
    def __init__(self, width, height, position):
        super(WebcamWindow, self).__init__()
        logger.debug("Initializing Webcam window.")

        self.xid = None

        self.window = Gtk.Window()
        self.window.set_default_size(width, height)
        self.webcam_area = Gtk.DrawingArea()
        self.window.add(self.webcam_area)
        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)
        self.window.show_all()

        screen = HW.screens[prefs.current_screen]
        self.window.set_size_request(width, height)
        if position == CAM_PREVIEW_TL:
            self.window.set_gravity(Gdk.Gravity.NORTH_WEST)
            self.window.move(screen['x'], screen['y'])
        elif position == CAM_PREVIEW_TR:
            self.window.set_gravity(Gdk.Gravity.NORTH_EAST)
            self.window.move(screen['x'] + screen['width'] - width, screen['y'])
        elif position == CAM_PREVIEW_BR:
            self.window.set_gravity(Gdk.Gravity.SOUTH_EAST)
            self.window.move(screen['x'] + screen['width'] - width, screen['y'] + screen['height'] - height)
        elif position == CAM_PREVIEW_BL:
            self.window.set_gravity(Gdk.Gravity.SOUTH_WEST)
            self.window.move(screen['x'], screen['y'] + screen['height'] - height)
        else:
            pass

        self.xid = self.webcam_area.get_property('window').get_xid()
