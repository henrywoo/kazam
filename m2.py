import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class MyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Hello")

        self.box = Gtk.Box(orientation="vertical", spacing=2)
        self.add(self.box)

        self.btn1 = Gtk.Button(label="For")
        self.btn1.connect("clicked", self.btn_clicked)
        self.btn2 = Gtk.Button(label="Against")
        self.btn2.connect("clicked", self.btn_clicked)

        self.box.pack_start(self.btn1, True, True, 0)
        self.box.pack_start(self.btn2, True, True, 0)

    def btn_clicked(self, widget):
        res = widget.get_property("label")
        if res == "For":
            print("Always agreeing")
        else:
            print("You can't please everyone")

win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()