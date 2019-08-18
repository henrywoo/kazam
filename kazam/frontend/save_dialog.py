# -*- coding: utf-8 -*-
#
#       save_dialog.py
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
import logging
logger = logging.getLogger("Save Dialog")

from datetime import datetime
from gettext import gettext as _

from gi.repository import Gtk

from kazam.backend.prefs import *

def SaveDialog(title, old_path, codec, main_mode=MODE_SCREENCAST):
    logger.debug("Save dialog called with path: {0}".format(old_path))
    dialog = Gtk.FileChooserDialog(title, None,
                                   Gtk.FileChooserAction.SAVE,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    _("Save"), Gtk.ResponseType.OK))

    dt = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    if main_mode == MODE_SCREENCAST:
        dialog.set_current_name("{0} {1}{2}".format(_("Screencast"), dt, CODEC_LIST[codec][3]))
    elif main_mode == MODE_SCREENSHOT:
        dialog.set_current_name("{0} {1}.png".format(_("Screenshot"), dt))

    dialog.set_do_overwrite_confirmation(True)

    if old_path and os.path.isdir(old_path):
        dialog.set_current_folder(old_path)
        logger.debug("Previous path is a valid destination")
    else:
        if main_mode in [MODE_SCREENCAST,  MODE_WEBCAM, MODE_BROADCAST]:
            dialog.set_current_folder(prefs.video_dest)
            logger.debug("Previous path invalid, setting it to: {0}".format(prefs.video_dest))
        elif main_mode == MODE_SCREENSHOT:
            dialog.set_current_folder(prefs.picture_dest)
            logger.debug("Previous path invalid, setting it to: {0}".format(prefs.picture_dest))

    dialog.show_all()
    result = dialog.run()
    old_path = dialog.get_current_folder()
    return dialog, result, old_path
