# -*- coding: utf-8 -*-
#
#       grabber.py
#
#       Copyright 2018 Henry Fuheng Wu <wufuheng@gmail.com>
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

import logging
import subprocess
import tempfile

logger = logging.getLogger("Grabber")

from gi.repository import GObject, Gtk, Gdk, GdkPixbuf, GdkX11

from kazam.backend.prefs import *
from kazam.frontend.save_dialog import SaveDialog
from gettext import gettext as _
from kazam.backend.neoocr import NeoOCR


class Grabber(GObject.GObject, NeoOCR):
    __gsignals__ = {
        "save-done": (GObject.SIGNAL_RUN_LAST,
                      None,
                      [GObject.TYPE_PYOBJECT],),
        "flush-done": (GObject.SIGNAL_RUN_LAST,
                       None,
                       (),),
    }

    def __init__(self, is_ocr=False, use_tesseract=True):
        GObject.GObject.__init__(self)
        NeoOCR.__init__(self, is_ocr, use_tesseract)
        logger.debug("Starting Grabber.")

    def setup_sources(self, video_source, area, xid, active=False, god=False):
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
            subprocess.call(['canberra-gtk-play', '-f', soundfile])

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
        if self.is_ocr:
            self.run_ocr()
        else:
            '''(dialog, result, self.old_path) = SaveDialog(_("Save capture"),
                                                                self.old_path, None, main_mode=MODE_SCREENSHOT)
            if result == Gtk.ResponseType.OK:
                uri = os.path.join(dialog.get_current_folder(), dialog.get_filename())
                self.save(uri)
            dialog.destroy()'''
            self.run_screenshot()
        self.emit("save-done", self.old_path)

    def autosave(self, filename):
        logger.debug("Autosaving to: {0}".format(filename))
        self.save(filename)
        self.emit("save-done", filename)

    def run_screenshot(self):
        if self.pixbuf is not None:
            self.show_screenshot_window()

    def show_screenshot_window(self):
        img_width = self.pixbuf.get_width()
        img_height = self.pixbuf.get_height()

        # Limit the image rendering area to a third of the window size

        # Get the size of the captured screenshot
        img_width = self.pixbuf.get_width()
        img_height = self.pixbuf.get_height()

        # Define the base size for the window
        margin_space = 0  # Space for margins
        button_area_height = 40  # Fixed height for the button area

        # Get the screen height and define a conservative max height for the window
        screen_height = Gdk.Screen.height()  # Get the screen height
        max_height = min(screen_height - 100, 400)  # Max height is 600 or screen height - 100

        # Calculate the window size based on the image size
        h = min(img_height + margin_space + button_area_height, max_height)
        w = min(img_width + 2 * margin_space, 600)  # Max width limited to 1000 pixels

        # Scale the image to fit within the calculated window size
        if img_height + button_area_height + margin_space > h:
            scale_y = (h - button_area_height - margin_space) / img_height
        else:
            scale_y = 1.0

        scale_x = (w - 2 * margin_space) / img_width
        scale = min(scale_x, scale_y, 1.0)

        # Create a new window
        window = Gtk.Dialog(title="Screenshot Result", transient_for=None, flags=0)
        window.set_default_size(w, h)
        window.set_modal(True)
        #window.set_resizable(False)  # Make the window size unchangeable
        window.set_transient_for(self.get_main_window())

        content_area = window.get_content_area()

        # Create a label with the image's width and height
        info_label = Gtk.Label(label=f"Image Size: {img_width} x {img_height}")
        content_area.pack_start(info_label, False, False, 5)  # Add some padding

        # Create a vertical box to hold the image and buttons with minimal spacing
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        vbox.set_margin_top(10)
        vbox.set_margin_start(margin_space)
        vbox.set_margin_end(margin_space)
        content_area.add(vbox)

        # Center the image in the middle of the window
        image_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(image_box, True, True, 0)

        image = Gtk.Image()

        scaled_pixbuf = self.pixbuf.scale_simple(int(img_width * scale), int(img_height * scale),
                                                 GdkPixbuf.InterpType.BILINEAR)
        image.set_from_pixbuf(scaled_pixbuf)
        image_box.pack_start(image, True, True, 0)

        # Add some space between the image and the separator
        vbox.pack_start(Gtk.Box(orientation=Gtk.Orientation.VERTICAL), False,
                        False, 0)

        # Add the separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(separator, False, False, 0)

        # Add some space between the separator and the buttons
        vbox.pack_start(Gtk.Box(orientation=Gtk.Orientation.VERTICAL),
                        False, False, 0)

        # Create a fixed-height box for buttons at the bottom
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_size_request(-1, button_area_height)  # Fixed height for buttons
        vbox.pack_end(button_box, False, False, 0)

        copy_image_button = Gtk.Button(label="Copy Image to Clipboard")
        copy_image_button.connect("clicked", self.on_copy_image_button_clicked, self.pixbuf)
        button_box.pack_start(copy_image_button, True, True, 0)

        save_image_button = Gtk.Button(label="Save Image As")
        save_image_button.connect("clicked", self.on_save_image_button_clicked, None)
        button_box.pack_start(save_image_button, True, True, 0)

        edit_image_button = Gtk.Button(label="Edit Image")
        edit_image_button.connect("clicked", self.on_edit_image_button_clicked, None)
        button_box.pack_start(edit_image_button, True, True, 0)

        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close_button_clicked, window)
        button_box.pack_start(close_button, True, True, 0)

        window.show_all()

    def on_copy_image_button_clicked(self, button, pixbuf):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_image(pixbuf)

    def on_save_image_button_clicked(self, button, _):
        dialog, result, _ = SaveDialog(title="Save Screenshot As", old_path=None, codec=None, main_mode=MODE_SCREENSHOT)
        if result == Gtk.ResponseType.OK:
            save_path = dialog.get_filename()
            self.save(save_path)
        dialog.destroy()

    def on_edit_image_button_clicked(self, button, _):
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_filename = temp_file.name
            self.save(temp_filename)
            subprocess.call(['xdg-open', temp_filename])

    def on_close_button_clicked(self, button, window):
        window.destroy()
