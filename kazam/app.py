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
import imp
import sys
import locale
import shutil
import gettext
import logging
from subprocess import Popen
from gettext import gettext as _

from gi.repository import Gtk, Gdk, GObject

from kazam.utils import *
from kazam.backend.prefs import *
from kazam.backend.grabber import Grabber
from kazam.backend.keypress import KeypressViewer
from kazam.backend.gstreamer import Screencast, GWebcam

from kazam.frontend.main_menu import MainMenu
from kazam.frontend.window_area import AreaWindow
from kazam.frontend.preferences import Preferences
from kazam.frontend.about_dialog import AboutDialog
from kazam.frontend.indicator import KazamIndicator
from kazam.frontend.window_select import SelectWindow
from kazam.frontend.done_recording import DoneRecording
from kazam.frontend.window_outline import OutlineWindow
from kazam.frontend.window_countdown import CountdownWindow
from kazam.frontend.window_keypress import KeypressWindow

logger = logging.getLogger("Main")

#
# Detect GStreamer version and bail out if lower than 1.0 and no GI
#
try:
    from gi.repository import Gst
    gst_gi = Gst.version()
    if not gst_gi[0]:
        logger.critical(_("Gstreamer 1.0 or higher required, bailing out."))
        gst_gi = None
        sys.exit(0)
    else:
        logger.debug("Gstreamer version detected: {}.{}.{}.{}".format(gst_gi[0],
                                                                      gst_gi[1],
                                                                      gst_gi[2],
                                                                      gst_gi[3]))
except ImportError:
    logger.critical(_("Gstreamer 1.0 or higher required, bailing out."))
    sys.exit(0)


class KazamApp(GObject.GObject):

    def __init__(self, datadir, dist, debug, test, sound, silent):
        GObject.GObject.__init__(self)
        logger.debug("Setting variables.")

        prefs.datadir = datadir
        prefs.get_sound_files()

        self.startup = True
        prefs.debug = debug
        prefs.test = test
        prefs.dist = dist
        prefs.silent = silent
        prefs.sound = sound

        self.setup_translations()

        if prefs.sound:
            try:
                from kazam.pulseaudio.pulseaudio import pulseaudio_q
                prefs.sound = True
            except:
                logger.warning(_("Pulse Audio Failed to load. Sound recording disabled."))
                prefs.sound = False

        self.icons = Gtk.IconTheme.get_default()
        self.default_cursor = Gdk.Cursor(Gdk.CursorType.LEFT_PTR)

        # Initialize all the variables

        self.main_x = 0
        self.main_y = 0
        self.countdown = None
        self.tempfile = ""
        self.recorder = None
        self.area_window = None
        self.select_window = None
        self.outline_window = None
        self.old_vid_path = None
        self.old_pic_path = None
        self.in_countdown = False
        self.recording_paused = False
        self.recording = False
        self.main_mode = 0
        self.record_mode = 0
        self.last_mode = None
        self.keypress_detect = False
        self.keypress_viewer = None
        self.cam = None

        if prefs.sound:
            prefs.pa_q = pulseaudio_q()
            prefs.pa_q.start()

        prefs.get_webcam_sources()

        self.mainmenu = MainMenu()

        logger.debug("Connecting indicator signals.")
        logger.debug("Starting in silent mode: {0}".format(prefs.silent))
        self.indicator = KazamIndicator(prefs.silent)
        self.indicator.connect("indicator-quit-request", self.cb_quit_request)
        self.indicator.connect("indicator-show-request", self.cb_show_request)
        self.indicator.connect("indicator-start-request", self.cb_start_request)
        self.indicator.connect("indicator-stop-request", self.cb_stop_request)
        self.indicator.connect("indicator-pause-request", self.cb_pause_request)
        self.indicator.connect("indicator-unpause-request", self.cb_unpause_request)
        self.indicator.connect("indicator-about-request", self.cb_about_request)

        self.mainmenu.connect("file-quit", self.cb_quit_request)
        self.mainmenu.connect("file-preferences", self.cb_preferences_request)
        self.mainmenu.connect("help-about", self.cb_help_about)
        self.webcam = HW.webcam
        self.webcam.connect("webcam-change", self.cb_webcam_change)

        #
        # Detect Xlib, if there's no Xlib, there's no KeyViewer
        #

        try:
            imp.find_module('Xlib')
            self.keypress_viewer = KeypressViewer()
            self.keypress_viewer.connect("keypress", self.cb_got_keypress)
            self.keypress_detect = True
        except ImportError:
            logger.warning(_("No Xlib support in python3, unable to capture key and mouse clicks."))
            self.keypress_detect = False

        #
        # Setup UI
        #
        logger.debug("Main Window UI setup.")

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(prefs.datadir, "ui", "kazam.ui"))
        self.builder.connect_signals(self)
        for w in self.builder.get_objects():
            if issubclass(type(w), Gtk.Buildable):
                name = Gtk.Buildable.get_name(w)
                setattr(self, name, w)
            else:
                logger.debug("Unable to get name for '%s'" % w)

        # Retrieve gdk_win for the root window
        self.gdk_win = self.window.get_root_window()

        #
        # Attach main menu, so that
        #
        self.MainGrid.attach(self.mainmenu.menubar, 0, 0, 1, 1)

        self.main_context = self.toolbar_main.get_style_context()
        self.main_context.add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        self.main_context.connect("changed", self.cb_main_context_change)
        self.main_fg_color = self.main_context.get_color(Gtk.StateFlags.ACTIVE)

        #
        # Screen cast mode
        #
        self.btn_screencast = Gtk.RadioToolButton(group=None)
        self.btn_screencast.set_label(_("Screencast"))
        self.btn_screencast.set_tooltip_text(_("Record a video of your desktop."))
        screencast_icon = self.icons.lookup_icon("kazam-screencast-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
        if screencast_icon:
            cast_icon_pixbuf, was_sym = screencast_icon.load_symbolic(self.main_fg_color, None, None, None)
            cast_img = Gtk.Image.new_from_pixbuf(cast_icon_pixbuf)
            self.btn_screencast.set_icon_widget(cast_img)
        self.btn_screencast.set_active(True)
        self.btn_screencast.set_name("MAIN_SCREENCAST")
        self.btn_screencast.connect("toggled", self.cb_main_toggled)

        #
        # Screen shot mode
        #
        self.btn_screenshot = Gtk.RadioToolButton(group=self.btn_screencast)
        self.btn_screenshot.set_label(_("Screenshot"))
        self.btn_screenshot.set_tooltip_text(_("Record a picture of your desktop."))
        screenshot_icon = self.icons.lookup_icon("kazam-screenshot-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
        if screenshot_icon:
            shot_icon_pixbuf, was_sym = screenshot_icon.load_symbolic(self.main_fg_color, None, None, None)
            shot_img = Gtk.Image.new_from_pixbuf(shot_icon_pixbuf)
            self.btn_screenshot.set_icon_widget(shot_img)
        self.btn_screenshot.set_name("MAIN_SCREENSHOT")
        self.btn_screenshot.connect("toggled", self.cb_main_toggled)

        #
        # Broadcast mode
        #
        self.btn_broadcast = Gtk.RadioToolButton(group=self.btn_screencast)
        self.btn_broadcast.set_label(_("Broadcast"))
        self.btn_broadcast.set_tooltip_text(_("Broadcast your desktop."))
        broadcast_icon = self.icons.lookup_icon("kazam-broadcast-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
        if broadcast_icon:
            cam_icon_pixbuf, was_sym = broadcast_icon.load_symbolic(self.main_fg_color, None, None, None)
            cam_img = Gtk.Image.new_from_pixbuf(cam_icon_pixbuf)
            self.btn_broadcast.set_icon_widget(cam_img)
        self.btn_broadcast.set_name("MAIN_BROADCAST")
        self.btn_broadcast.connect("toggled", self.cb_main_toggled)

        #
        # Webcam mode
        #
        self.btn_webcam = Gtk.RadioToolButton(group=self.btn_screencast)
        self.btn_webcam.set_label(_("Webcam"))
        self.btn_webcam.set_tooltip_text(_("Capture form your webcam."))
        webcam_icon = self.icons.lookup_icon("kazam-webcam-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
        if webcam_icon:
            cam_icon_pixbuf, was_sym = webcam_icon.load_symbolic(self.main_fg_color, None, None, None)
            cam_img = Gtk.Image.new_from_pixbuf(cam_icon_pixbuf)
            self.btn_webcam.set_icon_widget(cam_img)
        self.btn_webcam.set_name("MAIN_WEBCAM")
        self.btn_webcam.connect("toggled", self.cb_main_toggled)

        self.sep_1 = Gtk.SeparatorToolItem()
        self.sep_1.set_draw(False)
        self.sep_1.set_expand(True)
        self.toolbar_main.insert(self.sep_1, -1)
        self.toolbar_main.insert(self.btn_screencast, -1)
        self.toolbar_main.insert(self.btn_screenshot, -1)
        self.toolbar_main.insert(self.btn_broadcast, -1)
        if prefs.webcam_sources:
            self.toolbar_main.insert(self.btn_webcam, -1)
        else:
            self.chk_webcam.set_sensitive(False)
            self.chk_webcam_broadcast.set_sensitive(False)
        self.toolbar_main.insert(self.sep_1, -1)

        # Auxiliary toolbar
        self.aux_context = self.toolbar_aux.get_style_context()
        self.aux_context.add_class(Gtk.STYLE_CLASS_TOOLBAR)
        self.aux_fg_color = self.aux_context.get_color(Gtk.StateFlags.ACTIVE)

        self.btn_full = Gtk.RadioToolButton(group=None)
        self.btn_full.set_label(_("Fullscreen"))
        self.btn_full.set_tooltip_text(_("Capture contents of the current screen."))
        full_icon = self.icons.lookup_icon("kazam-fullscreen-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
        if full_icon:
            full_icon_pixbuf, was_sym = full_icon.load_symbolic(self.aux_fg_color, None, None, None)
            full_img = Gtk.Image.new_from_pixbuf(full_icon_pixbuf)
            self.btn_full.set_icon_widget(full_img)
        self.btn_full.set_active(True)
        self.btn_full.set_name("MODE_FULL")
        self.btn_full.connect("toggled", self.cb_record_mode_toggled)

        self.btn_allscreens = Gtk.RadioToolButton(group=self.btn_full)
        self.btn_allscreens.set_label(_("All Screens"))
        self.btn_allscreens.set_tooltip_text(_("Capture contents of all of your screens."))
        allscreens_icon = self.icons.lookup_icon("kazam-all-screens-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
        if allscreens_icon:
            allscreens_icon_pixbuf, was_sym = allscreens_icon.load_symbolic(self.aux_fg_color, None, None, None)
            allscreens_img = Gtk.Image.new_from_pixbuf(allscreens_icon_pixbuf)
            self.btn_allscreens.set_icon_widget(allscreens_img)
        self.btn_allscreens.set_name("MODE_ALL")
        self.btn_allscreens.connect("toggled", self.cb_record_mode_toggled)
        if HW.combined_screen is None:
            self.btn_allscreens.set_sensitive(False)

        self.btn_window = Gtk.RadioToolButton(group=self.btn_full)
        self.btn_window.set_label(_("Window"))
        self.btn_window.set_tooltip_text(_("Capture contents of a single window."))
        window_icon = self.icons.lookup_icon("kazam-window-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
        if window_icon:
            window_icon_pixbuf, was_sym = window_icon.load_symbolic(self.aux_fg_color, None, None, None)
            window_img = Gtk.Image.new_from_pixbuf(window_icon_pixbuf)
            self.btn_window.set_icon_widget(window_img)
        self.btn_window.set_name("MODE_WIN")
        self.btn_window.connect("toggled", self.cb_record_mode_toggled)
        self.btn_window.connect("clicked", self.cb_record_window_clicked)

        self.btn_area = Gtk.RadioToolButton(group=self.btn_full)
        self.btn_area.set_label(_("Area"))
        self.btn_area.set_tooltip_text(_("Capture a pre-selected area of your screen."))
        area_icon = self.icons.lookup_icon("kazam-area-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
        if area_icon:
            area_icon_pixbuf, was_sym = area_icon.load_symbolic(self.aux_fg_color, None, None, None)
            area_img = Gtk.Image.new_from_pixbuf(area_icon_pixbuf)
            self.btn_area.set_icon_widget(area_img)
        self.btn_area.set_name("MODE_AREA")
        self.btn_area.connect("toggled", self.cb_record_mode_toggled)
        self.btn_area.connect("clicked", self.cb_record_area_clicked)

        self.sep_2 = Gtk.SeparatorToolItem()
        self.sep_2.set_draw(False)
        self.sep_2.set_expand(True)
        self.toolbar_aux.insert(self.sep_2, -1)
        self.toolbar_aux.insert(self.btn_full, -1)
        self.toolbar_aux.insert(self.btn_allscreens, -1)
        self.toolbar_aux.insert(self.btn_window, -1)
        self.toolbar_aux.insert(self.btn_area, -1)
        self.toolbar_aux.insert(self.sep_2, -1)
        self.ntb_main.set_current_page(0)
        self.btn_record.grab_focus()

        #
        # Take care of screen size changes.
        #
        self.default_screen = Gdk.Screen.get_default()
        self.default_screen.connect("size-changed", self.cb_screen_size_changed)
        self.window.connect("configure-event", self.cb_configure_event)

        # Fetch sources info, take care of all the widgets and saved settings and show main window
        if prefs.sound:
            prefs.get_audio_sources()

        if not prefs.silent:
            self.window.show_all()
        else:
            logger.info("""Starting in silent mode:\n"""
                        """  SUPER-CTRL-W to toggle main window.\n"""
                        """  SUPER-CTRL-R to start recording.\n"""
                        """  SUPER-CTRL-F to finish recording.\n"""
                        """  SUPER-CTRL-P to pause/resume recording.\n"""
                        """  SUPER-CTRL-Q to quit.\n"""
                        )

        self.restore_UI()

        if not self.keypress_detect:
            self.chk_keypresses.set_sensitive(False)
            self.chk_keypresses.set_active(False)

        HW.get_current_screen(self.window)
        self.startup = False

        screen = HW.get_current_screen(self.window)
        prefs.current_screen = screen

        #
        # For debugging purposes only ...
        #
        # self.keypress_viewer.start()
        # self.keypress_window = KeypressWindow()

    #
    # Callbacks, go down here ...
    #

    def cb_got_keypress(self, kv, ev_type, action, value):
        """ev_type: 'KeySym', 'KeyStr', 'MouseButton'
           action: 'Press' or 'Release'
           value: A key name ('Control_L' or 'd' or 'backslash' or 1,2,3 for
                              mouse buttons.)
        """
        logger.info("GOT EVENT: {}, {}, {}".format(ev_type, action, value))
        self.keypress_window.show(ev_type, value, action)

    #
    # Mode of operation toggles
    #

    def cb_main_toggled(self, widget):
        # Here be defaults
        self.toolbar_aux.set_sensitive(True)
        self.chk_borders_pic.set_sensitive(True)

        name = widget.get_name()
        if name == "MAIN_SCREENCAST" and widget.get_active():
            logger.debug("Main toggled: {0}".format(name))
            self.main_mode = MODE_SCREENCAST
            self.ntb_main.set_current_page(0)
            self.indicator.menuitem_start.set_label(_("Start recording"))
            self.btn_record.set_label(_("Capture"))

        elif name == "MAIN_SCREENSHOT" and widget.get_active():
            logger.debug("Main toggled: {0}".format(name))
            self.main_mode = MODE_SCREENSHOT
            self.ntb_main.set_current_page(1)
            if self.record_mode == MODE_WIN:
                self.last_mode.set_active(True)
            self.indicator.menuitem_start.set_label(_("Take screenshot"))
            if self.record_mode != "MODE_WIN":
                self.chk_borders_pic.set_sensitive(False)
            self.btn_record.set_label(_("Capture"))

        elif name == "MAIN_BROADCAST" and widget.get_active():
            logger.debug("Main toggled: {0}".format(name))
            self.main_mode = MODE_BROADCAST
            self.ntb_main.set_current_page(2)
            self.indicator.menuitem_start.set_label(_("Start broadcasting"))
            self.btn_record.set_label(_("Broadcast"))
            self.toolbar_aux.set_sensitive(False)

        elif name == "MAIN_WEBCAM" and widget.get_active():
            logger.debug("Main toggled: {0}".format(name))
            self.ntb_main.set_current_page(3)
            self.main_mode = MODE_WEBCAM
            self.toolbar_aux.set_sensitive(False)
            self.indicator.menuitem_start.set_label(_("Start recording"))
            self.btn_record.set_label(_("Capture"))

    #
    # Record mode toggles
    #
    def cb_record_mode_toggled(self, widget):
        if widget.get_active():
            self.current_mode = widget
        else:
            self.last_mode = widget

        if widget.get_name() == "MODE_AREA" and widget.get_active():
            logger.debug("Area ON.")
            self.area_window = AreaWindow()
            self.tmp_sig1 = self.area_window.connect("area-selected", self.cb_area_selected)
            self.tmp_sig2 = self.area_window.connect("area-canceled", self.cb_area_canceled)
            self.record_mode = MODE_AREA

        if widget.get_name() == "MODE_AREA" and not widget.get_active():
            logger.debug("Area OFF.")
            if self.area_window:
                self.area_window.disconnect(self.tmp_sig1)
                self.area_window.disconnect(self.tmp_sig2)
                self.area_window.window.destroy()
                self.area_window = None

        if widget.get_name() == "MODE_FULL" and widget.get_active():
            logger.debug("Capture full screen.")
            self.record_mode = MODE_FULL

        if widget.get_name() == "MODE_ALL" and widget.get_active():
            logger.debug("Capture all screens.")
            self.record_mode = MODE_ALL

        if widget.get_name() == "MODE_WIN" and widget.get_active():
            logger.debug("Window capture ON.")
            self.select_window = SelectWindow()
            self.tmp_sig3 = self.select_window.connect("window-selected", self.cb_window_selected)
            self.tmp_sig4 = self.select_window.connect("window-canceled", self.cb_window_canceled)
            self.record_mode = MODE_WIN
            self.chk_borders_pic.set_sensitive(True)

        if widget.get_name() == "MODE_WIN" and not widget.get_active():
            logger.debug("Window capture OFF.")
            self.chk_borders_pic.set_sensitive(False)
            if self.select_window:
                self.select_window.disconnect(self.tmp_sig3)
                self.select_window.disconnect(self.tmp_sig4)
                self.select_window.window.destroy()
                self.select_window = None

    def cb_main_context_change(self, widget):
        #
        # If this is the only way on how to deal with symbolic icons, then someone needs spanking ...
        #
        if widget.get_state() == Gtk.StateFlags.BACKDROP:
            self.main_fg_color = self.main_context.get_color(Gtk.StateFlags.ACTIVE)
            self.aux_fg_color = self.aux_context.get_color(Gtk.StateFlags.ACTIVE)

            #
            # Update icons on the main toolbar
            #
            cast_icon = self.icons.lookup_icon("kazam-screencast-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
            if cast_icon:
                cast_icon_pixbuf, was_sym = cast_icon.load_symbolic(self.main_fg_color, None, None, None)
                cast_img = Gtk.Image.new_from_pixbuf(cast_icon_pixbuf)
                self.btn_screencast.set_icon_widget(cast_img)
                cast_img.show_all()

            shot_icon = self.icons.lookup_icon("kazam-screenshot-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
            if shot_icon:
                shot_icon_pixbuf, was_sym = shot_icon.load_symbolic(self.main_fg_color, None, None, None)
                shot_img = Gtk.Image.new_from_pixbuf(shot_icon_pixbuf)
                self.btn_screenshot.set_icon_widget(shot_img)
                shot_img.show_all()

            webcam_icon = self.icons.lookup_icon("kazam-webcam-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
            if webcam_icon:
                webcam_icon_pixbuf, was_sym = webcam_icon.load_symbolic(self.main_fg_color, None, None, None)
                webcam_img = Gtk.Image.new_from_pixbuf(webcam_icon_pixbuf)
                self.btn_screencast.set_icon_widget(webcam_img)
                webcam_img.show_all()

            broadcast_icon = self.icons.lookup_icon("kazam-broadcast-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
            if broadcast_icon:
                broadcast_icon_pixbuf, was_sym = broadcast_icon.load_symbolic(self.main_fg_color, None, None, None)
                broadcast_img = Gtk.Image.new_from_pixbuf(broadcast_icon_pixbuf)
                self.btn_screenshot.set_icon_widget(broadcast_img)
                broadcast_img.show_all()

            #
            # Update icons on the aux toolbar
            #
            full_icon = self.icons.lookup_icon("kazam-fullscreen-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
            if full_icon:
                full_icon_pixbuf, was_sym = full_icon.load_symbolic(self.aux_fg_color, None, None, None)
                full_img = Gtk.Image.new_from_pixbuf(full_icon_pixbuf)
                self.btn_full.set_icon_widget(full_img)
                full_img.show_all()

            allscreens_icon = self.icons.lookup_icon("kazam-all-screens-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
            if allscreens_icon:
                allscreens_icon_pixbuf, was_sym = allscreens_icon.load_symbolic(self.aux_fg_color, None, None, None)
                allscreens_img = Gtk.Image.new_from_pixbuf(allscreens_icon_pixbuf)
                self.btn_allscreens.set_icon_widget(allscreens_img)
                allscreens_img.show_all()

            window_icon = self.icons.lookup_icon("kazam-window-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
            if window_icon:
                window_icon_pixbuf, was_sym = window_icon.load_symbolic(self.aux_fg_color, None, None, None)
                window_img = Gtk.Image.new_from_pixbuf(window_icon_pixbuf)
                self.btn_window.set_icon_widget(window_img)
                window_img.show_all()

            area_icon = self.icons.lookup_icon("kazam-area-symbolic", 24, Gtk.IconLookupFlags.FORCE_SIZE)
            if area_icon:
                area_icon_pixbuf, was_sym = area_icon.load_symbolic(self.aux_fg_color, None, None, None)
                area_img = Gtk.Image.new_from_pixbuf(area_icon_pixbuf)
                self.btn_area.set_icon_widget(area_img)
                area_img.show_all()

    #
    # Unity quick list callbacks
    #

    def cb_ql_screencast(self, menu, data):
        logger.debug("Screencast quicklist activated.")
        self.btn_screencast.set_active(True)
        self.run_counter()

    def cb_ql_screenshot(self, menu, data):
        logger.debug("Screenshot quicklist activated.")
        self.btn_screenshot.set_active(True)
        self.run_counter()

    def cb_record_area_clicked(self, widget):
        if self.area_window:
            logger.debug("Area mode clicked.")
            self.area_window.window.show_all()
            self.window.set_sensitive(False)

    def cb_record_window_clicked(self, widget):
        if self.select_window:
            logger.debug("Window mode clicked.")
            self.select_window.window.show_all()
            self.window.set_sensitive(False)

    def cb_area_selected(self, widget):
        logger.debug("Area selected: SX: {0}, SY: {1}, EX: {2}, EY: {3}".format(
            self.area_window.startx,
            self.area_window.starty,
            self.area_window.endx,
            self.area_window.endy))
        logger.debug("Area selected: GX: {0}, GY: {1}, GX: {2}, GY: {3}".format(
            self.area_window.g_startx,
            self.area_window.g_starty,
            self.area_window.g_endx,
            self.area_window.g_endy))
        prefs.area = (self.area_window.g_startx,
                      self.area_window.g_starty,
                      self.area_window.g_endx,
                      self.area_window.g_endy,
                      self.area_window.width,
                      self.area_window.height)
        self.window.set_sensitive(True)

    def cb_area_canceled(self, widget):
        logger.debug("Area selection canceled.")
        self.window.set_sensitive(True)
        self.last_mode.set_active(True)

    def cb_window_selected(self, widget):
        prefs.xid = self.select_window.xid
        prefs.xid_geometry = self.select_window.geometry
        logger.debug("Window selected: {0} - {1}".format(self.select_window.win_name, prefs.xid))
        logger.debug("Window geometry: {0}".format(self.select_window.geometry))
        self.window.set_sensitive(True)

    def cb_window_canceled(self, widget):
        logger.debug("Window selection canceled.")
        self.window.set_sensitive(True)
        self.last_mode.set_active(True)

    def cb_screen_size_changed(self, screen):
        logger.debug("Screen size changed.")
        HW.get_screens()
        #
        # If combined screen was set to none, turn off the button for all screens
        #
        if HW.combined_screen:
            self.btn_allscreens.set_sensitive(True)
        else:
            self.btn_allscreens.set_sensitive(False)

    def cb_configure_event(self, widget, event):
        if event.type == Gdk.EventType.CONFIGURE:
            prefs.main_x = event.x
            prefs.main_y = event.y

    def cb_quit_request(self, indicator):
        logger.debug("Quit requested.")
        # Restore cursor, just in case if by some chance stays set to cross-hairs
        self.gdk_win.set_cursor(self.default_cursor)
        (prefs.main_x, prefs.main_y) = self.window.get_position()
        try:
            os.remove(self.recorder.tempfile)
            os.remove("{0}.mux".format(self.recorder.tempfile))
        except OSError:
            logger.info("Unable to delete one of the temporary files. Check your temporary directory.")
        except AttributeError:
            pass

        prefs.save_config()

        if prefs.sound:
            prefs.pa_q.end()

        #
        # Just in case, try to shutdown keylogger
        #
        if self.keypress_viewer:
            self.keypress_viewer.stop()
        Gtk.main_quit()

    def cb_preferences_request(self, indicator):
        logger.debug("Preferences requested.")
        self.preferences_window = Preferences()
        self.preferences_window.open()

    def cb_show_request(self, indicator):
        if not self.window.get_property("visible"):
            logger.debug("Show requested, raising window.")
            self.window.show_all()
            self.window.present()
            self.window.move(prefs.main_x, prefs.main_y)
        else:
            self.window.hide()

    def cb_close_clicked(self, indicator):
        (prefs.main_x, prefs.main_y) = self.window.get_position()
        self.window.hide()

    def cb_about_request(self, activated):
        AboutDialog(self.icons)

    def cb_delete_event(self, widget, user_data):
        self.cb_quit_request(None)

    def cb_start_request(self, widget):
        logger.debug("Start recording selected.")
        self.run_counter()

    def cb_record_clicked(self, widget):
        logger.debug("Record clicked, invoking Screencast.")
        self.run_counter()

    def cb_counter_finished(self, widget):
        logger.debug("Counter finished.")
        self.in_countdown = False
        self.countdown = None
        self.indicator.blink_set_state(BLINK_STOP)
        if self.main_mode in [MODE_SCREENCAST, MODE_WEBCAM, MODE_BROADCAST]:
            if self.main_mode == MODE_BROADCAST:
                self.indicator.menuitem_finish.set_label(_("Finish broadcasting"))
            else:
                self.indicator.menuitem_finish.set_label(_("Finish recording"))
            self.indicator.menuitem_pause.set_sensitive(True)
            self.indicator.start_recording()
            self.recorder.start_recording()
            if (self.main_mode == MODE_SCREENCAST and prefs.capture_keys) or (self.main_mode == MODE_BROADCAST and prefs.capture_keys_broadcast):
                self.keypress_window = KeypressWindow()
                self.keypress_viewer.start()
        elif self.main_mode == MODE_SCREENSHOT:
            self.indicator.hide_it()
            self.grabber.grab()
            self.indicator.show_it()

    def cb_stop_request(self, widget):
        self.recording = False

        if self.outline_window:
            self.outline_window.hide()
            self.outline_window.window.destroy()
            self.outline_window = None

        if self.in_countdown:
            logger.debug("Cancel countdown request.")
            self.countdown.cancel_countdown()
            self.countdown = None
            self.indicator.menuitem_finish.set_label(_("Finish recording"))
            self.window.set_sensitive(True)
            self.window.show()
            self.window.present()
        else:
            if self.recording_paused:
                self.recorder.unpause_recording()
            logger.debug("Stop request.")
            self.recorder.stop_recording()
            if (self.main_mode == MODE_SCREENCAST and prefs.capture_keys) or (self.main_mode == MODE_BROADCAST and prefs.capture_keys_broadcast):
                self.keypress_viewer.stop()
                self.keypress_window.window.destroy()
                self.keypress_window = None
                self.keypress_viewer = None

            self.tempfile = self.recorder.get_tempfile()
            logger.debug("Recorded tmp file: {0}".format(self.tempfile))
            logger.debug("Waiting for data to flush.")

    def cb_flush_done(self, widget):
        if self.main_mode == MODE_SCREENCAST and prefs.autosave_video:
            logger.debug("Autosaving enabled.")
            fname = get_next_filename(prefs.autosave_video_dir,
                                      prefs.autosave_video_file,
                                      CODEC_LIST[prefs.codec][3])

            shutil.move(self.tempfile, fname)

            self.window.set_sensitive(True)
            self.window.show()
            self.window.present()
        elif self.main_mode == MODE_SCREENCAST or self.main_mode == MODE_WEBCAM:
            self.done_recording = DoneRecording(self.icons,
                                                self.tempfile,
                                                prefs.codec,
                                                self.old_vid_path)
            logger.debug("Done Recording initialized.")
            self.done_recording.connect("save-done", self.cb_save_done)
            self.done_recording.connect("save-cancel", self.cb_save_cancel)
            self.done_recording.connect("edit-request", self.cb_edit_request)
            logger.debug("Done recording signals connected.")
            self.done_recording.show_all()
            self.window.set_sensitive(False)

        elif self.main_mode == MODE_BROADCAST:
            self.window.set_sensitive(True)
            self.window.show_all()
            self.window.present()
            self.window.move(prefs.main_x, prefs.main_y)

        elif self.main_mode == MODE_SCREENSHOT:
            if self.outline_window:
                self.outline_window.hide()
                self.outline_window.window.destroy()
                self.outline_window = None

            self.grabber.connect("save-done", self.cb_save_done)
            self.indicator.recording = False
            self.indicator.menuitem_start.set_sensitive(True)
            self.indicator.menuitem_pause.set_sensitive(False)
            self.indicator.menuitem_pause.set_active(False)
            self.indicator.menuitem_finish.set_sensitive(False)
            self.indicator.menuitem_quit.set_sensitive(True)

            if prefs.autosave_picture:
                fname = get_next_filename(prefs.autosave_picture_dir,
                                          prefs.autosave_picture_file,
                                          ".png")
                self.grabber.autosave(fname)
            else:
                self.grabber.save_capture(self.old_pic_path)

    def cb_pause_request(self, widget):
        logger.debug("Pause requested.")
        self.recording_paused = True
        self.recorder.pause_recording()

    def cb_unpause_request(self, widget):
        logger.debug("Unpause requested.")
        self.recording_paused = False
        self.recorder.unpause_recording()

    def cb_save_done(self, widget, result):
        logger.debug("Save Done, result: {0}".format(result))
        if self.main_mode == MODE_SCREENCAST:
            self.old_vid_path = result
        else:
            self.old_pic_path = result

        self.window.set_sensitive(True)
        self.window.show_all()
        self.window.present()
        self.window.move(prefs.main_x, prefs.main_y)

    def cb_save_cancel(self, widget):
        try:
            logger.debug("Save canceled, removing {0}".format(self.tempfile))
            os.remove(self.tempfile)
        except OSError:
            logger.info("Failed to remove tempfile {0}".format(self.tempfile))
        except AttributeError:
            logger.info("Failed to remove tempfile {0}".format(self.tempfile))
            pass

        self.window.set_sensitive(True)
        self.window.show_all()
        self.window.present()
        self.window.move(prefs.main_x, prefs.main_y)

    def cb_help_about(self, widget):
        AboutDialog(self.icons)

    def cb_edit_request(self, widget, data):
        (command, arg_list) = data
        arg_list.insert(0, command)
        #
        # Use the current autosave filename for edit file.
        #
        fname = get_next_filename(prefs.video_dest,
                                  prefs.autosave_video_file,
                                  CODEC_LIST[prefs.codec][3])

        shutil.move(self.tempfile, fname)
        arg_list.append(fname)
        logger.debug("Edit request, cmd: {0}".format(arg_list))
        try:
            Popen(arg_list)
        except:
            logger.warning("Failed to open selected editor.")
        self.window.set_sensitive(True)
        self.window.show_all()

    def cb_check_cursor(self, widget):
        name = Gtk.Buildable.get_name(widget)
        if name == "chk_cursor":
            prefs.capture_cursor = widget.get_active()
        elif name == "chk_cursor_pic":
            prefs.capture_cursor_pic = widget.get_active()
        elif name == "chk_cursor_broadcast":
            prefs.capture_cursor_broadcast = widget.get_active()
        logger.debug("Toggled {}: {}.".format(name, widget.get_active()))

    def cb_check_borders_pic(self, widget):
        prefs.capture_borders_pic = widget.get_active()
        logger.debug("Capture borders_pic: {0}.".format(prefs.capture_borders_pic))

    def cb_check_speakers(self, widget):
        name = Gtk.Buildable.get_name(widget)
        if name == "chk_speakers":
            prefs.capture_speakers = widget.get_active()
        elif name == "chk_speakers_webcam":
            prefs.capture_speakers_webcam = widget.get_active()
        elif name == "chk_speakers_broadcast":
            prefs.capture_speakers_broadcast = widget.get_active()
        logger.debug("Toggled {}: {}.".format(name, widget.get_active()))

    def cb_check_microphone(self, widget):
        name = Gtk.Buildable.get_name(widget)
        if name == "chk_microphone":
            prefs.capture_microphone = widget.get_active()
        elif name == "chk_microphone_webcam":
            prefs.capture_microphone_webcam = widget.get_active()
        elif name == "chk_microphone_broadcast":
            prefs.capture_microphone_broadcast = widget.get_active()
        logger.debug("Toggled {}: {}.".format(name, widget.get_active()))

    def cb_spinbutton_delay_change(self, widget):
        prefs.countdown_timer = widget.get_value_as_int()
        logger.debug("Start delay now: {0}".format(prefs.countdown_timer))

    def cb_check_webcam(self, widget):
        name = Gtk.Buildable.get_name(widget)
        if widget.get_active() is True:
            if self.cam is None:
                logger.debug("Turning ON webcam window.")
                self.cam = GWebcam()
                self.cam.start()
                if name == "chk_webcam_broadcast":
                    self.chk_webcam.set_active(True)
                else:
                    self.chk_webcam_broadcast.set_active(True)
        else:
            if self.cam is not None:
                logger.debug("Turning OFF webcam window.")
                self.cam.close()
                self.cam = None
                if name == "chk_webcam_broadcast":
                    self.chk_webcam.set_active(False)
                else:
                    self.chk_webcam_broadcast.set_active(False)

    def cb_check_keypresses(self, widget):
        name = Gtk.Buildable.get_name(widget)
        if name == "chk_keypresses":
            prefs.capture_keys = widget.get_active()
        elif name == "chk_keypresses_broadcast":
            prefs.capture_keys_broadcast = widget.get_active()
        logger.debug("Toggled {}: {}.".format(name, widget.get_active()))

    #
    # Other somewhat useful stuff ...
    #

    def run_counter(self):
        #
        # Annoyances with the menus
        #
        logger.debug("Running Counter.")
        (main_x, main_y) = self.window.get_position()
        if main_x and main_y:
            prefs.main_x = main_x
            prefs.main_y = main_y

        self.indicator.recording = True
        self.indicator.menuitem_start.set_sensitive(False)
        self.indicator.menuitem_pause.set_sensitive(False)
        self.indicator.menuitem_finish.set_sensitive(True)
        self.indicator.menuitem_quit.set_sensitive(False)
        self.indicator.menuitem_finish.set_label(_("Cancel countdown"))
        self.in_countdown = True

        self.indicator.blink_set_state(BLINK_START)

        if prefs.sound:
            if (self.main_mode == MODE_SCREENCAST and prefs.capture_speakers) or \
               (self.main_mode == MODE_BROADCAST and prefs.capture_speakers_broadcast) or \
               (self.main_mode == MODE_WEBCAM and prefs.capture_speakers_webcam):
                try:
                    audio_source = prefs.speaker_sources[prefs.audio_source][1]
                    try:
                        audio_channels = prefs.pa_q.get_source_info_by_index(prefs.speaker_sources[prefs.audio_source][0])[2].channels
                    except:
                        audio_channels = 1
                    logger.debug("Detected audio channels: {}".format(audio_channels))
                except IndexError:
                    logger.warning("It appears that speakers audio source isn't set up correctly.")
                    audio_source = None
            else:
                audio_source = None
                audio_channels = 1

            if (self.main_mode == MODE_SCREENCAST and prefs.capture_microphone) or \
               (self.main_mode == MODE_BROADCAST and prefs.capture_microphone_broadcast) or \
               (self.main_mode == MODE_WEBCAM and prefs.capture_microphone_webcam):
                try:
                    audio2_source = prefs.mic_sources[prefs.audio2_source][1]
                    try:
                        audio2_channels = prefs.pa_q.get_source_info_by_index(prefs.speaker_sources[prefs.audio2_source][0])[2].channels
                    except:
                        audio2_channels = 1
                    logger.debug("Detected audio2 channels: {}".format(audio2_channels))
                except IndexError:
                    logger.warning("It appears that microphone audio source isn't set up correctly.")
                    audio2_source = None
            else:
                audio2_source = None
                audio2_channels = 1
        else:
            audio_source = None
            audio_channels = 1
            audio2_source = None
            audio2_channels = 1

        #
        # Get appropriate coordinates for recording
        #

        video_source = None

        screen = HW.get_current_screen(self.window)
        prefs.current_screen = screen

        if self.main_mode == MODE_WEBCAM:
            video_source = CAM_RESOLUTIONS[prefs.webcam_source]
        elif self.record_mode == MODE_ALL:
            video_source = HW.combined_screen
        else:
            video_source = HW.screens[screen]

        if self.main_mode in [MODE_SCREENCAST, MODE_WEBCAM, MODE_BROADCAST]:
            self.recorder = Screencast(self.main_mode)
            self.recorder.setup_sources(video_source,
                                        audio_source,
                                        audio2_source,
                                        prefs.area if self.record_mode == MODE_AREA and self.main_mode not in [MODE_WEBCAM, MODE_BROADCAST] else None,
                                        prefs.xid if self.record_mode == MODE_WIN and self.main_mode not in [MODE_WEBCAM, MODE_BROADCAST] else None,
                                        audio_channels,
                                        audio2_channels)

            self.recorder.connect("flush-done", self.cb_flush_done)

        elif self.main_mode == MODE_SCREENSHOT:
            self.grabber = Grabber()
            self.grabber.setup_sources(video_source,
                                       prefs.area if self.record_mode == MODE_AREA else None,
                                       prefs.xid if self.record_mode == MODE_WIN else None)
            self.grabber.connect("flush-done", self.cb_flush_done)

        self.countdown = CountdownWindow(self.indicator, show_window=prefs.countdown_splash)
        self.countdown.connect("counter-finished", self.cb_counter_finished)
        logger.debug("Starting counter.")
        self.countdown.run(prefs.countdown_timer)
        self.recording = True
        logger.debug("Hiding main window.")
        self.window.hide()
        if self.main_mode == MODE_SCREENCAST or self.main_mode == MODE_SCREENSHOT:
            try:
                if self.record_mode == MODE_AREA and prefs.area:
                    logger.debug("Showing recording outline.")
                    self.outline_window = OutlineWindow(prefs.area[0],
                                                        prefs.area[1],
                                                        prefs.area[4],
                                                        prefs.area[5])
                    self.outline_window.show()
            except:
                logger.debug("Unable to show recording outline.")

    def setup_translations(self):
        gettext.bindtextdomain("kazam", "/usr/share/locale")
        gettext.textdomain("kazam")
        try:
            locale.setlocale(locale.LC_ALL, "")
        except:
            logger.exception("EXCEPTION: Setlocale failed, no language support.")

    def restore_UI(self):
        self.window.move(prefs.main_x, prefs.main_y)
        self.chk_cursor.set_active(prefs.capture_cursor)
        self.chk_speakers.set_active(prefs.capture_speakers)
        self.chk_microphone.set_active(prefs.capture_microphone)
        self.chk_keypresses.set_active(prefs.capture_keys)

        self.chk_cursor_pic.set_active(prefs.capture_cursor_pic)
        self.chk_borders_pic.set_active(prefs.capture_borders_pic)
        self.spinbutton_delay.set_value(prefs.countdown_timer)

        self.chk_speakers_webcam.set_active(prefs.capture_speakers_webcam)
        self.chk_microphone_webcam.set_active(prefs.capture_microphone_webcam)

        self.chk_cursor_broadcast.set_active(prefs.capture_cursor_broadcast)
        self.chk_speakers_broadcast.set_active(prefs.capture_speakers_broadcast)
        self.chk_microphone_broadcast.set_active(prefs.capture_microphone_broadcast)
        self.chk_keypresses_broadcast.set_active(prefs.capture_keys_broadcast)

        #
        # Turn off the combined screen icon if we don't have more than one screen.
        #
        if HW.combined_screen:
            self.btn_allscreens.set_sensitive(True)
        else:
            self.btn_allscreens.set_sensitive(False)

    def cb_webcam_change(self, widget):
        prefs.get_webcam_sources()
        logger.debug("Webcams: {}".format(prefs.webcam_sources))
        if prefs.webcam_sources:
            logger.debug("Adding Webcam UI items.")
            self.toolbar_main.insert(self.btn_webcam, -1)
            self.toolbar_main.show_all()
            self.chk_webcam.set_active(False)
            self.chk_webcam.set_sensitive(True)
        else:
            logger.debug("Removing Webcam UI items.")
            self.toolbar_main.remove(self.btn_webcam)
            self.chk_webcam.set_sensitive(False)
            self.chk_webcam.set_active(False)
            if self.btn_webcam.get_active():
                self.btn_screencast.set_active(True)
