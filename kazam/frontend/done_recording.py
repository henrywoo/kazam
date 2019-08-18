# -*- coding: utf-8 -*-
#
#       app.py
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

import os
import shutil
import logging
logger = logging.getLogger("Done Recording")

from gettext import gettext as _
from gi.repository import Gtk, GObject

from kazam.backend.prefs import *
from kazam.frontend.combobox import EditComboBox
from kazam.frontend.save_dialog import SaveDialog


class DoneRecording(Gtk.Window):

    __gsignals__ = {
        "save-done": (GObject.SIGNAL_RUN_LAST,
                      None,
                      [GObject.TYPE_PYOBJECT],),
        "edit-request": (GObject.SIGNAL_RUN_LAST,
                         None,
                         [GObject.TYPE_PYOBJECT],),
        "save-cancel": (GObject.SIGNAL_RUN_LAST,
                        None,
                        (),)
    }

    def __init__(self, icons, tempfile, codec, old_path):
        Gtk.Window.__init__(self, title="Kazam - " + _("Recording finished"))
        self.icons = icons
        self.tempfile = tempfile
        self.codec = codec
        self.action = ACTION_SAVE
        self.old_path = old_path
        self.set_position(Gtk.WindowPosition.NONE)

        # Setup UI
        self.set_border_width(10)
        self.vbox = Gtk.Box(spacing=20, orientation=Gtk.Orientation.VERTICAL)
        self.label_box = Gtk.Box()
        self.done_label = Gtk.Label(_("Kazam finished recording.\nWhat do you want to do now?"))
        self.label_box.add(self.done_label)
        self.grid = Gtk.Grid(row_spacing=10, column_spacing=5)
        self.radiobutton_edit = Gtk.RadioButton.new_with_label_from_widget(None, _("Edit with:"))
        self.combobox_editor = EditComboBox(self.icons)
        self.grid.add(self.radiobutton_edit)
        self.grid.attach_next_to(self.combobox_editor,
                                 self.radiobutton_edit,
                                 Gtk.PositionType.RIGHT,
                                 1, 1)
        self.radiobutton_save = Gtk.RadioButton.new_from_widget(self.radiobutton_edit)
        self.radiobutton_save.set_label(_("Save for later"))

        if self.combobox_editor.empty:
            self.radiobutton_edit.set_active(False)
            self.radiobutton_edit.set_sensitive(False)

        self.radiobutton_save.set_active(True)

        self.radiobutton_save.connect("toggled", self.cb_radiobutton_save_toggled)
        self.radiobutton_edit.connect("toggled", self.cb_radiobutton_edit_toggled)
        self.btn_cancel = Gtk.Button(label=_("Cancel"))
        self.btn_cancel.set_size_request(100, -1)
        self.btn_continue = Gtk.Button(label=_("Continue"))
        self.btn_continue.set_size_request(100, -1)

        self.btn_continue.connect("clicked", self.cb_continue_clicked)
        self.btn_cancel.connect("clicked", self.cb_cancel_clicked)

        self.hbox = Gtk.Box(spacing=10)
        self.left_hbox = Gtk.Box()
        self.right_hbox = Gtk.Box(spacing=5)

        self.right_hbox.pack_start(self.btn_cancel, False, True, 0)
        self.right_hbox.pack_start(self.btn_continue, False, True, 0)

        self.hbox.pack_start(self.left_hbox, True, True, 0)
        self.hbox.pack_start(self.right_hbox, False, False, 0)

        self.vbox.pack_start(self.label_box, True, True, 0)
        self.vbox.pack_start(self.grid, True, True, 0)
        self.vbox.pack_start(self.radiobutton_save, True, True, 0)
        self.vbox.pack_start(self.hbox, True, True, 0)
        self.add(self.vbox)
        self.connect("delete-event", self.cb_delete_event)
        self.set_resizable(False)
        self.show_all()
        self.present()

    def cb_continue_clicked(self, widget):
        if self.action == ACTION_EDIT:
            logger.debug("Continue - Edit.")
            (command, args) = self.combobox_editor.get_active_value()
            self.emit("edit-request", (command, args))
            self.destroy()
        else:
            self.set_sensitive(False)
            logger.debug("Continue - Save ({0}).".format(self.codec))
            (dialog, result, self.old_path) = SaveDialog(_("Save screencast"),
                                                         self.old_path, self.codec)

            if result == Gtk.ResponseType.OK:
                uri = os.path.join(dialog.get_current_folder(), dialog.get_filename())

                if not uri.endswith(CODEC_LIST[self.codec][3]):
                    uri += CODEC_LIST[self.codec][3]

                logger.debug("Moving from {} to {}".format(self.tempfile, uri))
                shutil.move(self.tempfile, uri)
                dialog.destroy()
                self.emit("save-done", self.old_path)
                self.destroy()
            else:
                logger.debug("Save cancelled.")
                self.set_sensitive(True)
                dialog.destroy()

    def cb_cancel_clicked(self, widget):
        self.emit("save-cancel")
        self.destroy()

    def cb_delete_event(self, widget, data):
        self.emit("save-cancel")
        self.destroy()

    def cb_radiobutton_save_toggled(self, widget):
        if not widget.get_active():
            return
        else:
            self.action = ACTION_SAVE
            self.combobox_editor.set_sensitive(False)

    def cb_radiobutton_edit_toggled(self, widget):
        if not widget.get_active():
            return
        else:
            self.action = ACTION_EDIT
            self.combobox_editor.set_sensitive(True)
