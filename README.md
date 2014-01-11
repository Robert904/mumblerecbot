Mumble audio recorder
=====================

Description
-----------
* mumblerecbot.py is a mumble client application that connect to a server, waiting for enough users to be connected and then start to record.
  It also create Webvtt files to indicate events and speakers.
  to join the different streams when more than one user speak at the same time, it use a smal cython script for performance reasons
  I make it public, but it is a tailor made solution for my situation, and must be seen only as an example for using the
  pymumble module which is meant to be versatile 

* basicplayer is an exemple of a pymumble audio emitter.  It takes as parameter a wav file encoded in 16bit mono 48000Hz

Requirements/installation
-------------------------
You need the pymumble <https://github.com/Robert904/pymumble> module available (on your path or in a subdirectory)

It seems to work fine on Python 2.6 and 2.7.
I have used it on both Windows and Linux

for the mumblerecbotfast module, Cython is needed, at least 0.14, and you need a worinkg compiler environment (I use MINGW for windows)
there is a basic Makefile that should work inside the directory


License
-------
Copyright Robert Hendrickx <rober@percu.be> - 2014

pymumble is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


Included opus and celt libraries sources have their own licensing