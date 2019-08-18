# -*- coding: utf-8 -*-
#
#       main_menu.py
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

from gettext import gettext as _

from gi.repository import Gtk, GObject

MENUBAR = """
    <ui>
        <menubar name='MenuBar'>
            <menu action='FileMenu'>
                <menuitem action='FilePreferences' />
                <menuitem action='FileQuit' />
            </menu>
            <menu action='HelpMenu'>
                <menuitem action='HelpAbout' />
            </menu>
        </menubar>
</ui>
"""


class MainMenu(GObject.GObject):
    __gsignals__ = {
        "file-preferences": (GObject.SIGNAL_RUN_LAST,
                             None,
                             (),
                             ),
        "file-quit": (GObject.SIGNAL_RUN_LAST,
                      None,
                      (),
                      ),
        "help-about": (GObject.SIGNAL_RUN_LAST,
                       None,
                       (),
                       ),
    }

    def __init__(self):
        GObject.GObject.__init__(self)

        self.action_group = Gtk.ActionGroup("kazam_actions")
        self.action_group.add_actions([
            ("FileMenu", None, _("File")),
            ("FileQuit", Gtk.STOCK_QUIT, _("Quit"), None, _("Quit Kazam"),
             self.cb_file_quit),
            ("FilePreferences", Gtk.STOCK_PREFERENCES, _("Preferences"), None, _("Open preferences"),
             self.cb_file_preferences),
            ("HelpMenu", None, _("Help")),
            ("HelpAbout", None, _("About"), None, _("About Kazam"),
             self.cb_help_about)
        ])

        self.uimanager = Gtk.UIManager()
        self.uimanager.add_ui_from_string(MENUBAR)
        self.uimanager.insert_action_group(self.action_group)
        self.menubar = self.uimanager.get_widget("/MenuBar")

    def cb_file_quit(self, action):
        self.emit("file-quit")

    def cb_file_preferences(self, action):
        self.emit("file-preferences")

    def cb_help_about(self, action):
        self.emit("help-about")
