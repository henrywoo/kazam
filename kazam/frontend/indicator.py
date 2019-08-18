# -*- coding: utf-8 -*-
#
#       indicator.py
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

import logging
logger = logging.getLogger("Indicator")

from gettext import gettext as _
from gi.repository import Gtk, GObject, GLib

from kazam.backend.prefs import *


class KazamSuperIndicator(GObject.GObject):
    __gsignals__ = {
        "indicator-pause-request": (GObject.SIGNAL_RUN_LAST,
                                    None,
                                    (), ),
        "indicator-unpause-request": (GObject.SIGNAL_RUN_LAST,
                                      None,
                                      (), ),
        "indicator-quit-request": (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (), ),
        "indicator-show-request": (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (), ),
        "indicator-stop-request": (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (), ),
        "indicator-start-request": (GObject.SIGNAL_RUN_LAST,
                                    None,
                                    (), ),

        "indicator-about-request": (GObject.SIGNAL_RUN_LAST,
                                    None,
                                    (), ),
    }

    def __init__(self, silent=False):
        super(KazamSuperIndicator, self).__init__()
        self.blink_icon = BLINK_STOP_ICON
        self.blink_state = False
        self.blink_mode = BLINK_SLOW
        self.recording = False
        self.silent = silent
        logger.debug("Indicatior silent: {0}".format(self.silent))

        self.menu = Gtk.Menu()

        self.menuitem_start = Gtk.MenuItem(_("Start recording"))
        self.menuitem_start.set_sensitive(True)
        self.menuitem_start.connect("activate", self.on_menuitem_start_activate)

        self.menuitem_pause = Gtk.CheckMenuItem(_("Pause recording"))
        self.menuitem_pause.set_sensitive(False)
        self.menuitem_pause.connect("toggled", self.on_menuitem_pause_activate)

        self.menuitem_finish = Gtk.MenuItem(_("Finish recording"))
        self.menuitem_finish.set_sensitive(False)
        self.menuitem_finish.connect("activate", self.on_menuitem_finish_activate)

        self.menuitem_separator = Gtk.SeparatorMenuItem()

        self.menuitem_quit = Gtk.MenuItem(_("Quit"))
        self.menuitem_quit.connect("activate", self.on_menuitem_quit_activate)

        self.menu.append(self.menuitem_start)
        self.menu.append(self.menuitem_pause)
        self.menu.append(self.menuitem_finish)
        self.menu.append(self.menuitem_separator)
        self.menu.append(self.menuitem_quit)

        self.menu.show_all()

        #
        # Setup keybindings - Hardcore way
        #
        try:
            from gi.repository import Keybinder
            logger.debug("Trying to bind hotkeys.")
            Keybinder.init()
            Keybinder.bind("<Super><Ctrl>R", self.cb_hotkeys, "start-request")
            Keybinder.bind("<Super><Ctrl>F", self.cb_hotkeys, "stop-request")
            Keybinder.bind("<Super><Ctrl>P", self.cb_hotkeys, "pause-request")
            Keybinder.bind("<Super><Ctrl>W", self.cb_hotkeys, "show-request")
            Keybinder.bind("<Super><Ctrl>Q", self.cb_hotkeys, "quit-request")
            self.recording = False
        except ImportError:
            logger.info("Unable to import Keybinder, hotkeys not available.")

    def cb_hotkeys(self, key, action):
        logger.debug("KEY {0}, ACTION {1}".format(key, action))
        if action == "start-request" and not self.recording:
            self.on_menuitem_start_activate(None)
        elif action == "stop-request" and self.recording:
            self.on_menuitem_finish_activate(None)
        elif action == "pause-request" and self.recording:
            if not self.menuitem_pause.get_active():
                self.menuitem_pause.set_active(True)
            else:
                self.menuitem_pause.set_active(False)
        elif action == "show-request" and not self.recording:
            self.emit("indicator-show-request")
        elif action == "quit-request" and not self.recording:
            self.emit("indicator-quit-request")

    def on_menuitem_pause_activate(self, menuitem):
        if self.menuitem_pause.get_active():
            self.emit("indicator-pause-request")
        else:
            self.emit("indicator-unpause-request")

    def on_menuitem_start_activate(self, menuitem):
        self.recording = True
        self.emit("indicator-start-request")

    def on_menuitem_finish_activate(self, menuitem):
        self.recording = False
        self.menuitem_start.set_sensitive(True)
        self.menuitem_pause.set_sensitive(False)
        self.menuitem_pause.set_active(False)
        self.menuitem_finish.set_sensitive(False)
        self.menuitem_quit.set_sensitive(True)
        self.emit("indicator-stop-request")

    def on_menuitem_quit_activate(self, menuitem):
        self.emit("indicator-quit-request")

try:
    from gi.repository import AppIndicator3

    class KazamIndicator(KazamSuperIndicator):

        def __init__(self, silent=False):
            super(KazamIndicator, self).__init__(silent)
            self.silent = silent

            self.indicator = AppIndicator3.Indicator.new("kazam",
                                                         "kazam-stopped",
                                                         AppIndicator3.IndicatorCategory.APPLICATION_STATUS)

            self.indicator.set_menu(self.menu)
            self.indicator.set_attention_icon("kazam-recording")
            self.indicator.set_icon("kazam-stopped")

            if self.silent:
                self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
            else:
                self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        def hide_it(self):
            self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

        def show_it(self):
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        def on_menuitem_pause_activate(self, menuitem):
            if menuitem.get_active():
                self.indicator.set_attention_icon("kazam-paused")
                logger.debug("Recording paused.")
            else:
                self.indicator.set_attention_icon("kazam-recording")
                logger.debug("Recording resumed.")
            KazamSuperIndicator.on_menuitem_pause_activate(self, menuitem)

        def on_menuitem_finish_activate(self, menuitem):
            logger.debug("Recording stopped.")
            if not self.silent:
                self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            KazamSuperIndicator.on_menuitem_finish_activate(self, menuitem)

        def blink_set_state(self, state):
            if state == BLINK_STOP:
                self.blink_state = BLINK_STOP
                self.indicator.set_icon("kazam-stopped")
            elif state == BLINK_START:
                self.blink_state = BLINK_SLOW
                GLib.timeout_add(500, self.blink)
            elif state == BLINK_SLOW:
                self.blink_state = BLINK_SLOW
            elif state == BLINK_FAST:
                self.blink_state = BLINK_FAST

        def blink(self):
            if self.blink_state != BLINK_STOP:
                if self.blink_icon == BLINK_READY_ICON:
                    if not self.silent:
                        self.indicator.set_icon("kazam-stopped")
                    self.blink_icon = BLINK_STOP_ICON
                else:
                    if not self.silent:
                        self.indicator.set_icon("kazam-countdown")
                    self.blink_icon = BLINK_READY_ICON

                if self.blink_state == BLINK_SLOW:
                    GLib.timeout_add(500, self.blink)
                elif self.blink_state == BLINK_FAST:
                    GLib.timeout_add(200, self.blink)

        def start_recording(self):
            logger.debug("Recording started.")
            if not self.silent:
                self.indicator.set_status(AppIndicator3.IndicatorStatus.ATTENTION)

except ImportError:
    #
    # AppIndicator failed to import, not running Ubuntu?
    # Fallback to Gtk.StatusIcon.
    #
    class KazamIndicator(KazamSuperIndicator):

        def __init__(self, silent=False):
            super(KazamIndicator, self).__init__()
            self.silent = silent

            self.indicator = Gtk.StatusIcon()
            self.indicator.set_from_icon_name("kazam-stopped")
            self.indicator.connect("popup-menu", self.cb_indicator_popup_menu)
            self.indicator.connect("activate", self.cb_indicator_activate)

            if self.silent:
                self.indicator.set_visible(False)

        def cb_indicator_activate(self, widget):
            def position(menu, widget):
                return (Gtk.StatusIcon.position_menu(self.menu, widget))
            self.menu.popup(None, None, position, self.indicator, 0, Gtk.get_current_event_time())

        def cb_indicator_popup_menu(self, icon, button, time):
            def position(menu, icon):
                return (Gtk.StatusIcon.position_menu(self.menu, icon))
            self.menu.popup(None, None, position, self.indicator, button, time)

        def on_menuitem_finish_activate(self, menuitem):
            logger.debug("Recording stopped.")
            self.indicator.set_from_icon_name("kazam-stopped")
            KazamSuperIndicator.on_menuitem_finish_activate(self, menuitem)

        def on_menuitem_pause_activate(self, menuitem):
            if menuitem.get_active():
                self.indicator.set_from_icon_name("kazam-paused")
                logger.debug("Recording paused.")
            else:
                self.indicator.set_from_icon_name("kazam-recording")
                logger.debug("Recording resumed.")
            KazamSuperIndicator.on_menuitem_pause_activate(self, menuitem)

        def blink_set_state(self, state):
            if state == BLINK_STOP:
                self.blink_state = BLINK_STOP
                self.indicator.set_from_icon_name("kazam-stopped")
            elif state == BLINK_START:
                self.blink_state = BLINK_SLOW
                GLib.timeout_add(500, self.blink)
            elif state == BLINK_SLOW:
                self.blink_state = BLINK_SLOW
            elif state == BLINK_FAST:
                self.blink_state = BLINK_FAST

        def blink(self):
            if self.blink_state != BLINK_STOP:
                if self.blink_icon == BLINK_READY_ICON:
                    self.indicator.set_from_icon_name("kazam-stopped")
                    self.blink_icon = BLINK_STOP_ICON
                else:
                    self.indicator.set_from_icon_name("kazam-countdown")
                    self.blink_icon = BLINK_READY_ICON

                if self.blink_state == BLINK_SLOW:
                    GLib.timeout_add(500, self.blink)
                elif self.blink_state == BLINK_FAST:
                    GLib.timeout_add(200, self.blink)

        def start_recording(self):
            logger.debug("Recording started.")
            self.indicator.set_from_icon_name("kazam-recording")

        def hide_it(self):
            self.indicator.set_visible(False)

        def show_it(self):
            self.indicator.set_visible(True)
