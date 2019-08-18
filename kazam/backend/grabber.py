# -*- coding: utf-8 -*-
#
#       grabber.py
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


import os
import subprocess
import logging
logger = logging.getLogger("Grabber")

from gi.repository import GObject, Gtk, Gdk, GdkPixbuf, GdkX11

from kazam.backend.prefs import *
from kazam.frontend.save_dialog import SaveDialog
from gettext import gettext as _

class Grabber(GObject.GObject):
    __gsignals__ = {
        "save-done"       : (GObject.SIGNAL_RUN_LAST,
                             None,
                             [GObject.TYPE_PYOBJECT],),
        "flush-done"      : (GObject.SIGNAL_RUN_LAST,
                             None,
                             (),),
        }

    def __init__(self):
        GObject.GObject.__init__(self)
        logger.debug("Starting Grabber.")


    def setup_sources(self, video_source, area, xid, active = False, god = False):
        self.video_source = video_source
        self.area = area
        self.xid = xid
        self.god = god
        if active:
            from gi.repository import GdkX11
            active_win = HW.default_screen.get_active_window()
            self.xid = GdkX11.X11Window.get_xid(active_win)

        logger.debug("Grabber source: {0}, {1}, {2}, {3}".format(self.video_source['x'],
                                                                 self.video_source['y'],
                                                                 self.video_source['width'],
                                                                 self.video_source['height']))

    def grab(self):
        self.pixbuf = None
        disp = GdkX11.X11Display.get_default()
        dm = Gdk.Display.get_device_manager(disp)
        pntr_device = dm.get_client_pointer()

        #
        # Rewrite this, because it sucks
        #
        if prefs.shutter_sound and (not self.god):
            soundfile = os.path.join(prefs.datadir, 'sounds', prefs.sound_files[prefs.shutter_type])
            subprocess.call(['/usr/bin/canberra-gtk-play', '-f', soundfile])

        if self.xid:
            if prefs.capture_borders_pic:
                app_win = GdkX11.X11Window.foreign_new_for_display(disp, self.xid)
                (rx, ry, rw, rh) = app_win.get_geometry()
                area = app_win.get_frame_extents()
                (fx, fy, fw, fh) = (area.x, area.y, area.width, area.height)
                win = Gdk.get_default_root_window()
                logger.debug("Coordinates w: RX {0} RY {1} RW {2} RH {3}".format(rx, ry, rw, rh))
                logger.debug("Coordinates f: FX {0} FY {1} FW {2} FH {3}".format(fx, fy, fw, fh))
                dx = fw - rw
                dy = fh - rh
                (x, y, w, h) = (fx, fy, fw, fh)
                logger.debug("Coordinates delta: DX {0} DY {1}".format(dx, dy))
            else:
                win = GdkX11.X11Window.foreign_new_for_display(disp, self.xid)
                (x, y, w, h) = win.get_geometry()
        else:
            win = Gdk.get_default_root_window()
            (x, y, w, h) = (self.video_source['x'],
                            self.video_source['y'],
                            self.video_source['width'],
                            self.video_source['height'])

        self.pixbuf = Gdk.pixbuf_get_from_window(win, x, y, w, h)
        logger.debug("Coordinates     X {0}  Y {1}  W {2}  H {3}".format(x, y, w, h))

        # Code below partially solves problem with overlapping windows.
        # Partially only because if something is overlapping window frame
        # it will be captured where the frame should be and also
        # because it doesn't work as it should. Offset trouble.
        #
        #if self.xid and prefs.capture_borders_pic:
        #    cw_pixbuf = Gdk.pixbuf_get_from_window(app_win, rx, ry, rw, rh)
        #    cw_pixbuf.composite(self.pixbuf, rx, ry, rw, rh,
        #                        dx,
        #                        dy,
        #                        1.0,
        #                        1.0,
        #                        GdkPixbuf.InterpType.BILINEAR,
        #                        255)

        if prefs.capture_cursor_pic:
            logger.debug("Adding cursor.")

            cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.LEFT_PTR)
            c_picbuf = Gdk.Cursor.get_image(cursor)

            if self.xid and prefs.capture_borders_pic:
                pointer = app_win.get_device_position(pntr_device)
                (px, py) = (pointer[1], pointer[2])
                logger.debug("XID cursor: {0} {1}".format(px, py))
                c_picbuf.composite(self.pixbuf, rx, ry, rw, rh,
                                   px + dx - 6,
                                   py + dy - 2,
                                   1.0,
                                   1.0,
                                   GdkPixbuf.InterpType.BILINEAR,
                                   255)

            else:
                (scr, px, py) = pntr_device.get_position()
                cur = scr.get_monitor_at_point(x, y)

                px = px - HW.screens[cur]['x']
                py = py - HW.screens[cur]['y']

                #
                # Cursor is offset by 6 pixels to the right and 2 down
                #
                c_picbuf.composite(self.pixbuf, 0, 0, w - 1, h - 1,
                                   px - 6,
                                   py - 2,
                                   1.0,
                                   1.0,
                                   GdkPixbuf.InterpType.BILINEAR,
                                   255)

                logger.debug("Cursor coords: {0} {1}".format(px, py))

        if self.area is not None:
            logger.debug("Cropping image.")
            self.area_buf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, self.area[4], self.area[5])
            self.pixbuf.copy_area(self.area[0], self.area[1], self.area[4], self.area[5], self.area_buf, 0, 0)
            self.pixbuf = None
            self.pixbuf = self.area_buf

        self.emit("flush-done")

    def save(self, filename):
        if self.pixbuf is not None:
            self.pixbuf.savev(filename, "png", "", "")

    def save_capture(self, old_path):
        logger.debug("Saving screenshot.")
        self.old_path = old_path
        (dialog, result, self.old_path) = SaveDialog(_("Save capture"),
                                                     self.old_path, None, main_mode=MODE_SCREENSHOT)

        if result == Gtk.ResponseType.OK:
            uri = os.path.join(dialog.get_current_folder(), dialog.get_filename())

            self.save(uri)

        dialog.destroy()
        self.emit("save-done", self.old_path)

    def autosave(self, filename):
        logger.debug("Autosaving to: {0}".format(filename))
        self.save(filename)
        self.emit("save-done", filename)
