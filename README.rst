|image0| Kazam - Linux Desktop Screen Recorder and Broadcaster
==================================================================

|Documentation Status| |CodeCov| |Github release| |lic|


Kazam is a simple screen recording program that will capture the content of your screen and record a video file that can be played by any video player that supports VP8/WebM video format. Optionally you can record sound from any sound input device that is supported and visible by PulseAudio.

Installation
============================

.. code:: bash

   pip install kazam


Kazam need some dependency libraries like `dbus`, `cairo` to work, in Ubuntu 22.04, you can use the following command to install them:

.. code:: bash

   sudo apt install build-essential libpython3-dev \
       libdbus-1-dev libcairo2-dev libgirepository1.0-dev -y


Screenshot
============================

.. figure:: https://github.com/henrywoo/kazam/blob/master/img/Kazam_001.png?raw=true
   :alt: Kazam GUI Screenshot


.. figure:: https://github.com/henrywoo/kazam/blob/master/img/Kazam_002.png?raw=true
   :alt: Kazam Preferences Screenshot



Running Kazam
============================

From Source Code
~~~~~~~~~~~~~~~~~~~~~~

If you want to run Kazam from the source tree, there are a few limitations that you have to take into account. Every icon has to be taken from currently installed icon theme. Toolbars will not show any icons and you will not see Unity AppIndicator.

To run Kazam simply execute te following commands in the source tree:

.. code:: bash

  $ pip install -r requirements.txt
  $ cd bin
  $ ./kazam


From Command Line
~~~~~~~~~~~~~~~~~~~~~~

Make sure **~/.local/bin** into you PATH, and run `kazam` in your terminal should work.


From GUI
~~~~~~~~~~~~~~~~~~~~~~
If you already have Kazam installed then Kazam icons will be displayed properly.


Keyboard shortcuts
============================

.. code:: bash

  SUPER-CTRL-Q - Quit
  SUPER-CTRL-W - Show/Hide main window
  SUPER-CTRL-R - Start Recording
  SUPER-CTRL-F - Finish Recording

In a normal logitech keyboard, SUPER-CTRL is Ctrl+CMD.



Recording Tips
============================

Choose small numerb of framerate. My personal setup is framerate equal to 3. Framerates above 20fps are unlikely to work well because of software and hardware limitations. If you increase framerate and framerate in resulting video drops, that is because encoder can't keep up.

Always do a sound check. Especially if you are recording a live commentary with background sound. I got the best results when I used earphones to listen to the audio while recording. This way your mic will not pick up any audio coming from speakers.

If you _really_ want loss-less quality, then you will have to record in RAW format. This is possible, but without an SSD with a lot of free space your results will be terrible. 1920x1080 at 15 frames per second will need around 45 MB of disk space per second. Most people will want to record at 20 or 25 frames per second. Most disk will not handle that and your
system will start to crawl.

Your next best bet is HUFFYUV format, which is a little bit friendlier on disk bandwidth with 28 MB per second at 15 frames per second. The problem? Not many video editors and players can handle HUFFYUV, let alone video sharing services.



Debugging & reporting problems
========================================================

If you encounter a bug or any kind of unexpected behavior please try to reproduce it while you run Kazam from standard terminal with --debug option. Please report bugs at (https://github.com/henrywoo/kazam/issues) and include generated output.


----

.. |image0| image:: https://raw.githubusercontent.com/henrywoo/kazam/master/kazam.png
.. |Documentation Status| image:: https://readthedocs.org/projects/hiq/badge/?version=latest
   :target: https://hiq.readthedocs.io/en/latest/?badge=latest
.. |CodeCov| image:: https://codecov.io/gh/uber/athenadriver/branch/master/graph/badge.svg
   :target: https://hiq.readthedocs.io/en/latest/index.html
.. |Github release| image:: https://img.shields.io/badge/release-v1.5.7-red
   :target: https://github.com/uber/athenadriver/releases
.. |lic| image:: https://img.shields.io/badge/License-Apache--2.0-red
   :target: https://github.com/uber/athenadriver/blob/master/LICENSE
