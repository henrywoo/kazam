#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       instant.py
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

import sys
import logging

from gi.repository import Gtk, GObject

from kazam.utils import *
from kazam.backend.prefs import *
from kazam.backend.grabber import Grabber

logger = logging.getLogger("Instant")


class InstantApp(GObject.GObject):

    def __init__(self, datadir, dist, debug, mode, preferences=False):
        GObject.GObject.__init__(self)
        logger.debug("Setting variables.{0}".format(datadir))

        self.mode = mode
        self.take = 0

        prefs.datadir = datadir
        prefs.debug = debug
        prefs.dist = dist
        prefs.get_sound_files()

        if preferences:
            logger.debug("Preferences requested.")
            from kazam.frontend.preferences import Preferences
            from kazam.pulseaudio.pulseaudio import pulseaudio_q
            prefs.pa_q = pulseaudio_q()
            prefs.pa_q.start()
            prefs.get_audio_sources()

            self.preferences_window = Preferences()
            self.preferences_window.connect("prefs-quit", self.cb_prefs_quit)
            self.preferences_window.open()

        else:
            self.old_path = None

            if HW.combined_screen:
                self.video_source = HW.combined_screen
            else:
                screen = HW.get_current_screen()
                self.video_source = HW.screens[screen]

            self.grabber = Grabber()
            self.grabber.connect("flush-done", self.cb_flush_done)
            self.grabber.connect("save-done", self.cb_save_done)

            if self.mode == MODE_AREA:
                logger.debug("Area ON.")
                from kazam.frontend.window_area import AreaWindow
                self.area_window = AreaWindow()
                self.area_window.connect("area-selected", self.cb_area_selected)
                self.area_window.connect("area-canceled", self.cb_area_canceled)
                self.area_window.window.show_all()
            elif self.mode == MODE_ALL:
                self.grabber.setup_sources(self.video_source, None, None)
                logger.debug("Grabbing screen")
                self.grabber.grab()
            elif self.mode == MODE_ACTIVE:
                self.grabber.setup_sources(self.video_source, None, None, active=True)
                logger.debug("Grabbing screen")
                self.grabber.grab()
            elif self.mode == MODE_WIN:
                logger.debug("Window Selection ON.")
                from kazam.frontend.window_select import SelectWindow
                self.select_window = SelectWindow()
                self.select_window.connect("window-selected", self.cb_window_selected)
                self.select_window.connect("window-canceled", self.cb_window_canceled)
                self.select_window.window.show_all()
            elif self.mode == MODE_GOD:
                logger.debug("Grabbing in god mode.")
                self.grabber.setup_sources(self.video_source, None, None, god=True)
                self.grabber.grab()
                self.grabber.setup_sources(self.video_source, None, None, active=True, god=True)
                self.grabber.grab()
            else:
                sys.exit(0)

    def cb_area_selected(self, widget):
        logger.debug("Area selected: SX: {0}, SY: {1}, EX: {2}, EY: {3}".format(
            self.area_window.startx,
            self.area_window.starty,
            self.area_window.endx,
            self.area_window.endy))
        prefs.area = (self.area_window.startx,
                      self.area_window.starty,
                      self.area_window.endx,
                      self.area_window.endy,
                      self.area_window.width,
                      self.area_window.height)
        self.grabber.setup_sources(self.video_source, prefs.area, None)
        logger.debug("Grabbing screen")
        self.grabber.grab()

    def cb_area_canceled(self, widget):
        Gtk.main_quit()
        sys.exit(0)

    def cb_window_selected(self, widget):
        xid = self.select_window.xid
        # xid_geometry = self.select_window.geometry
        logger.debug("Window selected: {0} - {1}".format(self.select_window.win_name, prefs.xid))
        logger.debug("Window geometry: {0}".format(self.select_window.geometry))
        self.grabber.setup_sources(self.video_source, None, xid)
        logger.debug("Grabbing screen")
        self.grabber.grab()

    def cb_window_canceled(self, widget):
        Gtk.main_quit()
        sys.exit(0)

    def cb_flush_done(self, widget):
        if prefs.autosave_picture or self.mode == MODE_GOD:
            fname = get_next_filename(prefs.picture_dest, prefs.autosave_picture_file, ".png")
            self.grabber.autosave(fname)
        else:
            self.grabber.save_capture(None)

    def cb_save_done(self, widget, result):
        logger.debug("Save Done, result: {0}".format(result))
        self.old_path = result

        if self.take == 1 or self.mode != MODE_GOD:
            Gtk.main_quit()
            sys.exit(0)

        self.take += 1

    def cb_prefs_quit(self, widget):
        logger.debug("Saving settings.")
        prefs.pa_q.end()
        prefs.save_config()
        Gtk.main_quit()
        sys.exit(0)
