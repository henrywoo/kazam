# -*- coding: utf-8 -*-
#
#       window_keypress.py
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

import math
import cairo
import logging
logger = logging.getLogger("Window Keypress")

from gi.repository import Gtk, GObject, Gdk, GdkX11, GLib
from kazam.backend.prefs import *


class KeypressWindow(GObject.GObject):
    def __init__(self, show_window=True):
        super(KeypressWindow, self).__init__()
        logger.debug("Initializing Keypress window.")

        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("draw", self.cb_draw)
        self.window.connect("screen-changed", self.onScreenChanged)
        self.window.set_app_paintable(True)
        self.window.set_decorated(False)
        self.window.set_title("CountdownWindow")
        self.window.set_keep_above(True)
        self.window.set_focus_on_map(False)
        self.window.set_accept_focus(False)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)

        self.cursor_ind = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.cursor_ind.connect("delete-event", Gtk.main_quit)
        self.cursor_ind.connect("draw", self.cb_cursor_ind_draw)
        self.cursor_ind.set_app_paintable(True)
        self.cursor_ind.set_decorated(False)
        self.cursor_ind.set_title("CountdownWindow")
        self.cursor_ind.set_keep_above(True)
        self.cursor_ind.set_focus_on_map(False)
        self.cursor_ind.set_accept_focus(False)
        self.cursor_ind.set_skip_pager_hint(True)
        self.cursor_ind.set_skip_taskbar_hint(True)
        self.cursor_ind.set_size_request(50, 50)
        self.cursor_ind.set_default_geometry(50, 50)

        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()

        self.disp = GdkX11.X11Display.get_default()
        self.dm = Gdk.Display.get_device_manager(self.disp)
        self.pntr_device = self.dm.get_client_pointer()

        if self.visual is not None and self.screen.is_composited():
            logger.debug("Compositing window manager detected.")
            self.window.set_visual(self.visual)
            self.cursor_ind.set_visual(self.visual)
            self.compositing = True
        else:
            logger.warning("Compositing window manager not found, expect the unexpected.")
            self.compositing = False

        # make window click-through, this needs pycairo 1.10.0 for python3
        # to work
        rect = cairo.RectangleInt(0, 0, 1, 1)
        region = cairo.Region(rect)
        if (not region.is_empty()):
            self.window.input_shape_combine_region(None)
            self.window.input_shape_combine_region(region)
            self.cursor_ind.input_shape_combine_region(None)
            self.cursor_ind.input_shape_combine_region(region)

        # make sure that gtk-window opens with a RGBA-visual
        self.onScreenChanged(self.window, None)
        self.window.set_opacity(0)
        self.window.realize()
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        transparent = Gdk.RGBA(0.0, 0.0, 0.0, 0.0)
        gdkwindow = self.window.get_window()
        gdkwindow.set_background_rgba(transparent)

        screen = HW.screens[prefs.current_screen]
        width = 1
        height = 1
        self.window.set_size_request(width, height)
        self.window.set_default_geometry(width, height)
        self.window.move(int(screen['width'] / 2 - width / 2), screen['height'] - 150)

        self.alpha = 0

        self.buffer = ""

        self._in = False
        self._out = False
        self.f_t = None
        self.previous_key = None
        self.keys_pressed = False
        self.window.show_all()

        self.modifiers = [False, False, False, False]

    #
    # Rewrite this
    #
    def show(self, ev_type, value, action):
        logger.debug("Current buffer: {}".format(self.buffer))
        if (ev_type == 'KeyStr' or ev_type == 'KeySym') and action == 'Press':
            if value != self.previous_key:
                if self.f_t:
                    GLib.source_remove(self.f_t)
                    self.f_t = None
                if value.startswith('Shift'):
                    self.modifiers[K_SHIFT] = True
                elif value.startswith('Control'):
                    self.modifiers[K_CTRL] = True
                elif value.startswith('Super'):
                    self.modifiers[K_SUPER] = True
                elif value.startswith('Alt'):
                    self.modifiers[K_ALT] = True
                else:
                        self.buffer += value
                        self.previous_key = value
                #
                # Show keys only if modifiers are pressed
                #
                if True in self.modifiers:
                    self._in = True
                    # self.f_t = GLib.timeout_add(1300, self.fade_out, self.window)
                    self.window.queue_draw()

        elif (ev_type == 'KeyStr' or ev_type == 'KeySym') and action == 'Release':
            if value.startswith('Shift'):
                self.modifiers[K_SHIFT] = False
            elif value.startswith('Control'):
                self.modifiers[K_CTRL] = False
            elif value.startswith('Super'):
                self.modifiers[K_SUPER] = False
            elif value.startswith('Alt'):
                self.modifiers[K_ALT] = False

            if not all(self.modifiers) and not any(self.modifiers):  # Fadeout if none of the modifiers are pressed
                logger.debug("Fadeout!")
                self.fade_out(self.window)

        elif ev_type == 'MouseButton' and action == 'Press':
            if value in ['1', '2', '3']:  # For now ignore all the other buttons
                self.show_cursor()

    def onScreenChanged(self, widget, oldScreen):
        screen = widget.get_screen()
        visual = screen.get_rgba_visual()
        if visual is None:
            visual = screen.get_system_visual()
        widget.set_visual(visual)

    def fade(self, widget):
        widget.queue_draw()
        return True

    def fade_out(self, widget):
        self._out = True
        self.buffer = ""
        self.previous_key = None
        widget.queue_draw()
        self.modifiers[K_SHIFT] = False
        self.modifiers[K_CTRL] = False
        self.modifiers[K_SUPER] = False
        self.modifiers[K_ALT] = False
        return True

    def cb_draw(self, widget, cr):
        buf = " + ".join([i[0] for i in zip(KEY_STRINGS, self.modifiers) if i[1]])
        buf = " ".join((buf, self.buffer))

        w, h = self._text_size(cr, 20, buf)

        self.window.set_size_request(w + 20, 50)
        self.window.set_default_geometry(w + 20, 50)
        Ww, Wh = widget.get_size()
        widget.set_opacity(self.alpha)
        cr.set_source_rgba(.4, .4, .4, .7)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        self._outline_text(cr, 10, Wh - 15, 20, buf)

        if self._in:
            if self.alpha >= 1:
                self._in = False
                return False
            else:
                self.alpha += 0.10
                self.f_ret = GLib.timeout_add(2, self.fade, self.window)
            return True

        elif self._out:
            if self.alpha <= 0:
                self._out = False
                return False
            else:
                self.alpha -= 0.10
                self.f_ret = GLib.timeout_add(2, self.fade, self.window)
            return True

    def _outline_text(self, cr, x, y, size, text):
        cr.set_font_size(size)
        try:
            cr.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        except:  # Think of what to do here ...
            pass
        cr.set_line_width(2.0)
        if self.compositing:
            cr.set_source_rgba(0.4, 0.4, 0.4, 1.0)
        else:
            cr.set_source_rgb(0.4, 0.4, 0.4)

        cr.move_to(x, y)
        cr.text_path(text)
        cr.stroke()
        if self.compositing:
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        else:
            cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.move_to(x, y)
        cr.show_text(text)

    def _text_size(self, cr, size, text):
        cr.set_font_size(size)
        try:
            cr.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        except:  # Think of what to do here ...
            pass
        te = cr.text_extents(text)
        return (te[2], te[3])

    def show_cursor(self):
        self.c_alpha = 1
        self.disp = GdkX11.X11Display.get_default()
        self.dm = Gdk.Display.get_device_manager(self.disp)
        self.pntr_device = self.dm.get_client_pointer()
        (scr, x, y) = self.pntr_device.get_position()
        self.cursor_ind.move(x - 25, y - 25)
        self.cursor_ind.show_all()
        self.f_t = GLib.timeout_add(200, self.fade, self.cursor_ind)

    def cb_cursor_ind_draw(self, widget, cr):
        cr.set_source_rgba(.0, .0, .0, .7)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_line_width(9)
        cr.set_source_rgba(0.7, 0.7, 0.0, self.c_alpha)
        w, h = self.cursor_ind.get_size()
        cr.translate(w / 2, h / 2)
        cr.arc(0, 0, 20, 0, 2 * math.pi)
        cr.stroke_preserve()
        cr.set_source_rgba(0.7, 0.7, 0.0, self.c_alpha)
        cr.fill()

        if self.c_alpha <= 0:
            return False
        else:
            self.c_alpha -= 0.05
            self.c_ret = GLib.timeout_add(2, self.fade, self.cursor_ind)
        return True
