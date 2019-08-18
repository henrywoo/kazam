# -*- coding: utf-8 -*-
#
#       authenticate.py
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

from gettext import gettext as _
from gi.repository import Gtk
from kazam.version import *

AUTHORS = """
Andrew Higginson <rugby471@gmail.com>
David Klasinc <bigwhale@lubica.net>
"""

ARTISTS = """
Matthew Paul Thomas <mpt@canonical.com>
Georgi Karavasilev <kokoto-java@ubuntu.com>
Frank Souza <franksouza183@gmail.com>
Sam Hewitt <snwh@ubuntu.com>
Robert McKenna <ttk1opc@yahoo.com>
Andrew Higginson <rugby471@gmail.com>
"""

LICENSE = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


def AboutDialog(icons):
    dialog = Gtk.AboutDialog()
    dialog.set_program_name(_("Kazam") + " - \"" + CODENAME + "\"")
    dialog.set_comments(_("Record a video of activity on your screen or capture a screenshot."))
    dialog.set_license(LICENSE)
    dialog.set_version(VERSION)
    dialog.set_copyright("© 2010 Andrew Higginson, © 2012 David Klasinc")
    dialog.set_website("http://launchpad.net/kazam")
    dialog.set_authors(AUTHORS.split("\n"))
    dialog.set_artists(ARTISTS.split("\n"))
    try:
        icon = icons.load_icon("kazam", 96, Gtk.IconLookupFlags.GENERIC_FALLBACK)
        dialog.set_logo(icon)
    except:
        # Not important, we just don't get to show our lovely logo.. :)
        pass
    dialog.show_all()
    dialog.set_position(Gtk.WindowPosition.CENTER)
    dialog.run()
    dialog.hide()
