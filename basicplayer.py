# -*- coding: utf-8 -*-

import wave
import time
import sys

import pymumble

from pymumble import pyopus

DEBUG = False

HOST = "localhost"
PORT = 64738
USER = "player"
PASSWORD = "player"

AUDIO_FILE = sys.argv[1]

# create the mumble instance
mumble = pymumble.Mumble(HOST, PORT, USER, PASSWORD, debug=DEBUG)

mumble.start()  # start the mumble thread
mumble.is_ready()  # wait for the connection
mumble.users.myself.unmute()  # by sure the user is not muted

audio=wave.open(AUDIO_FILE)

start = time.time()

frames = audio.readframes(480)
while frames:
    while mumble.sound_output.get_buffer_size() > 0.5:
        time.sleep(0.01)  # if mumble outgoing buffer is full enough, wait a bit
        
    mumble.sound_output.add_sound(frames)  # send a piece of audio to mumble
    
    frames = audio.readframes(480)

while mumble.sound_output.get_buffer_size() > 0:  # wait for the output buffer to empty
    time.sleep(0.01)  # wait for the mumble buffer's exhaustion before exiting

audio.close()
