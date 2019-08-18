# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger("KeypressViewer")
import os
import sys
import signal

from gi.repository import GObject, GLib

from kazam.backend.prefs import *


class KeypressViewer(GObject.GObject):
    __gsignals__ = {
        "keypress": (GObject.SIGNAL_RUN_LAST,
                     None,
                     [GObject.TYPE_PYOBJECT,
                      GObject.TYPE_PYOBJECT,
                      GObject.TYPE_PYOBJECT],)
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        logger.debug("Creating KeypressViewer.")
        self.child_pid = None

    def start(self):
        def readline(io, condition):
            if condition is GLib.IO_IN:
                line = io.readline()
                parts = line.strip().split()
                if len(parts) != 3:
                    logger.debug("Unexpected line from keypress viewer: {}".format(parts))
                else:
                    logger.debug("Got keypress details: '{}'".format(line))
                    self.emit("keypress", parts[0], parts[1], parts[2])
                return True
            elif condition is GLib.IO_HUP | GLib.IO_IN:
                GLib.source_remove(self.source_id)
                return False

        keypress_viewer_exe = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "listkeys-subprocess.py"))
        logger.info("Starting KeypressViewer ({}).".format(keypress_viewer_exe))
        argv = [sys.executable, keypress_viewer_exe]
        self.child_pid, stdin, stdout, stderr = GLib.spawn_async(argv, standard_output=True)
        io = GLib.IOChannel(stdout)
        self.source_id = io.add_watch(GLib.IO_IN | GLib.IO_HUP,
                                      readline, priority=GLib.PRIORITY_HIGH)

    def stop(self):
        if self.child_pid:
            logger.info("Stopping KeypressViewer")
            os.kill(self.child_pid, signal.SIGTERM)
            self.child_pid = None
