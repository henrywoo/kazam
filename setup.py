#!/usr/bin/python3

from ctypes.wintypes import LONG
import sys
if sys.version_info < (3, 2):
    sys.exit('Kazam requires Python 3.2 or newer')

import os

here = os.path.dirname(os.path.realpath(__file__))

from distutils.core import setup
from DistUtilsExtra.command import build_extra, build_i18n, build_help, build_icons

import re
import glob

try:
    line = open("kazam/version.py").readline()
    VERSION = re.search(r"VERSION = '(.*)'", line).group(1)
except:
    VERSION = "1.0.0"


LONG_DESC="""
|image0|
============================

|Documentation Status| |CodeCov| |Github release| |lic|


Kazam is a simple screen recording program that will capture the content of your screen and record a video file that can be played by any video player that supports VP8/WebM video format. Optionally you can record sound from any sound input device that is supported and visible by PulseAudio.

Installation
============================

.. code:: bash

   pip install kazam distutils-extra-python

Screenshot
============================

.. figure:: https://github.com/henrywoo/kazam-screen-recorder/blob/tmp/img/Kazam_001.png?raw=true
   :alt: Kazam GUI Screenshot


.. figure:: https://github.com/henrywoo/kazam-screen-recorder/blob/tmp/img/Kazam_002.png?raw=true
   :alt: Kazam Preferences Screenshot



Running Kazam
============================

From Source Code
~~~~~~~~~~~~~~~~~~~~~~

If you want to run Kazam from the source tree, there are a few limitations that you have to take into account. Every icon has to be taken from currently installed icon theme. Toolbars will not show any icons and you will not see Unity AppIndicator.

To run Kazam simply execute te following commands in the source tree:

.. code:: bash

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

If you encounter a bug or any kind of unexpected behavior please try to reproduce it while you run Kazam from standard terminal with --debug option. Use Launchpad to report bugs (https://github.com/henrywoo/kazam-screen-recorder/issues) and include generated output.

----

.. |image0| image:: https://raw.githubusercontent.com/henrywoo/kazam-screen-recorder/master/kazam.png
.. |Documentation Status| image:: https://readthedocs.org/projects/hiq/badge/?version=latest
   :target: https://hiq.readthedocs.io/en/latest/?badge=latest
.. |CodeCov| image:: https://codecov.io/gh/uber/athenadriver/branch/master/graph/badge.svg
   :target: https://hiq.readthedocs.io/en/latest/index.html
.. |Github release| image:: https://img.shields.io/badge/release-v1.5.7-red
   :target: https://github.com/uber/athenadriver/releases
.. |lic| image:: https://img.shields.io/badge/License-Apache--2.0-red
   :target: https://github.com/uber/athenadriver/blob/master/LICENSE

"""

setup(name='kazam',
      version=VERSION,
      description='A screencasting program created with design in mind.',
      author='Henry Fuheng Wu, David Klasinc',
      author_email='wufuheng@gmail.com, bigwhale@lubica.net',
      long_description=LONG_DESC,
      classifiers=['Development Status :: 4',
                   'Environment :: X11 Applications :: GTK',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
                   'Operating System :: POSIX :: Linux',
                   'Programming Language :: Python',
                   'Topic :: Multimedia :: Graphics :: Capture :: Screen Capture',
                   'Topic :: Multimedia :: Sound/Audio :: Capture/Recording',
                   'Topic :: Multimedia :: Video :: Capture',
                  "Programming Language :: Python :: 3",
                  "Programming Language :: Python :: 3.3",
                  "Programming Language :: Python :: 3.4",
                  "Programming Language :: Python :: 3.5",
                  "Programming Language :: Python :: 3.6",
                  "Programming Language :: Python :: 3.7",
                  "Programming Language :: Python :: 3.8",
                  "Programming Language :: Python :: 3.9",
                  "Programming Language :: Python :: 3.10",
                   ],
      keywords='screencast screenshot capture audio sound video recorder kazam',
      url='https://github.com/henrywoo/kazam-screen-recorder',
      license='Apache-2.0',
      scripts=['bin/kazam'],
      packages=['kazam',
                'kazam.pulseaudio',
                'kazam.backend',
                'kazam.frontend',
                ],
      data_files=[('share/kazam/ui/', glob.glob('data/ui/*ui')),
                  ('share/kazam/sounds/', glob.glob('data/sounds/*ogg')),
                  ('share/icons/gnome/scalable/apps/', glob.glob('data/icons/scalable/*svg')),
                  ],
      cmdclass={'build': build_extra.build_extra,
                'build_i18n':  build_i18n.build_i18n,
                'build_help': build_help.build_help,
                'build_icons': build_icons.build_icons}
      )
