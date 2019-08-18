# -*- coding: utf-8 -*-
#
#       preferences.py
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
import math
import logging

from gi.repository import Gtk, GObject, Pango

from kazam.utils import *
from kazam.backend.prefs import *

logger = logging.getLogger("Preferences")


class Preferences(GObject.GObject):
    __gsignals__ = {
        "prefs-quit": (GObject.SIGNAL_RUN_LAST,
                       None,
                       (),
                       ),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        logger.debug("Preferences Init.")
        #
        # Setup UI
        #
        logger.debug("Preferences UI setup.")

        self.audio_source_info = None
        self.audio2_source_info = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(prefs.datadir, "ui", "preferences.ui"))
        self.builder.connect_signals(self)
        for w in self.builder.get_objects():
            if issubclass(type(w), Gtk.Buildable):
                name = Gtk.Buildable.get_name(w)
                setattr(self, name, w)
            else:
                logger.debug("Unable to get name for '%s'" % w)

        codec_renderer = Gtk.CellRendererText()

        audio_renderer = Gtk.CellRendererText()
        audio_renderer.props.ellipsize = Pango.EllipsizeMode.END
        audio_renderer.props.max_width_chars = 40

        webcam_renderer = Gtk.CellRendererText()

        self.combobox_codec.pack_start(codec_renderer, True)
        self.combobox_codec.add_attribute(codec_renderer, "text", 1)

        self.combobox_audio.pack_start(audio_renderer, True)
        self.combobox_audio.add_attribute(audio_renderer, "text", 0)

        self.combobox_audio2.pack_start(audio_renderer, True)
        self.combobox_audio2.add_attribute(audio_renderer, "text", 0)

        self.combobox_webcam.pack_start(webcam_renderer, True)
        self.combobox_webcam.add_attribute(webcam_renderer, "text", 1)

        self.filechooser_video.set_current_folder(prefs.video_dest)

        self.populate_codecs()
        if prefs.sound:
            self.populate_audio_sources()
        self.populate_shutter_sounds()

        self.populate_webcams()

        self.restore_UI()
        self.window.set_position(Gtk.WindowPosition.CENTER)

    def open(self):
        self.window.show_all()

    def is_separator(self, model, iter, data):
        if model.get_value(iter, 0) == 99:
            return True
        return False

    def populate_codecs(self):
        #
        # Is this necessary?
        #
        old_model = self.combobox_codec.get_model()
        old_model = None

        codec_model = Gtk.ListStore(int, str)
        codecs = detect_codecs()

        #
        # I'm sure this could be done without going through the list twice, right?
        # Fist, we add basic codecs, then a dummy separator item and then advanced codecs.
        #

        for codec in codecs:
            if not CODEC_LIST[codec][4]:
                codec_model.append([CODEC_LIST[codec][0], CODEC_LIST[codec][2]])

        codec_model.append([99, "--"])  # Insert dummy item for separator

        for codec in codecs:
            if CODEC_LIST[codec][4]:
                codec_model.append([CODEC_LIST[codec][0], CODEC_LIST[codec][2]])

        self.combobox_codec.set_model(codec_model)
        self.combobox_codec.set_row_separator_func(self.is_separator, None)

    def populate_audio_sources(self):
        speaker_source_model = Gtk.ListStore(str, int)
        mic_source_model = Gtk.ListStore(str, int)
        for source in prefs.audio_sources:
            logger.debug("Adding audio device D: {} Idx: {}".format(source[2], source[0]))
            if "Monitor" in source[2]:
                speaker_source_model.append([source[2], source[0]])
            else:
                mic_source_model.append([source[2], source[0]])

        self.combobox_audio.set_model(speaker_source_model)
        self.combobox_audio2.set_model(mic_source_model)

    def populate_shutter_sounds(self):
        for s_file in prefs.sound_files:
            self.combobox_shutter_type.append(None, s_file[:-4])

    def populate_webcams(self):
        webcam_source_model = Gtk.ListStore(str, str)
        for cam in prefs.webcam_sources:
            webcam_source_model.append((cam[0], cam[1]))

        self.combobox_webcam.set_model(webcam_source_model)

    def restore_UI(self):
        logger.debug("Restoring UI.")

        if prefs.sound:
            self.combobox_audio.set_active(prefs.audio_source)
            self.combobox_audio2.set_active(prefs.audio2_source)
        else:
            self.combobox_audio.set_sensitive(False)
            self.combobox_audio2.set_sensitive(False)
            self.volumebutton_audio.set_sensitive(False)
            self.volumebutton_audio2.set_sensitive(False)

        if prefs.countdown_splash:
            self.switch_countdown_splash.set_active(True)
        else:
            self.switch_countdown_splash.set_active(False)

        self.spinbutton_framerate.set_value(prefs.framerate)

        if prefs.autosave_video:
            self.switch_autosave_video.set_active(True)
            self.filechooser_video.set_sensitive(True)
            self.entry_autosave_video.set_sensitive(True)
        else:
            self.switch_autosave_video.set_active(False)
            self.filechooser_video.set_sensitive(False)
            self.entry_autosave_video.set_sensitive(False)

        self.entry_autosave_video.set_text(prefs.autosave_video_file)

        self.filechooser_video.set_current_folder(prefs.autosave_video_dir)

        if prefs.shutter_sound:
            self.switch_shutter_sound.set_active(True)
            self.combobox_shutter_type.set_sensitive(True)
        else:
            self.switch_shutter_sound.set_active(False)
            self.combobox_shutter_type.set_sensitive(False)

        self.combobox_shutter_type.set_active(prefs.shutter_type)

        if prefs.autosave_picture:
            self.switch_autosave_picture.set_active(True)
            self.filechooser_picture.set_sensitive(True)
            self.entry_autosave_picture.set_sensitive(True)

        else:
            self.switch_autosave_picture.set_active(False)
            self.filechooser_picture.set_sensitive(False)
            self.entry_autosave_picture.set_sensitive(False)

        self.combobox_webcam.set_active(prefs.webcam_source)
        self.combobox_webcam_preview.set_active(prefs.webcam_preview_pos)
        self.combobox_webcam_resolution.set_active(prefs.webcam_resolution)

        if prefs.webcam_show_preview:
            self.switch_webcam_preview.set_active(True)
        else:
            self.switch_webcam_preview.set_active(False)

        self.entry_autosave_picture.set_text(prefs.autosave_picture_file)
        self.filechooser_picture.set_current_folder(prefs.autosave_picture_dir)

        self.combobox_broadcast_dst.set_active(prefs.broadcast_dst)

        if prefs.yt_stream:
            self.entry_yt_stream.set_text(prefs.yt_stream)

        if prefs.yt_server:
            self.entry_yt_server.set_text(prefs.yt_server)

        if prefs.tw_stream:
            self.entry_tw_stream.set_text(prefs.tw_stream)

        if prefs.tw_server:
            self.entry_tw_server.set_text(prefs.tw_server)

        #
        # Crappy code below ... Can this be done some other way?
        #
        codec_model = self.combobox_codec.get_model()
        cnt = 0
        bingo = False

        for entry in codec_model:
            if prefs.codec == entry[0]:
                bingo = True
                break
            cnt += 1
        if not bingo:
            cnt = 0

        #
        # No, I wasn't kidding ...
        #
        codec_iter = codec_model.get_iter(cnt)
        self.combobox_codec.set_active_iter(codec_iter)
        prefs.codec = codec_model.get_value(codec_iter, 0)

    #
    # General callbacks
    #

    def cb_delete_event(self, widget, user_data):
        logger.debug("Deleting preferences window")
        self.emit("prefs-quit")

    def cb_switch_countdown_splash(self, widget, user_data):
        prefs.countdown_splash = widget.get_active()
        logger.debug("Countdown splash: {0}.".format(prefs.countdown_splash))

    def cb_audio_changed(self, widget):
        logger.debug("Audio Changed.")
        prefs.audio_source = self.combobox_audio.get_active()
        logger.debug("  - A_1 {0}".format(prefs.audio_source))

        pa_audio_idx = prefs.speaker_sources[prefs.audio_source][0]
        prefs.pa_q.set_source_mute_by_index(pa_audio_idx, 0)

        logger.debug("  - PA Audio1 IDX: {0}".format(pa_audio_idx))
        self.audio_source_info = prefs.pa_q.get_source_info_by_index(pa_audio_idx)
        if len(self.audio_source_info) > 0:
            val = prefs.pa_q.cvolume_to_dB(self.audio_source_info[2])
            if math.isinf(val):
                vol = 0
            else:
                vol = 60 + val
            self.volumebutton_audio.set_value(vol)
        else:
            logger.debug("Error getting volume info for Audio 1")
        if len(self.audio_source_info):
            logger.debug("New Audio1: {0}".format(self.audio_source_info[3]))
        else:
            logger.debug("New Audio1: Error retrieving data.")

    def cb_audio2_changed(self, widget):
        logger.debug("Audio2 Changed.")

        prefs.audio2_source = self.combobox_audio2.get_active()
        logger.debug("  - A_2 {0}".format(prefs.audio2_source))

        pa_audio2_idx = prefs.mic_sources[prefs.audio2_source][0]
        prefs.pa_q.set_source_mute_by_index(pa_audio2_idx, 0)

        logger.debug("  - PA Audio2 IDX: {0}".format(pa_audio2_idx))
        self.audio2_source_info = prefs.pa_q.get_source_info_by_index(pa_audio2_idx)

        if len(self.audio2_source_info) > 0:
            val = prefs.pa_q.cvolume_to_dB(self.audio2_source_info[2])
            if math.isinf(val):
                vol = 0
            else:
                vol = 60 + val
            self.volumebutton_audio2.set_value(vol)
        else:
            logger.debug("Error getting volume info for Audio 1")

        if len(self.audio2_source_info):
            logger.debug("New Audio2:\n  {0}".format(self.audio2_source_info[3]))
        else:
            logger.debug("New Audio2:\n  Error retrieving data.")

    def cb_volume_changed(self, widget, value):
        name = Gtk.Buildable.get_name(widget)
        logger.debug("Volume changed for {0}, new value: {1}".format(name, value))
        if name == 'volumebutton_audio':
            idx = self.combobox_audio.get_active()
            model = self.combobox_audio.get_model()
            chn = self.audio_source_info[2].channels
        else:
            idx = self.combobox_audio2.get_active()
            model = self.combobox_audio2.get_model()
            chn = self.audio2_source_info[2].channels

        c_iter = model.get_iter(idx)
        idx = model.get_value(c_iter, 1)
        pa_idx = list(get_by_idx(prefs.audio_sources, idx))[0][0]
        cvol = prefs.pa_q.dB_to_cvolume(chn, value - 60)
        prefs.pa_q.set_source_volume_by_index(pa_idx, cvol)

    #
    # Screencasting callbacks
    #

    def cb_spinbutton_framerate_change(self, widget):
        prefs.framerate = widget.get_value_as_int()
        logger.debug("Framerate now: {0}".format(prefs.framerate))

    def cb_codec_changed(self, widget):
        i = widget.get_active()
        model = widget.get_model()
        c_iter = model.get_iter(i)
        prefs.codec = model.get_value(c_iter, 0)
        logger.debug('Codec selected: {0} - {1}'.format(get_codec(prefs.codec)[2], prefs.codec))

    def cb_switch_autosave_video(self, widget, user_data):
        prefs.autosave_video = widget.get_active()
        logger.debug("Autosave for Video: {0}.".format(prefs.autosave_video))

        if prefs.autosave_video:
            self.filechooser_video.set_sensitive(True)
            self.entry_autosave_video.set_sensitive(True)
        else:
            self.filechooser_video.set_sensitive(False)
            self.entry_autosave_video.set_sensitive(False)

    def cb_filechooser_video(self, widget):
        prefs.autosave_video_dir = self.filechooser_video.get_current_folder()
        logger.debug("Autosave video folder set to: {0}".format(prefs.autosave_video_dir))

    def cb_entry_autosave_video(self, widget):
        prefs.autosave_video_file = widget.get_text()
        logger.debug("Video autosave file set to: {0}".format(prefs.autosave_video_file))

    #
    # Screenshot callbacks
    #

    def cb_switch_shutter_sound(self, widget, user_data):
        prefs.shutter_sound = widget.get_active()
        logger.debug("Shutter sound: {0}.".format(prefs.shutter_sound))

        if prefs.shutter_sound:
            self.combobox_shutter_type.set_sensitive(True)
        else:
            self.combobox_shutter_type.set_sensitive(False)

    def cb_shutter_type(self, widget):
        prefs.shutter_type = self.combobox_shutter_type.get_active()
        logger.debug("Shutter type set to: {0} - {1}".format(prefs.shutter_type, prefs.shutter_sound_file))

    def cb_switch_autosave_picture(self, widget, user_data):
        prefs.autosave_picture = widget.get_active()
        logger.debug("Autosave for Picture: {0}.".format(prefs.autosave_picture))

        if prefs.autosave_picture:
            self.filechooser_picture.set_sensitive(True)
            self.entry_autosave_picture.set_sensitive(True)
        else:
            self.filechooser_picture.set_sensitive(False)
            self.entry_autosave_picture.set_sensitive(False)

    def cb_filechooser_picture(self, widget):
        prefs.autosave_picture_dir = self.filechooser_picture.get_current_folder()
        logger.debug("Autosave picture folder set to: {0}".format(prefs.autosave_picture_dir))

    def cb_entry_autosave_picture(self, widget):
        prefs.autosave_picture_file = widget.get_text()
        logger.debug("Picture autosave file set to: {0}".format(prefs.autosave_picture_file))

    #
    # Webcam callbacks
    #
    def cb_webcam_changed(self, widget):
        logger.debug("Webcam changed.")
        prefs.webcam_source = self.combobox_webcam.get_active()
        logger.debug("  - CAM_0 {0}".format(prefs.webcam_source))

    def cb_combobox_webcam_preview_changed(self, widget):
        logger.debug("Webcam preview position set to:")
        prefs.webcam_preview_pos = self.combobox_webcam_preview.get_active()
        logger.debug("  {}".format(prefs.webcam_preview_pos))

    def cb_switch_webcam_preview(self, widget, user_data):
        prefs.webcam_show_preview = widget.get_active()
        logger.debug("Webcam preview: {}".format(prefs.webcam_show_preview))

    def cb_combobox_webcam_resolution_changed(self, widget):
        prefs.webcam_resolution = self.combobox_webcam_resolution.get_active()
        logger.debug("Webcam resolution: {}".format(prefs.webcam_resolution))

    #
    # Broadcast callbacks
    #

    def cb_broadcast_change(self, widget):
        prefs.broadcast_dst = self.combobox_broadcast_dst.get_active()
        logger.debug("Broadcast destination set to: {}".format(prefs.broadcast_dst))

    def cb_entry_yt_stream(self, widget):
        prefs.yt_stream = widget.get_text()
        logger.debug("YouTube Live stream set to: {}".format(prefs.yt_stream))

    def cb_entry_yt_server(self, widget):
        prefs.yt_server = widget.get_text()
        logger.debug("YouTube Live server set to: {}".format(prefs.yt_server))

    def cb_entry_tw_stream(self, widget):
        prefs.tw_stream = widget.get_text()
        logger.debug("Twitch stream set to: {}".format(prefs.tw_stream))

    def cb_entry_tw_server(self, widget):
        prefs.tw_server = widget.get_text()
        logger.debug("Twitch stream url set to: {}".format(prefs.tw_server))
