# -*- coding: utf-8 -*-
#
#       utils.py
#
#       Copyright 2018 Henry Fuheng Wu <wufuheng@gmail.com>
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

def show_popup(message, title="Kazam Notification"):
    from gi.repository import Gtk
    full_message = f"{title}:\n\n{message}"  # Combine title and message with spacing
    dialog = Gtk.MessageDialog(
        transient_for=None,
        flags=0,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text=full_message,  # Display the formatted message
    )
    dialog.set_title(title)  # Set the actual window title
    dialog.run()
    dialog.destroy()



def is_xdotool_installed():
    import subprocess
    try:
        subprocess.run(["xdotool", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False
    except PermissionError:
        return False

