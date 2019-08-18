# -*- coding: utf-8 -*-
#
#       window_select.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#       Copyright 2010 Andrew <andrew@karmic-desktop>
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
logger = logging.getLogger("Window Select")

from gettext import gettext as _

from gi.repository import Gtk, GObject, Gdk, Wnck, GdkX11

from kazam.backend.prefs import *


class SelectWindow(GObject.GObject):

    __gsignals__ = {
        "window-selected": (GObject.SIGNAL_RUN_LAST,
                            None,
                            (),
                            ),
        "window-canceled": (GObject.SIGNAL_RUN_LAST,
                            None,
                            (),
                            ),
    }

    def __init__(self):
        super(SelectWindow, self).__init__()
        logger.debug("Initializing select window.")

        self.xid = None

        self.window = Gtk.Window()
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("draw", self.cb_draw)
        self.window.connect("key-press-event", self.cb_keypress_event)
        self.window.connect("button-press-event", self.cb_button_press_event)
        self.window.connect("leave-notify-event", self.cb_leave_notify_event)

        self.window.set_border_width(30)
        self.window.set_app_paintable(True)
        self.window.set_has_resize_grip(False)
        self.window.set_resizable(True)
        self.window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)
        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()
        self.recording = False

        self.disp = GdkX11.X11Display.get_default()
        self.dm = Gdk.Display.get_device_manager(self.disp)
        self.pntr_device = self.dm.get_client_pointer()

        if self.visual is not None and self.screen.is_composited():
            logger.debug("Compositing window manager detected.")
            self.window.set_visual(self.visual)
            self.compositing = True
        else:
            self.compositing = False

        (scr, x, y) = self.pntr_device.get_position()
        cur = scr.get_monitor_at_point(x, y)
        self.window.unfullscreen()
        self.window.move(HW.screens[cur]['x'],
                         HW.screens[cur]['y'])
        self.window.fullscreen()
        crosshair_cursor = Gdk.Cursor(Gdk.CursorType.CROSSHAIR)
        self.last_cursor = Gdk.Cursor(Gdk.CursorType.LEFT_PTR)
        self.gdk_win = self.window.get_root_window()
        self.gdk_win.set_cursor(crosshair_cursor)

    def cb_leave_notify_event(self, widget, event):
        (scr, x, y) = self.pntr_device.get_position()
        cur = scr.get_monitor_at_point(x, y)
        self.window.unfullscreen()
        logger.debug("Move to X: {0} Y: {1}".format(HW.screens[cur]['x'], HW.screens[cur]['y']))
        self.window.move(HW.screens[cur]['x'],
                         HW.screens[cur]['y'])
        self.window.fullscreen()

    def cb_button_press_event(self, widget, event):
        self.geometry = None
        self.win_name = None
        self.xid = None
        # TODO: Error handling
        (op, button) = event.get_button()
        if button == 1:
            screen = Wnck.Screen.get_default()
            screen.force_update()
            workspace = screen.get_active_workspace()
            wins = screen.get_windows_stacked()

            for win in reversed(wins):
                if win.is_visible_on_workspace(workspace) and win.is_in_viewport(workspace):
                    self.win_name = win.get_name()
                    if not (self.win_name.lower().startswith("kazam") or self.win_name.lower().startswith("desktop")):
                        geometry = win.get_client_window_geometry()
                        self.geometry = geometry
                        if geometry[0] <= event.x_root <= (geometry[0] + geometry[2]) and geometry[1] <= event.y_root <= (geometry[1] + geometry[3]):
                            self.xid = win.get_xid()
                            break
            self.gdk_win.set_cursor(self.last_cursor)
            self.window.hide()
            if self.xid:
                self.emit("window-selected")
            else:
                self.emit("window-canceled")

    def cb_keypress_event(self, widget, event):
        (op, keycode) = event.get_keycode()
        if keycode == 36 or keycode == 104 or keycode == 9:  # Enter or Escape
            self.gdk_win.set_cursor(self.last_cursor)
            self.window.hide()
            self.emit("window-canceled")

    def cb_draw(self, widget, cr):
        (w, h) = self.window.get_size()

        if self.compositing:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.45)
        else:
            cr.set_source_rgb(0.5, 0.5, 0.5)

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        if self.compositing:
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        else:
            cr.set_source_rgba(1.0, 1.0, 1.0)

        cr.set_operator(cairo.OPERATOR_OVER)
        self._outline_text(cr, w, h, 30, _("Select a window by clicking on it."))
        self._outline_text(cr, w, h + 50, 26, _("Press ENTER or ESC to cancel"))

    def _outline_text(self, cr, w, h, size, text):
        cr.set_font_size(size)
        try:
            cr.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        except:
            pass
        te = cr.text_extents(text)
        cr.set_line_width(2.0)
        cx = w / 2 - te[2] / 2
        cy = h / 2 - te[3] / 2
        if self.compositing:
            cr.set_source_rgba(0.4, 0.4, 0.4, 1.0)
        else:
            cr.set_source_rgb(0.4, 0.4, 0.4)

        cr.move_to(cx, cy)
        cr.text_path(text)
        cr.stroke()
        if self.compositing:
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        else:
            cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.move_to(cx, cy)
        cr.show_text(text)
