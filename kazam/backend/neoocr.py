# -*- coding: utf-8 -*-
#
#       grabber.py
#
#       Copyright 2024 <wufuheng@gmail.com>
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

import tempfile
import os
from gi.repository import GObject, Gtk, Gdk, GdkPixbuf, GdkX11
from kazam.frontend.save_dialog import SaveDialog
from kazam.backend.prefs import MODE_OCR

my_rapidocr = None

class NeoOCR:
    def __init__(self, is_ocr=True, use_tesseract=True):
        self.is_ocr = is_ocr
        self.use_tesseract = use_tesseract

    def run_ocr(self):
        if self.pixbuf is not None and self.is_ocr:
            if self.use_tesseract:
                self.run_tesseract_ocr()
            else:
                self.run_rapidocr_ocr()
        else:
            print("No image data to process.")

    def run_tesseract_ocr(self):
        import pytesseract
        from PIL import Image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_filename = temp_file.name
            self.pixbuf.savev(temp_filename, "png", "", "")
        image = Image.open(temp_filename)
        text = pytesseract.image_to_string(image)
        self.show_text_window(text if text else "", temp_filename)
        #os.remove(temp_filename)

    def run_rapidocr_ocr(self):
        global my_rapidocr
        if my_rapidocr is None:
            from rapidocr_onnxruntime import RapidOCR  # Import RapidOCR
            my_rapidocr = RapidOCR()
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_filename = temp_file.name
            self.pixbuf.savev(temp_filename, "png", "", "")
        result, elapse = my_rapidocr(temp_filename)
        # can be optimized with layout analysis
        text = "\n".join([line[1] for line in result]) if result else ""  # Extracting text from result
        self.show_text_window(text, temp_filename)
        #os.remove(temp_filename)

    def show_text_window(self, text, image_path):
        # Create a new window
        window = Gtk.Dialog(title="OCR Result", transient_for=None, flags=0)
        w, h = 320, 600
        window.set_default_size(w, h)
        window.set_modal(True)  # Make the window modal
        window.set_transient_for(self.get_main_window())  # Set the main window as the parent

        # Create a vertical box container
        content_area = window.get_content_area()

        # Get image information
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
        img_width = pixbuf.get_width()
        img_height = pixbuf.get_height()

        # Create a label with the image's width and height
        info_label = Gtk.Label(label=f"Image Size: {img_width} x {img_height}")
        content_area.pack_start(info_label, False, False, 5)  # Add some padding

        # Limit the image rendering area to a third of the window size
        image_area_height = h // 3  # One third of the window height
        image_area_width = w  # Full window width

        # Upper part for displaying the image
        image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_area.pack_start(image_box, False, False, 0)  # Set expand and fill to False

        image = Gtk.Image()

        # Resize the image if it's too big to fit the designated area
        scale_x = image_area_width / img_width
        scale_y = image_area_height / img_height
        scale = min(scale_x, scale_y, 1.0)  # Do not upscale

        # Apply scaling
        scaled_pixbuf = pixbuf.scale_simple(int(img_width * scale), int(img_height * scale),
                                            GdkPixbuf.InterpType.BILINEAR)
        image.set_from_pixbuf(scaled_pixbuf)
        image_box.pack_start(image, False, False, 0)  # Set expand and fill to False

        # Lower part for the text and buttons
        lower_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content_area.pack_start(lower_box, True, True, 0)

        # Create a scrolled window for text
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        lower_box.pack_start(scrolled_window, True, True, 0)

        # Create a text view
        textview = Gtk.TextView()
        textbuffer = textview.get_buffer()
        textbuffer.set_text(text)
        scrolled_window.add(textview)

        # Create a horizontal box for buttons
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lower_box.pack_start(hbox, False, False, 0)

        # Copy OCR Text to Clipboard button
        copy_text_button = Gtk.Button(label="Copy OCR Text to Clipboard")
        copy_text_button.connect("clicked", self.on_copy_text_button_clicked, textbuffer)
        hbox.pack_start(copy_text_button, True, True, 0)

        # Copy Image to Clipboard button
        copy_image_button = Gtk.Button(label="Copy Image to Clipboard")
        copy_image_button.connect("clicked", self.on_copy_image_button_clicked, pixbuf)
        hbox.pack_start(copy_image_button, True, True, 0)

        # Save Image As button
        save_image_button = Gtk.Button(label="Save Image As")
        save_image_button.connect("clicked", self.on_save_image_button_clicked, image_path)
        hbox.pack_start(save_image_button, True, True, 0)

        # Save OCR Result As button
        save_text_button = Gtk.Button(label="Save OCR Result As")
        save_text_button.connect("clicked", self.on_save_text_button_clicked, textbuffer)
        hbox.pack_start(save_text_button, True, True, 0)

        # Close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close_button_clicked, window)
        hbox.pack_start(close_button, True, True, 0)

        # Show all components
        window.show_all()

    def on_copy_text_button_clicked(self, button, textbuffer):
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        start_iter, end_iter = textbuffer.get_bounds()
        text = textbuffer.get_text(start_iter, end_iter, True)
        clipboard.set_text(text, -1)

    def on_copy_image_button_clicked(self, button, pixbuf):
        # Print the size of the pixbuf to verify its resolution
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        print(f"Pixbuf size: {width} x {height}")

        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_image(pixbuf)

    def on_save_image_button_clicked(self, button, image_path):
        dialog, result, _ = SaveDialog(title="Save Image As", old_path=None, codec=None, main_mode=MODE_OCR)
        if result == Gtk.ResponseType.OK:
            save_path = dialog.get_filename()
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
            pixbuf.savev(save_path, "png", [], [])
        dialog.destroy()

    def on_save_text_button_clicked(self, button, textbuffer):
        dialog, result, _ = SaveDialog(title="Save OCR Result As", old_path=None, codec='text', main_mode=MODE_OCR)
        if result == Gtk.ResponseType.OK:
            save_path = dialog.get_filename()
            start_iter, end_iter = textbuffer.get_bounds()
            text = textbuffer.get_text(start_iter, end_iter, True)
            with open(save_path, 'w') as file:
                file.write(text)
        dialog.destroy()

    def on_close_button_clicked(self, button, window):
        window.destroy()

    def set_main_window(self, window):
        self.main_window = window

    def get_main_window(self):
        return self.main_window
