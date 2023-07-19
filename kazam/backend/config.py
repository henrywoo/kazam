# -*- coding: utf-8 -*-
#
#       config.py
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
from configparser import ConfigParser, NoSectionError, NoOptionError
from xdg.BaseDirectory import xdg_config_home


class KazamConfig(object):

    DEFAULTS = [{
                "name": "main",
                "keys": {"video_toggled":          "True",
                         "video_source":           "0",
                         "audio_toggled":          "False",
                         "audio_source":           "0",
                         "audio_volume":           "0",
                         "audio2_toggled":         "False",
                         "audio2_source":          "0",
                         "audio2_volume":          "0",
                         "codec":                  "0",
                         "counter":                "5",
                         "capture_cursor":         "True",
                         "capture_speakers":       "False",
                         "capture_microphone":     "False",
                         "capture_cursor_pic":     "True",
                         "capture_borders_pic":    "True",
                         "framerate":              "15",
                         "countdown_splash":       "True",
                         "last_x":                 "60",
                         "last_y":                 "25",
                         "advanced":               "0",
                         "silent":                 "0",
                         "autosave_video":         "False",
                         "autosave_video_dir":     "",
                         "autosave_video_file":    "Kazam_screencast",
                         "autosave_picture":       "False",
                         "autosave_picture_dir":   "",
                         "autosave_picture_file":  "Kazam_screenshot",
                         "shutter_sound":          "True",
                         "shutter_type":           "0",
                         "first_run":              "True",
                         "webcam_source":          "0",
                         "webcam_show_preview":    "True",
                         "webcam_preview_pos":     "1",
                         "webcam_preview_x_offset": "0",
                         "webcam_preview_y_offset": "0",
                         "webcam_resolution":      "0",
                         "capture_speakers_w":     "False",
                         "capture_microphone_w":   "False",
                         "capture_cursor_b":       "False",
                         "capture_speakers_b":     "False",
                         "capture_microphone_b":   "False",
                         "capture_keys":           "False",
                         "capture_keys_b":         "False",
                         "yt_stream":              "",
                         "yt_server":              "",
                         "broadcast_dst":          "1"
                         },
                },
                {"name": "keyboard_shortcuts",
                 "keys": {"pause":  "<Shift><Super>p",
                          "finish": "<Shift><Super>f",
                          "show":   "<Shift><Super>s",
                          "quit":   "<Shift><Super>q",
                          },
                 }]

    CONFIGDIR = os.path.join(xdg_config_home, "kazam")
    CONFIGFILE = os.path.join(CONFIGDIR, "kazam.conf")

    def __init__(self):
        self.config = ConfigParser(self.DEFAULTS[0]['keys'])
        if not os.path.isdir(self.CONFIGDIR):
            os.makedirs(self.CONFIGDIR)
        if not os.path.isfile(self.CONFIGFILE):
            self.create_default()
            self.write()
        self.config.read(self.CONFIGFILE)

    def create_default(self):
        # For every section
        for section in self.DEFAULTS:
            # Add the section
            self.config.add_section(section["name"])
            # And add every key in it, with its default value
            for key in section["keys"]:
                value = section["keys"][key]
                self.set(section["name"], key, value)

    def find_default(self, section, key):
        for d_section in self.DEFAULTS:
            if d_section["name"] == section:
                for d_key in d_section["keys"]:
                    if d_key == key:
                        return d_section["keys"][key]

    def get(self, section, key):
        try:
            ret = self.config.get(section, key)
            if ret == "None":
                default = self.find_default(section, key)
                self.set(section, key, default)
                self.write()
                return default
            else:
                return ret
        except NoSectionError:
            default = self.find_default(section, key)
            self.set(section, key, default)
            self.write()
            return default
        except NoOptionError:
            default = self.find_default(section, key)
            self.set(section, key, default)
            self.write()
            return default
        except ValueError:
            default = self.find_default(section, key)
            self.set(section, key, default)
            self.write()
            return default

    def getboolean(self, section, key):
        val = self.get(section, key)
        if val.lower() == 'true' or val.lower == "on" or val.lower() == "yes":
            return True
        else:
            return False

    def set(self, section, option, value):
        # If the section referred to doesn't exist (rare case),
        # then create it
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))

    def write(self):
        file_ = open(self.CONFIGFILE, "w")
        self.config.write(file_)
        file_.close()
