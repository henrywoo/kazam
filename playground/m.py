import gi
import numpy as np
import matplotlib.pyplot as plt
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
def display_buffer(buffer, width, height):
    arr = np.frombuffer(buffer, dtype=np.uint8)  # Use uint8 as each byte is considered separately
    arr = arr.reshape((height, width, 8))  # 8 bytes for each pixel
    bgr_arr = arr[:, :, 2:7:2]  # Taking B, G, R bytes and skipping alpha
    bgr_arr = bgr_arr // 256  # Convert to 8-bit
    plt.imshow(bgr_arr)
    plt.show()

Gst.init(None)

def video_ocr(sink):
    sample = sink.emit("pull-sample")
    caps = sample.get_caps()
    if caps:
        structure = caps.get_structure(0)
        width = structure.get_int('width').value
        height = structure.get_int('height').value
        format = structure.get_string('format')
        buffer = sample.get_buffer()
        data = buffer.extract_dup(0, buffer.get_size())
        print(f"Received frame of size:{len(data)}, format:{format}, {width}, {height}")
        display_buffer(data, width, height)
    return Gst.FlowReturn.OK

pipeline = Gst.parse_launch('videotestsrc ! videoconvert ! videorate ! video/x-raw,framerate=1/3 ! appsink name=sink emit-signals=True')

sink = pipeline.get_by_name("sink")
sink.connect("new-sample", video_ocr)

pipeline.set_state(Gst.State.PLAYING)
GLib.MainLoop().run()