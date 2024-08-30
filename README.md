# ![image0](https://raw.githubusercontent.com/henrywoo/kazam/master/kazam.png) Kazam2 - Linux Screen Recorder, Broadcaster, Capture and OCR

![Documentation Status](https://readthedocs.org/projects/hiq/badge/?version=latest) ![CodeCov](https://codecov.io/gh/uber/athenadriver/branch/master/graph/badge.svg) ![Github release](https://img.shields.io/badge/release-v2.0.0-red) ![License](https://img.shields.io/badge/License-Apache--2.0-red)

Kazam 2.0 is a versatile tool for **screen recording, broadcasting, capturing and optical character recognition(OCR)**.

![Kazam GUI Screenshot](https://raw.githubusercontent.com/henrywoo/images/main/kazam.png)

Main Features:

1. **Screen Recording**: Kazam allows you to capture everything displayed on your screen and save it as a video file. The recorded video is saved in a format compatible with any media player that supports H264, VP8 codec and WebM video format.

2. **Broadcasting**: Kazam offers the ability to broadcast your screen content live over the internet, making it suitable for live streaming sessions. It supports Twitch and Youtube live broadcasting at the time of this writing.

3. **Optical Character Recognition (OCR)**: Kazam includes OCR functionality, enabling it to detect and extract text from the captured screen content, which can then be edited or saved.

4. **Audio Recording**: In addition to screen content, Kazam can record audio from any sound input device that is recognized and supported by the PulseAudio sound system. This allows you to capture both the screen and accompanying audio, such as voice narration or system sounds, in your recordings.

5. **Web Camera**: Kazam support web camera recording and users can drag and drop webcam window anywhere in the screen to suit the recording need.

6. **Full Screen, Window and Area Mode**: Kazam support full screen, window and area modes.

📌 **Please use the latest version kazam 2.0.0. Make sure the version is the latest when you report issues.**

```bash
🍄 Tested in: Ubuntu 20.04, 22.04, and 24.04 with Python 3.8 - 3.12.
```

## 📥 Installation

```bash
pip install -U kazam
```

Kazam needs some dependency libraries like `dbus`, `cairo` to work. In Ubuntu, you can use the following command to install them:

```bash
sudo apt install build-essential libpython3-dev \
    libdbus-1-dev libcairo2-dev libgirepository1.0-dev \
    gir1.2-gudev-1.0 gir1.2-keybinder-3.0 python3-gi python3-gst-1.0 xdotool -y
```

In Ubuntu, make sure the PulseAudio GStreamer plugin is installed. If not, run:

```bash
sudo apt reinstall gstreamer1.0-pulseaudio -y
```

- To use OCR features, please install:

```bash
sudo apt-get install tesseract-ocr -y
pip install pytesseract pillow rapidocr-onnxruntime
```

## 🧸 Screenshots

- Live Broadcasting

![Kazam GUI Screenshot](https://raw.githubusercontent.com/henrywoo/images/main/live.png)

- Preferences Window

![Kazam Preferences Screenshot](https://raw.githubusercontent.com/henrywoo/images/main/prefs.png)

## 💎 Running Kazam

### From Source Code

If you want to run Kazam from the source tree, there are a few limitations that you have to take into account. Every icon has to be taken from the currently installed icon theme. Toolbars will not show any icons, and you will not see Unity AppIndicator.

To run Kazam, simply execute the following commands in the source tree:

```bash
pip install -r requirements.txt
cd bin
./kazam
```

### From Command Line

Make sure **~/.local/bin** is in your PATH, and running `kazam` in your terminal should work.

### From GUI

If you already have Kazam installed, then Kazam icons will be displayed properly.

## ⌨️ Keyboard Shortcuts

```bash
SUPER-CTRL-Q - Quit
SUPER-CTRL-W - Show/Hide main window
SUPER-CTRL-R - Start Recording
SUPER-CTRL-F - Finish Recording
```

On a normal Logitech keyboard, SUPER-CTRL is `Ctrl+CMD`.

## 💡 Recording Tips

- Choose a small framerate. My personal setup is framerate equal to 3. Framerates above 20fps are unlikely to work well because of software and hardware limitations. If you increase the framerate and the resulting video framerate drops, that is because the encoder can't keep up.

- Always do a sound check, especially if you are recording live commentary with background sound. I got the best results when I used earphones to listen to the audio while recording. This way, your mic will not pick up any audio coming from the speakers.

- If you _really_ want lossless quality, then you will have to record in RAW format. This is possible, but without an SSD with a lot of free space, your results will be terrible. 1920x1080 at 15 frames per second will need around 45 MB of disk space per second. Most people will want to record at 20 or 25 frames per second. Most disks will not handle that, and your system will start to crawl.

- Your next best bet is HUFFYUV format, which is a little bit friendlier on disk bandwidth with 28 MB per second at 15 frames per second. The problem? Not many video editors and players can handle HUFFYUV, let alone video sharing services.

## 💣 Debugging & Reporting Problems

If you encounter a bug or any kind of unexpected behavior, please try to reproduce it while running Kazam from a standard terminal with the `--debug` option. Please report bugs at [https://github.com/henrywoo/kazam/issues](https://github.com/henrywoo/kazam/issues) and include the generated output.

