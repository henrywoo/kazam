# -*- coding: utf-8 -*-
#
#       webcam.py
#
#       Copyright 2014 David Klasinc <bigwhale@lubica.net>
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

from gi.repository import GObject, GUdev

logger = logging.getLogger("Webcam")


class Webcam(GObject.GObject):

    """docstring for Webcam."""

    __gsignals__ = {"webcam-change": (GObject.SIGNAL_RUN_LAST,
                    None,
                    (),),
                    }

    def __init__(self):
        super(Webcam, self).__init__()

        self.device_list = {}
        self.has_webcam = False

        logger.debug("Initializing webcam support.")
        try:
            self.udev_client = GUdev.Client.new(subsystems=['video4linux'])
            self.udev_client.connect("uevent", self.watch)
        except:
            logger.warning("Unable to initialize webcam support.")
        self.detect()

    def watch(self, client, action, device):
        logger.debug("Webcam device list: {}".format(self.device_list))
        logger.debug("Webcam change detected: {}".format(action))
        if action == 'add':
            try:
                c_name = device.get_property('ID_V4L_PRODUCT')
                c_devname = device.get_property('DEVNAME')
                if (c_devname, c_name) not in self.device_list:
                    self.device_list.append((c_devname, c_name))
                    logger.debug("New webcam found: {}".format(c_name))
                else:
                    logger.warning("Duplicate cam detected!? {} {}".format(c_devname, c_name))

            except Exception as e:
                logger.debug("Unable to register new webcam. {}".format(e.str))
        elif action == 'remove':
            try:
                c_name = device.get_property('ID_V4L_PRODUCT')
                c_devname = device.get_property('DEVNAME')
                logger.debug("Removing webcam {}".format(c_name))
                for cam in self.device_list:
                    if c_devname == cam[0]:
                        self.device_list.remove(cam)
                        logger.debug("Removed webcam {}".format(c_name))
            except Exception as e:
                logger.debug("Unable to de-register a webcam. {}".format(e.str))

        else:
            logger.debug("Unknown UDEV action {}.".format(action))
        self.emit("webcam-change")

    def detect(self):
        self.device_list = []
        #try:
        cams = self.udev_client.query_by_subsystem(subsystem='video4linux')
        if cams:
            for c in cams:
                c_name = c.get_property('ID_V4L_PRODUCT')
                c_devname = c.get_property('DEVNAME')
                logger.debug("  Webcam found: {0}".format(c_name))
                self.device_list.append((c_devname, c_name))
        else:
                logger.info("Webcam not detected.")
        # except:
        #     logger.debug("Error while detecting webcams.")

        if self.device_list:
            self.has_webcam = True

        return self.device_list

    def get_device_file(self, num):
        try:
            return self.device_list[num][2]
        except:
            return None
