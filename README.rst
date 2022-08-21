|image0|
--------

|Documentation Status| |CodeCov| |Github release| |lic|


Kazam is a simple screen recording program that will capture the content of your screen and record a video file that can be played by any video player that supports VP8/WebM video format. Optionally you can record sound from any sound input device that is supported and visible by PulseAudio.

Installation
------------

Make sure you have `distutils-extra` installed. You can run command like the below to install it:

.. code:: bash

  sudo apt-get install python3-distutils-extra

.. code:: bash

   /usr/bin/python3 -m pip install kazam

Screenshot
------------

.. figure:: https://github.com/henrywoo/kazam-screen-recorder/blob/tmp/img/Kazam_001.png?raw=true
   :alt: Kazam GUI Screenshot


.. figure:: https://github.com/henrywoo/kazam-screen-recorder/blob/tmp/img/Kazam_002.png?raw=true
   :alt: Kazam Preferences Screenshot



Running Kazam
---------------

From Source Code
~~~~~~~~~~~~~~~~~~~~~~


If you want to run Kazam from the source tree, there are a few limitations that you have to take into account. Every icon has to be taken from currently installed icon theme. Toolbars will not show any icons and you will not see Unity AppIndicator.

To run Kazam simply execute te following commands in the source tree:

```shell script
$ cd bin
$ ./kazam
```


From Command Line
~~~~~~~~~~~~~~~~~~~~~~

Add ~/.local/bin into you PATH, and run `kazam` in your terminal should work.


From GUI
~~~~~~~~~~~~~~~~~~~~~~
If you already have Kazam installed then Kazam icons will be displayed properly.



----

.. |image0| image:: https://raw.githubusercontent.com/henrywoo/kazam-screen-recorder/master/kazam.png
.. |Documentation Status| image:: https://readthedocs.org/projects/hiq/badge/?version=latest
   :target: https://hiq.readthedocs.io/en/latest/?badge=latest
.. |CodeCov| image:: https://codecov.io/gh/uber/athenadriver/branch/master/graph/badge.svg
   :target: https://hiq.readthedocs.io/en/latest/index.html
.. |Github release| image:: https://img.shields.io/badge/release-v1.5.6-red
   :target: https://github.com/uber/athenadriver/releases
.. |lic| image:: https://img.shields.io/badge/License-Apache--2.0-red
   :target: https://github.com/uber/athenadriver/blob/master/LICENSE
