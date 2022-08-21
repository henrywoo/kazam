import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

if __name__ == "__main__":
    window = Gtk.Window(title="Hello World")
    window.show()
    window.connect("destroy", Gtk.main_quit)
    Gtk.main()