# -*- coding: utf-8 -*-
#
#       window_select.py
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

import cairo
import logging
logger = logging.getLogger("Outline Window")

from gi.repository import Gtk, GObject, Gdk, Wnck, GdkX11

from kazam.backend.prefs import *


class OutlineWindow(GObject.GObject):

    def __init__(self, x, y, w, h):
        super(OutlineWindow, self).__init__()
        logger.debug("Initializing outline window.")
        self.x = x - 1
        self.y = y - 1
        self.w = w + 3
        if y > 23:
            self.h = h + 3
        else:
            self.no_top = True
            self.h = h - 23 + y
        self.window = Gtk.Window()

        self.window.connect("draw", self.cb_draw)

        self.window.set_border_width(0)
        self.window.set_app_paintable(True)
        self.window.set_has_resize_grip(False)
        self.window.set_resizable(True)
        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)

        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()

        self.disp = GdkX11.X11Display.get_default()
        self.dm = Gdk.Display.get_device_manager(self.disp)
        self.pntr_device = self.dm.get_client_pointer()

        if self.visual is not None and self.screen.is_composited():
            logger.debug("Compositing window manager detected.")
            self.window.set_visual(self.visual)
            self.compositing = True
        else:
            logger.warning("Compositing window manager not found, expect the unexpected.")
            self.compositing = False

        #
        # Hardcore Launcher and Panel size detection
        #
        screen = Wnck.Screen.get_default()
        screen.force_update()
        workspace = screen.get_active_workspace()
        wins = screen.get_windows_stacked()
        self.panel_height = 24
        self.launcher_width = 49

        try:
            logger.debug("Trying to determine Unity Launcher and Panel sizes.")
            for win in reversed(wins):
                if win.get_name() == 'unity-panel':
                    self.panel_height = win.get_client_window_geometry()[3]
                if win.get_name() == 'unity-launcher':
                    self.launcher_width = win.get_client_window_geometry()[2]
        except:
            logger.warning("Unable to detect correct launcher and panel sizes. Using fallback.")

        logger.debug("Got panel size and launcher.")
        self.window.move(self.x, self.y)
        self.window.set_default_geometry(self.w, self.h)
        (x, y) = self.window.get_position()
        (w, h) = self.window.get_size()
        logger.debug("Showing outline window.")
        self.window.show_all()
        logger.debug("Outline window shown.")

    def show(self):
        self.window.show_all()

    def hide(self):
        (x, y) = self.window.get_position()
        (w, h) = self.window.get_size()
        self.window.hide()

    def cb_draw(self, widget, cr):
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
        surface_ctx = cairo.Context(surface)
        surface_ctx.set_source_rgba(1.0, 1.0, 1.0, 0.0)
        surface_ctx.set_operator(cairo.OPERATOR_SOURCE)
        surface_ctx.paint()

        rect = cairo.RectangleInt(0, 0, 1, 1)
        reg = cairo.Region(rect)
        if (not reg.is_empty()):
            widget.input_shape_combine_region(None)
            widget.input_shape_combine_region(reg)

        cr.move_to(0, 0)
        cr.set_source_rgba(1.0, 0.0, 0.0, 0.8)
        cr.set_line_width(2.0)

        #
        # Seriously?
        # The thing is, windows cannot overlap Panel or Launcher.
        # Ugly code taking care of this overlapping is below.
        #
        if self.y > self.panel_height - 1:
            cr.line_to(self.w, 0)
        else:
            cr.move_to(self.w, 0)
        if self.x + self.w < HW.screens[self.screen.get_number()]['width']:
            cr.line_to(self.w, self.h)
        else:
            cr.move_to(self.w, self.h)
        if self.y + self.h < HW.screens[self.screen.get_number()]['height']:
            cr.line_to(0, self.h)
        else:
            cr.move_to(0, self.h)
        if self.x > self.launcher_width:
            cr.line_to(0, 0)

        cr.stroke()
        cr.set_operator(cairo.OPERATOR_OVER)
