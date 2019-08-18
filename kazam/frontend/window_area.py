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
import math
import logging
logger = logging.getLogger("Window Select")

from gettext import gettext as _

from gi.repository import Gtk, GObject, Gdk, Wnck, GdkX11

from kazam.backend.prefs import *
from kazam.utils import in_circle


class AreaWindow(GObject.GObject):

    __gsignals__ = {
        "area-selected": (GObject.SIGNAL_RUN_LAST,
                          None,
                          (),
                          ),
        "area-canceled": (GObject.SIGNAL_RUN_LAST,
                          None,
                          (),
                          ),
    }

    def __init__(self):
        super(AreaWindow, self).__init__()
        logger.debug("Initializing select window.")

        # Resizing and movement
        self.resize_handle = None
        self.move_offsetx = 0
        self.move_offsety = 0

        # Position and size
        self.startx = 0
        self.starty = 0
        self.endx = 0
        self.endy = 0
        self.g_startx = 0
        self.g_starty = 0
        self.g_endx = 0
        self.g_endy = 0
        self.height = 0
        self.width = 0

        self.window = Gtk.Window()
        self.box = Gtk.Box()
        self.drawing = Gtk.DrawingArea()
        self.box.pack_start(self.drawing, True, True, 0)
        self.drawing.set_size_request(500, 500)
        self.window.add(self.box)

        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("key-press-event", self.cb_keypress_event)

        self.drawing.connect("draw", self.cb_draw)
        self.drawing.connect("motion-notify-event", self.cb_draw_motion_notify_event)
        self.drawing.connect("button-press-event", self.cb_draw_button_press_event)
        self.drawing.connect("button-release-event", self.cb_draw_button_release_event)
        self.drawing.connect("leave-notify-event", self.cb_leave_notify_event)
        self.drawing.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |
                                Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                                Gdk.EventMask.LEAVE_NOTIFY_MASK)

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

        (scr, x, y) = self.pntr_device.get_position()
        cur = scr.get_monitor_at_point(x, y)
        self.window.move(HW.screens[cur]['x'],
                         HW.screens[cur]['y'])
        self.window.fullscreen()

        crosshair_cursor = Gdk.Cursor(Gdk.CursorType.CROSSHAIR)
        self.last_cursor = Gdk.Cursor(Gdk.CursorType.LEFT_PTR)
        self.gdk_win = self.window.get_root_window()
        self.gdk_win.set_cursor(crosshair_cursor)

    def cb_draw_motion_notify_event(self, widget, event):
        (state, x, y, mask) = event.window.get_device_position(self.pntr_device)

        (scr, x, y) = self.pntr_device.get_position()
        cur = scr.get_monitor_at_point(x, y)
        ex = int(event.x)
        ey = int(event.y)
        sx = HW.screens[cur]['x']
        sy = HW.screens[cur]['y']

        # Set arrow cursors
        cursor_changed = False
        for i in range(0, 9):
            # X and Y offsets, added to start position
            x = i % 3 / 2
            y = math.floor(i / 3) / 2
            offsetx = self.width * x
            offsety = self.height * y

            # Invert cursors if area is selected from the bottom up
            if self.g_startx > self.g_endx:
                offsetx *= -1
            if self.g_starty > self.g_endy:
                offsety *= -1

            # Show arrow cursors when hovering over any of the handles
            if in_circle(min(self.g_startx, self.g_endx) + offsetx, min(self.g_starty, self.g_endy) + offsety, 8, sx + ex, sy + ey):
                cursor_changed = True
                self.gdk_win.set_cursor(Gdk.Cursor(HANDLE_CURSORS[i]))
                break
            self.gdk_win.set_cursor(Gdk.Cursor(Gdk.CursorType.CROSSHAIR))

        # Set hand cursor
        if not cursor_changed and \
           min(self.startx, self.endx) < ex < max(self.startx, self.endx) and \
           min(self.starty, self.endy) < ey < max(self.starty, self.endy):
            self.gdk_win.set_cursor(Gdk.Cursor(HANDLE_CURSORS[HANDLE_MOVE]))

        if mask & Gdk.ModifierType.BUTTON1_MASK:
            # Top left
            if self.resize_handle == HANDLE_TL:
                self.startx = ex
                self.starty = ey
                self.g_startx = sx + ex
                self.g_starty = sy + ey

            # Top center
            elif self.resize_handle == HANDLE_TC:
                self.starty = ey
                self.g_starty = sy + ey

            # Top right
            elif self.resize_handle == HANDLE_TR:
                self.endx = ex
                self.starty = ey
                self.g_endx = sx + ex
                self.g_starty = sy + ey

            # Center left
            elif self.resize_handle == HANDLE_CL:
                self.startx = ex
                self.g_startx = sx + ex

            # Center right
            elif self.resize_handle == HANDLE_CR:
                self.endx = ex
                self.g_endx = sx + ex

            # Bottom left
            elif self.resize_handle == HANDLE_BL:
                self.startx = ex
                self.endy = ey
                self.g_startx = sx + ex
                self.g_endy = sy + ey

            # Bottom center
            elif self.resize_handle == HANDLE_BC:
                self.endy = ey
                self.g_endy = sy + ey

            # Bottom right
            elif self.resize_handle == HANDLE_BR:
                self.endx = ex
                self.endy = ey
                self.g_endx = sx + ex
                self.g_endy = sy + ey

            # Make selection movable
            elif self.resize_handle == HANDLE_MOVE:
                # The position where the movement was initiated
                if self.move_offsetx == self.move_offsety == 0:
                    self.move_offsetx = ex - self.startx
                    self.move_offsety = ey - self.starty

                # Update area position with respect to the initial offset
                self.startx = max(0, ex - self.move_offsetx)
                self.starty = max(0, ey - self.move_offsety)
                self.endx = self.startx + self.width
                self.endy = self.starty + self.height

                sw = HW.screens[cur]['width']
                sh = HW.screens[cur]['height']
                if self.endx > sw:
                    self.startx -= self.endx - sw
                    self.endx = sw
                if self.endy > sh:
                    self.starty -= self.endy - sh
                    self.endy = sh

                self.g_startx = sx + self.startx
                self.g_starty = sy + self.starty
                self.g_endx = sx + self.endx
                self.g_endy = sy + self.endy

            # New selection
            else:
                self.endx = ex
                self.endy = ey
                self.g_endx = sx + ex
                self.g_endy = sy + ey

            # Width and height should always be updated
            self.width = self.endx - self.startx
            self.height = self.endy - self.starty

        widget.queue_draw()
        return True

    def cb_draw_button_press_event(self, widget, event):
        (scr, x, y) = self.pntr_device.get_position()
        cur = scr.get_monitor_at_point(x, y)

        # Save them temporarily here as we need both the new and old values
        startx = int(event.x)
        starty = int(event.y)
        g_startx = HW.screens[cur]['x'] + startx
        g_starty = HW.screens[cur]['y'] + starty

        for i in range(0, 9):
            # X and Y offsets, added to start position
            x = i % 3 / 2
            y = math.floor(i / 3) / 2
            offsetx = self.width * x
            offsety = self.height * y

            if in_circle(self.g_startx + offsetx, self.g_starty + offsety, 8, g_startx, g_starty):
                self.resize_handle = i
                return True

        # Move selection
        if min(self.startx, self.endx) < startx < max(self.startx, self.endx) and \
           min(self.starty, self.endy) < starty < max(self.starty, self.endy):

            # Check if user double clicked somewhere in the selected area and accept it if they did
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.accept_area()
                self.emit("area-selected")

            self.resize_handle = HANDLE_MOVE
            return True

        # Start new selection if no handle is selected
        self.startx = startx
        self.starty = starty
        self.g_startx = g_startx
        self.g_starty = g_starty
        self.endx = 0
        self.endy = 0
        self.g_endx = 0
        self.g_endy = 0
        self.width = 0
        self.height = 0

    def cb_draw_button_release_event(self, widget, event):
        self.resize_handle = None
        self.move_offsetx = 0
        self.move_offsety = 0

    def cb_leave_notify_event(self, widget, event):
        (scr, x, y) = self.pntr_device.get_position()
        if x > 0 or y > 0:
            cur = scr.get_monitor_at_point(x, y)
            self.window.unfullscreen()
            self.window.move(HW.screens[cur]['x'],
                             HW.screens[cur]['y'])
            self.window.fullscreen()
            logger.debug("Move to X: {0} Y: {1}".format(HW.screens[cur]['x'], HW.screens[cur]['y']))
        return True

    def cb_keypress_event(self, widget, event):
        (op, keycode) = event.get_keycode()
        if keycode == 36 or keycode == 104:  # Enter
            self.accept_area()
            self.emit("area-selected")
        elif keycode == 9:  # ESC
            self.gdk_win.set_cursor(self.last_cursor)
            self.window.hide()
            self.emit("area-canceled")

    def cb_draw(self, widget, cr):
        (w, h) = self.window.get_size()

        if self.compositing:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.45)
        else:
            cr.set_source_rgb(0.5, 0.5, 0.5)

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        # Draw the selection area
        cr.set_line_width(1)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.rectangle(self.startx, self.starty, self.width, self.height)
        cr.stroke()

        if self.compositing:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        else:
            cr.set_source_rgb(0.0, 0.0, 0.0)

        cr.rectangle(self.startx + 1, self.starty + 1, self.width - 2, self.height - 2)
        cr.fill()

        cr.set_operator(cairo.OPERATOR_OVER)

        # Draw resize handles
        for i in range(0, 9):
            # Skip center handle
            if i == HANDLE_MOVE:
                continue

            # X and Y offsets, added to start position
            x = i % 3 / 2
            y = math.floor(i / 3) / 2
            centerx = self.startx + self.width * x
            centery = self.starty + self.height * y

            # Handle shadow
            grad = cairo.RadialGradient(centerx, centery, 0, centerx, centery + 2, 10)
            grad.add_color_stop_rgba(0.6, 0.0, 0.0, 0.0, 0.6)
            grad.add_color_stop_rgba(0.75, 0.0, 0.0, 0.0, 0.25)
            grad.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.0)

            cr.arc(centerx, centery, 10, 0, 2 * math.pi)
            cr.set_source(grad)
            cr.fill()

            # Handle background
            grad = cairo.LinearGradient(centerx, centery - 8, centerx, centery + 8)
            grad.add_color_stop_rgb(0.0, 0.75, 0.75, 0.75)
            grad.add_color_stop_rgb(0.75, 0.95, 0.95, 0.95)

            cr.arc(centerx, centery, 8, 0, 2 * math.pi)
            cr.set_source(grad)
            cr.fill()

            # White outline
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.arc(centerx, centery, 8, 0, 2 * math.pi)
            cr.stroke()

        self._outline_text(cr, w, h, 30, _("Select an area by clicking and dragging."))
        self._outline_text(cr, w, h + 50, 26, _("Press ENTER to confirm or ESC to cancel"))

        self._outline_text(cr, w, h + 100, 20, "({0} × {1})".format(abs(self.width + 1), abs(self.height + 1)))
        cr.set_operator(cairo.OPERATOR_SOURCE)

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

    def accept_area(self):
        self.gdk_win.set_cursor(self.last_cursor)
        self.window.hide()
        if self.startx > self.endx:
            self.startx, self.endx = self.endx, self.startx

        if self.g_startx > self.g_endx:
            self.g_startx, self.g_endx = self.g_endx, self.g_startx

        if self.starty > self.endy:
            self.starty, self.endy = self.endy, self.starty

        if self.g_starty > self.g_endy:
            self.g_starty, self.g_endy = self.g_endy, self.g_starty

        if self.startx < 0:
            self.startx = 0

        if self.starty < 0:
            self.starty = 0

        self.width = abs(self.endx - self.startx)
        self.height = abs(self.endy - self.starty)
        logger.debug("Selected coords: {0} {1} {2} {3}".format(self.g_startx, self.g_starty, self.g_endx, self.g_endy))
