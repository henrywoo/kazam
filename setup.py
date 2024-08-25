#!/usr/bin/env python3

from ctypes.wintypes import LONG
import sys
if sys.version_info < (3, 2):
    sys.exit('Kazam requires Python 3.2 or newer')

import os

here = os.path.dirname(os.path.realpath(__file__))

from distutils.core import setup
from DistUtilsExtra.command import build_extra, build_i18n, build_help, build_icons
import hiq

import re
import glob

try:
    line = open("kazam/version.py").readline()
    VERSION = re.search(r"VERSION = '(.*)'", line).group(1)
except:
    VERSION = "1.0.0"


LONG_DESC=hiq.read_file(f"{here}/README.rst", by_line=False)

def read_file(filename: str):
    try:
        lines = []
        with open(filename) as file:
            lines = file.readlines()
            lines = [line.rstrip() for line in lines if not line.startswith("#")]
        return lines
    except:
        return []

setup(name='kazam',
      version=VERSION,
      description='A screencasting program created with design in mind.',
      author='Henry Fuheng Wu, David Klasinc',
      author_email='wufuheng@gmail.com',
      long_description=LONG_DESC,
      install_requires=read_file(f"{here}/requirements.txt"),
      classifiers=['Development Status :: 5 - Production/Stable',
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
                  "Programming Language :: Python :: 3.11",
                  "Programming Language :: Python :: 3.12",
                   ],
      keywords='screencast screenshot capture audio sound video recorder kazam',
      url='https://github.com/henrywoo/kazam',
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
