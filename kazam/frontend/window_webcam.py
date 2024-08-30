# -*- coding: utf-8 -*-
#
#       window_select.py
#
#       Copyright 2018 Henry Fuheng Wu <wufuheng@gmail.com>
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
    def __init__(self, width, height, position, x_offset, y_offset):
        super(WebcamWindow, self).__init__()
        logger.debug("Initializing Webcam window.")

        self.xid = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.window = Gtk.Window()
        self.window.set_default_size(width, height)
        self.webcam_area = Gtk.DrawingArea()
        self.window.add(self.webcam_area)
        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)

        # Connect to the realize signal to safely access the window's XID
        self.webcam_area.connect("realize", self.on_realize)
        self.webcam_area.set_double_buffered(True)
        self.webcam_area.set_app_paintable(True)
        self.window.set_app_paintable(True)

        # Connect mouse events for dragging
        self.window.connect("button-press-event", self.on_button_press)
        self.window.connect("motion-notify-event", self.on_motion_notify)

        self.window.show_all()

        screen = HW.screens[prefs.current_screen]
        self.window.set_size_request(width, height)
        if position == CAM_PREVIEW_TL:
            self.window.set_gravity(Gdk.Gravity.NORTH_WEST)
            self.window.move(screen['x'] + x_offset, screen['y'] + y_offset)
        elif position == CAM_PREVIEW_TR:
            self.window.set_gravity(Gdk.Gravity.NORTH_EAST)
            self.window.move(screen['x'] + screen['width'] - width - x_offset, screen['y'] + y_offset)
        elif position == CAM_PREVIEW_BR:
            self.window.set_gravity(Gdk.Gravity.SOUTH_EAST)
            self.window.move(screen['x'] + screen['width'] - width - x_offset, screen['y'] + screen['height'] - height - y_offset)
        elif position == CAM_PREVIEW_BL:
            self.window.set_gravity(Gdk.Gravity.SOUTH_WEST)
            self.window.move(screen['x'] + x_offset, screen['y'] + screen['height'] - height - y_offset)
        else:
            pass

    def on_realize(self, widget):
        # Ensure the GDK window is realized before accessing XID
        self.xid = widget.get_property('window').get_xid()
        logger.debug(f"Webcam area XID: {self.xid}")

    def on_button_press(self, widget, event):
        # Store the initial click position for dragging
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:  # Left click
            self.drag_offset_x = event.x
            self.drag_offset_y = event.y

    def on_motion_notify(self, widget, event):
        # Update window position based on mouse movement
        if event.state & Gdk.ModifierType.BUTTON1_MASK:  # Left button is held
            x, y = self.window.get_position()
            new_x = x + (event.x - self.drag_offset_x)
            new_y = y + (event.y - self.drag_offset_y)
            self.window.move(new_x, new_y)
