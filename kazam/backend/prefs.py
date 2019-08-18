# -*- coding: utf-8 -*-
#
#       prefs.py
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
import logging
from os.path import expanduser
from gettext import gettext as _
from xdg.BaseDirectory import xdg_config_home

from gi.repository import Gdk, GdkX11

from kazam.backend.webcam import Webcam
from kazam.backend.config import KazamConfig


class Prefs():

    def __init__(self):
        """Initialize prefs and set all the preference variables to their
           default values.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.logger = logging.getLogger("Prefs")

        #
        # GUI preferences and stuff (should this be stored in a dict or something?)
        #
        self.capture_cursor = False
        self.capture_speakers = False
        self.capture_microphone = False

        self.capture_speakers_webcam = False
        self.capture_microphone_webcam = False

        self.capture_cursor_broadcast = False
        self.capture_speakers_broadcast = False
        self.capture_microphone_broadcast = False

        self.capture_cursor_pic = False
        self.capture_borders_pic = False

        self.countdown_timer = 5

        self.speakers_source = None
        self.microphone_source = None

        self.speakers_volume = 0
        self.microphone_volume = 0

        self.countdown_splash = True
        self.silent_start = False

        self.capture_keys = False

        #
        # Other stuff
        #
        self.datadir = None

        #
        # Capture related stuff
        #
        self.codec = None
        self.pa_q = None
        self.framerate = 15
        self.autosave_video = False
        self.autosave_video_dir = None
        self.autosave_video_file = None

        self.autosave_picture = False
        self.autosave_picture_dir = None
        self.autosave_picture_file = None
        self.shutter_sound = True
        self.shutter_type = 0
        self.shutter_sound_file = ""

        self.area = None
        self.xid = None
        self.xid_geometry = None

        #
        # Audio sources
        #  - Tuple of all sources
        #  - Selected first source
        #  - Selected second source
        #
        self.audio_sources = None
        self.audio_source = None
        self.audio2_source = None

        self.speaker_sources = []
        self.mic_sources = []

        #
        # Broadcast and webcam stuff
        #
        self.webcam_source = None
        self.webcam_sources = {}
        self.webcam_show_preview = True
        self.webcam_preview_pos = 1
        self.webcam_resolution = 0

        self.yt_stream = ''
        self.yt_server = ''

        self.tw_stream = ''
        self.tw_server = ''

        self.broadcast_dst = ''

        #
        # Command line parameters
        #
        self.debug = False
        self.test = False
        self.dist = ('Ubuntu', '12.10', 'quantal')
        self.silent = False
        self.sound = True
        self.first_run = True

        self.config = KazamConfig()

        self.read_config()

        self.get_dirs()

        #
        # Fix codec list
        #

    def get_audio_sources(self):
        self.logger.debug("Getting Audio sources.")
        try:
            self.audio_sources = prefs.pa_q.get_audio_sources()
            for src in self.audio_sources:
                if "Monitor" in src[2]:
                    self.speaker_sources.append(src)
                else:
                    self.mic_sources.append(src)

            if prefs.debug:
                for src in self.audio_sources:
                    self.logger.debug(" Device found: ")
                    for item in src:
                        self.logger.debug("  - {0}".format(item))
        except:
            # Something went wrong, just fallback to no-sound
            self.logger.warning("Unable to find any audio devices.")
            self.audio_sources = [[0, _("Unknown"), _("Unknown")]]

    def get_webcam_sources(self):
        self.webcam_sources = HW.webcam.device_list

    def get_dirs(self):
        paths = {}
        f = None
        try:
            f = open(os.path.join(xdg_config_home, "user-dirs.dirs"))
            for la in f:
                if la.startswith("XDG_VIDEOS") or la.startswith("XDG_DOCUMENTS") or la.startswith("XDG_PICTURES"):
                    (idx, val) = la.strip()[:-1].split('="')
                    paths[idx] = os.path.expandvars(val)
        except:
            paths['XDG_VIDEOS_DIR'] = os.path.expanduser("~/Videos/")
            paths['XDG_PICTURES_DIR'] = os.path.expanduser("~/Pictures/")
            paths['XDG_DOCUMENTS_DIR'] = os.path.expanduser("~/Documents/")
        finally:
            if f is not None:
                f.close()

        paths['HOME_DIR'] = os.path.expandvars("$HOME")

        if 'XDG_VIDEOS_DIR' in paths and os.path.isdir(paths['XDG_VIDEOS_DIR']):
            self.video_dest = paths['XDG_VIDEOS_DIR']
        elif 'XDG_DOCUMENTS_DIR' in paths and os.path.isdir(paths['XDG_DOCUMENTS_DIR']):
            self.video_dest = paths['XDG_DOCUMENTS_DIR']
        elif 'HOME_DIR' in paths and os.path.isdir(paths['HOME_DIR']):
            self.video_dest = paths['HOME_DIR']
        else:
            self.video_dest = expanduser("~")

        if 'XDG_PICTURES_DIR' in paths and os.path.isdir(paths['XDG_PICTURES_DIR']):
            self.logger.debug("XDG_PICTURES is a directory and accessible")
            self.picture_dest = paths['XDG_PICTURES_DIR']
        elif 'XDG_DOCUMENTS_DIR' in paths and os.path.isdir(paths['XDG_DOCUMENTS_DIR']):
            self.logger.debug("XDG_DOCUMENTS is a directory and accessible")
            self.picture_dest = paths['XDG_DOCUMENTS_DIR']
        elif 'HOME_DIR' in paths and os.path.isdir(paths['HOME_DIR']):
            self.logger.debug("HOME_DIR is a directory and accessible")
            self.picture_dest = paths['HOME_DIR']
        else:
            self.logger.debug("Fallback to ~ for save files.")
            self.picture_dest = expanduser("~")

    def get_sound_files(self):
        self.sound_files = []
        for root, d_dir, files in os.walk(os.path.join(self.datadir, "sounds")):
            for f_file in files:
                if f_file.endswith('.ogg'):
                    self.sound_files.append(f_file)

    def read_config(self):
        self.audio_source = int(self.config.get("main", "audio_source"))
        self.audio2_source = int(self.config.get("main", "audio2_source"))
        self.webcam_source = int(self.config.get("main", "webcam_source"))

        self.main_x = int(self.config.get("main", "last_x"))
        self.main_y = int(self.config.get("main", "last_y"))

        self.countdown_timer = float(self.config.get("main", "counter"))
        #
        # Just in case this blows up in our face later
        #
        if self.countdown_timer > 10:
            self.countdown_timer = 10
        self.framerate = float(self.config.get("main", "framerate"))

        self.capture_cursor = self.config.getboolean("main", "capture_cursor")
        self.capture_speakers = self.config.getboolean("main", "capture_speakers")
        self.capture_microphone = self.config.getboolean("main", "capture_microphone")

        self.capture_speakers_webcam = self.config.getboolean("main", "capture_speakers_w")
        self.capture_microphone_webcam = self.config.getboolean("main", "capture_microphone_w")

        self.capture_cursor_broadcast = self.config.getboolean("main", "capture_cursor_b")
        self.capture_speakers_broadcast = self.config.getboolean("main", "capture_speakers_b")
        self.capture_microphone_broadcast = self.config.getboolean("main", "capture_microphone_b")

        self.capture_cursor_pic = self.config.getboolean("main", "capture_cursor_pic")
        self.capture_borders_pic = self.config.getboolean("main", "capture_borders_pic")

        self.countdown_splash = self.config.getboolean("main", "countdown_splash")

        self.autosave_video = self.config.getboolean("main", "autosave_video")
        self.autosave_video_dir = self.config.get("main", "autosave_video_dir")
        self.autosave_video_file = self.config.get("main", "autosave_video_file")

        self.autosave_picture = self.config.getboolean("main", "autosave_picture")
        self.autosave_picture_dir = self.config.get("main", "autosave_picture_dir")
        self.autosave_picture_file = self.config.get("main", "autosave_picture_file")

        self.shutter_sound = self.config.getboolean("main", "shutter_sound")
        self.shutter_type = int(self.config.get("main", "shutter_type"))

        self.webcam_show_preview = self.config.getboolean("main", "webcam_show_preview")
        self.webcam_preview_pos = int(self.config.get("main", "webcam_preview_pos"))
        self.webcam_resolution = int(self.config.get("main", "webcam_resolution"))

        self.capture_keys = self.config.getboolean("main", "capture_keys")
        self.capture_keys_broadcast = self.config.getboolean("main", "capture_keys_b")

        self.yt_stream = self.config.get("main", "yt_stream")
        self.yt_server = self.config.get("main", "yt_server")

        self.tw_stream = self.config.get("main", "tw_stream")
        self.tw_server = self.config.get("main", "tw_server")

        self.broadcast_dst = int(self.config.get("main", "broadcast_dst"))

        self.first_run = self.config.getboolean("main", "first_run")

        #
        # Determine which codec to use
        #
        if self.first_run:
            self.logger.debug("First run detected.")
            self.config.set("main", "first_run", False)
            self.config.write()

            codecs_avail = detect_codecs()
            if CODEC_H264 in codecs_avail:
                self.codec = CODEC_H264
                self.logger.debug("Setting H264 as default codec.")
            elif CODEC_VP8 in codecs_avail:
                self.codec = CODEC_VP8
                self.logger.debug("Setting VP8 as default codec.")
            else:
                self.codec = CODEC_RAW
                self.logger.debug("Setting RAW as default codec.")
        else:
            self.codec = int(self.config.get("main", "codec"))

    def save_config(self):
        self.config.set("main", "capture_cursor", self.capture_cursor)
        self.config.set("main", "capture_speakers", self.capture_speakers)
        self.config.set("main", "capture_microphone", self.capture_microphone)
        self.config.set("main", "capture_keys", self.capture_keys)
        self.config.set("main", "capture_keys_b", self.capture_keys_broadcast)

        self.config.set("main", "capture_speakers_w", self.capture_speakers_webcam)
        self.config.set("main", "capture_microphone_w", self.capture_microphone_webcam)

        self.config.set("main", "capture_cursor_b", self.capture_cursor_broadcast)
        self.config.set("main", "capture_speakers_b", self.capture_speakers_broadcast)
        self.config.set("main", "capture_microphone_b", self.capture_microphone_broadcast)

        self.config.set("main", "capture_cursor_pic", self.capture_cursor_pic)
        self.config.set("main", "capture_borders_pic", self.capture_borders_pic)

        self.config.set("main", "last_x", self.main_x)
        self.config.set("main", "last_y", self.main_y)

        if self.sound:
            self.config.set("main", "audio_source", self.audio_source)
            self.config.set("main", "audio2_source", self.audio2_source)

        self.config.set("main", "webcam_source", self.webcam_source)

        self.config.set("main", "countdown_splash", self.countdown_splash)
        self.config.set("main", "counter", self.countdown_timer)
        self.config.set("main", "codec", self.codec)
        self.config.set("main", "framerate", self.framerate)
        self.config.set("main", "autosave_video", self.autosave_video)
        self.config.set("main", "autosave_video_dir", self.autosave_video_dir)
        self.config.set("main", "autosave_video_file", self.autosave_video_file)
        self.config.set("main", "autosave_picture", self.autosave_picture)
        self.config.set("main", "autosave_picture_dir", self.autosave_picture_dir)
        self.config.set("main", "autosave_picture_file", self.autosave_picture_file)
        self.config.set("main", "shutter_sound", self.shutter_sound)
        self.config.set("main", "shutter_type", self.shutter_type)

        self.config.set("main", "webcam_show_preview", self.webcam_show_preview)
        self.config.set("main", "webcam_preview_pos", self.webcam_preview_pos)
        self.config.set("main", "webcam_resolution", self.webcam_resolution)

        self.config.set("main", "yt_stream", self.yt_stream)
        self.config.set("main", "yt_server", self.yt_server)

        self.config.set("main", "tw_stream", self.tw_stream)
        self.config.set("main", "tw_server", self.tw_server)

        self.config.set("main", "broadcast_dst", self.broadcast_dst)

        self.config.write()


class hw:
    def __init__(self):
        self.logger = logging.getLogger("Prefs-HW")
        self.logger.debug("Getting hardware specs")
        self.screens = None
        self.combined_screen = None

        self.webcam = Webcam()

        self.get_screens()
        self.get_webcams()

    def get_current_screen(self, window=None):
        try:
            if window:
                screen = self.default_screen.get_monitor_at_window(window.get_window())
            else:
                disp = GdkX11.X11Display.get_default()
                dm = Gdk.Display.get_device_manager(disp)
                pntr_device = dm.get_client_pointer()
                (src, x, y) = pntr_device.get_position()
                screen = self.default_screen.get_monitor_at_point(x, y)
        except:
            screen = 0
        return screen

    def get_screens(self):
        try:
            self.logger.debug("Getting Video sources.")
            self.screens = []
            self.default_screen = Gdk.Screen.get_default()
            self.logger.debug("Found {0} monitor(s).".format(self.default_screen.get_n_monitors()))

            for i in range(self.default_screen.get_n_monitors()):
                rect = self.default_screen.get_monitor_geometry(i)
                self.logger.debug("  Monitor {0} - X: {1}, Y: {2}, W: {3}, H: {4}".format(i,
                                                                                          rect.x,
                                                                                          rect.y,
                                                                                          rect.width,
                                                                                          rect.height))
                self.screens.append({"x": rect.x,
                                     "y": rect.y,
                                     "width": rect.width,
                                     "height": rect.height})

            if self.default_screen.get_n_monitors() > 1:
                self.combined_screen = {"x": 0, "y": 0,
                                        "width": self.default_screen.get_width(),
                                        "height": self.default_screen.get_height()}
                self.logger.debug("  Combined - X: 0, Y: 0, W: {0}, H: {1}".format(self.default_screen.get_width(),
                                                                                   self.default_screen.get_height()))
            else:
                self.combined_screen = None

        except:
            self.logger.warning("Unable to find any video sources.")

    def get_webcams(self):
        self.webcam.detect()


def detect_codecs():
    logger = logging.getLogger("Prefs-DC")
    from gi.repository import Gst

    Gst.init(None)

    codecs_supported = []
    codec_test = None
    for codec in CODEC_LIST:
        logger.debug("Testing for: {0}".format(codec[2]))
        if codec[0]:
            try:
                codec_test = Gst.ElementFactory.make(codec[1], "video_encoder")
            except:
                logger.debug("Error loading {0} GStreamer plugin - support disabled.".format(codec[1]))
                codec_test = None

            if codec_test:
                codecs_supported.append(codec[0])
                logger.debug("Supported encoder: {0}.".format(codec[2]))
            else:
                logger.debug("Unable to find {0} GStreamer plugin - support disabled.".format(codec))

        else:
            # RAW codec is None, so we don't try to load it.
            codecs_supported.append(codec[0])
            logger.debug("Supported encoder: {0}.".format(codec[2]))
        codec_test = None
    return codecs_supported


def get_codec(codec):
    for c in CODEC_LIST:
        if c[0] == codec:
            return c
    return None


#
# The dreaded constants, we like those from time to time. Really.
#
# Codecs

CODEC_RAW = 0
CODEC_VP8 = 1
CODEC_H264 = 2
CODEC_HUFF = 3
CODEC_JPEG = 4

#
# Number, gstreamer element name, string description, file extension, advanced
#

CODEC_LIST = [[0, None, 'RAW (AVI)', '.avi', True],
              [1, 'vp8enc', 'VP8 (WEBM)', '.webm', False],
              [2, 'x264enc', 'H264 (MP4)', '.mp4', False],
              [3, 'avenc_huffyuv', 'HUFFYUV (AVI)', '.avi', True],
              [4, 'avenc_ljpeg', 'Lossless JPEG (AVI)', '.avi', True],
              ]

# PulseAudio Error Codes
PA_LOAD_ERROR = 1
PA_GET_STATE_ERROR = 2
PA_STARTUP_ERROR = 3
PA_UNABLE_TO_CONNECT = 4
PA_UNABLE_TO_CONNECT2 = 5
PA_MAINLOOP_START_ERROR = 6
PA_GET_SOURCES_ERROR = 7
PA_GET_SOURCES_TIMEOUT = 8
PA_GET_SOURCE_ERROR = 9
PA_GET_SOURCE_TIMEOUT = 10
PA_MAINLOOP_END_ERROR = 11

# PulseAudio Status Codes
PA_STOPPED = 0
PA_WORKING = 1
PA_FINISHED = 2
PA_ERROR = 3

# PulseAudio State Codes
PA_STATE_READY = 0
PA_STATE_BUSY = 1
PA_STATE_FAILED = 2
PA_STATE_WORKING = 3

# Various actions
ACTION_SAVE = 0
ACTION_EDIT = 1

# Blink modes and states
BLINK_STOP = 0
BLINK_START = 1
BLINK_SLOW = 2
BLINK_FAST = 3
BLINK_STOP_ICON = 4
BLINK_READY_ICON = 5

# Main modes
MODE_SCREENCAST = 0
MODE_SCREENSHOT = 1
MODE_BROADCAST = 2
MODE_WEBCAM = 3

# Record modes
MODE_FULL = 0
MODE_ALL = 1
MODE_AREA = 2
MODE_WIN = 3
MODE_ACTIVE = 4
MODE_GOD = 666

# Area resize handles
HANDLE_TL = 0
HANDLE_TC = 1
HANDLE_TR = 2
HANDLE_CL = 3
HANDLE_MOVE = 4
HANDLE_CR = 5
HANDLE_BL = 6
HANDLE_BC = 7
HANDLE_BR = 8

CAM_PREVIEW_TL = 0
CAM_PREVIEW_TR = 1
CAM_PREVIEW_BR = 2
CAM_PREVIEW_BL = 3

CAM_RESOLUTIONS = [
    [320, 240],
    [640, 480],
    [800, 600],
    [1024, 768]
]

# Area resize handle cursors
HANDLE_CURSORS = (
    Gdk.CursorType.TOP_LEFT_CORNER,
    Gdk.CursorType.TOP_SIDE,
    Gdk.CursorType.TOP_RIGHT_CORNER,
    Gdk.CursorType.LEFT_SIDE,
    Gdk.CursorType.FLEUR,
    Gdk.CursorType.RIGHT_SIDE,
    Gdk.CursorType.BOTTOM_LEFT_CORNER,
    Gdk.CursorType.BOTTOM_SIDE,
    Gdk.CursorType.BOTTOM_RIGHT_CORNER
)

#
# Keyboard modifiers
#
K_SHIFT = 0
K_CTRL = 1
K_SUPER = 2
K_ALT = 3

KEY_STRINGS = ["Shift",
               "Control",
               "Super",
               "Alt", ]
#
# Singletons, because we also like singletons from time to time ... :)
#

prefs = Prefs()
HW = hw()
