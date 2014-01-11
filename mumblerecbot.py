# -*- coding: utf-8 -*-

import time
from threading import Thread

from constants import *

import pymumble
from pymumble.constants import *

import webvtt

class MumbleRecBot:
    """
    stay connected on a mumble server.  When USER_COUNT are connected, start to record.  Stop when the
    number of users goes below.
    Create webvtt files with chapters, timestamps and speakers captions
    understand a number of commands sent through the mumble chat system
    """
    def __init__(self):
        from os import getpid

        pid = str(getpid())
        file(PIDFILE,'w').write("%s\n" % pid)  # store the process id

        self.recording = False  # recording ongoing"
        self.audio_file = None  # output audio_file
        self.chapters = None  # chapters webvtt object
        self.current_chapter = None  # insige a chapter (after a /gamestart, before a /gamestop)
        self.last_chapter_time = 0
        self.captions = None  # webvtt object for speakers captions
        
        self.cursor_time = None  # time for which the audio is treated
        
        self.force_start = False
        self.force_stop = False
        self.force_newfile = False
        self.exit = False
        
        self.users = dict()  # store some local informations about the users session
        
        # Create the mumble instance and assign callbals
        self.mumble = pymumble.Mumble(HOST, PORT, USER, PASSWORD, debug=DEBUG)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERCREATED, self.user_created)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERUPDATED, self.user_modified)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_USERREMOVED, self.user_removed)
        self.mumble.callbacks.set_callback(PYMUMBLE_CLBK_TEXTMESSAGERECEIVED, self.message_received)
    
        self.mumble.start()  # start the mumble thread
        self.mumble.is_ready()  # wait for the end of the connection process
        self.mumble.channels.find_by_name(CHANNEL).move_in()  # move to the configured channel
        self.mumble.users.myself.mute()  # mute the user (just to make clear he don't speak)
    
        self.loop()

    def user_created(self, user):
        """A user is connected on the server.  Create the specific structure with the local informations"""
        if user["session"] not in self.users:
            self.users[user["session"]] = dict()
            self.set_user_stereo(user["session"])
            if "name" in user and user["name"] != USER:
                if self.captions is not None:
                    self.captions.add_cue("<c.system>User {user} connected".format(user=user["name"]), duration=2)
                if self.chapters is not None:
                    self.chapters.add_cue("<c.system>{user} connected".format(user=user["name"]), region="timestamp", duration=0)
        
        if "name" in user:
            self.users[user["session"]]["name"] = user["name"]
            
        if "channel_id" in user:
            self.users[user["session"]]["channel_id"] = user["channel_id"]
            self.set_user_stereo(user["session"], user["channel_id"])

        self.test_for_users()
            
    def set_user_stereo(self, session, channel=None):
        if channel is not None and self.mumble.channels[channel]["name"] in STEREO_CHANNELS:
            self.users[session]["stereo"] = STEREO_CHANNELS[self.mumble.channels[channel]["name"]]["stereo"]
            self.users[session]["region"] = STEREO_CHANNELS[self.mumble.channels[channel]["name"]]["region"]
        else:
            self.users[session]["stereo"] = (1, 1)
            self.users[session]["region"] = None
            
    def user_modified(self, user, actions):
        """A modification was sent by the server about a connected user"""
        if "channel_id" in actions:
            if "channel_id" not in self.users[user["session"]] or self.users[user["session"]]["channel_id"] != user["channel_id"]:
                self.set_user_stereo(user["session"], user["channel_id"])
                if self.captions is not None and "name" in self.users[user["session"]]:
                    self.captions.add_cue("<c.system>User {user} moved to channel {channel}".format(user=self.users[user["session"]]["name"], channel=self.mumble.channels[user["channel_id"]]["name"]), duration=2)
                self.users[user["session"]]["channel_id"] = user["channel_id"]
            
        if "self_mute" in actions:
            if "self_mute" not in self.users[user["session"]] or self.users[user["session"]]["self_mute"] != user["self_mute"]:
                if self.captions is not None and "name" in self.users[user["session"]]:
                    if user["self_mute"]:
                        self.captions.add_cue("<c.system>User {user} muted himself".format(user=self.users[user["session"]]["name"]), duration=2)
                    else:
                        self.captions.add_cue("<c.system>User {user} unmuted himself".format(user=self.users[user["session"]]["name"]), duration=2)
                self.users[user["session"]]["self_mute"] = user["self_mute"]
            
        self.test_for_users()
            
    def user_removed(self, user, *args):
        """a user has disconnected"""
        if "name" in self.users[user["session"]]:
            if self.captions is not None:
                self.captions.add_cue("<c.system>User {user} disconnected".format(user=self.users[user["session"]]["name"]), duration=2)
            if self.chapters is not None:
                self.chapters.add_cue("<c.system>{user} disconnected".format(user=user["name"]), region="timestamp", duration=0)
        del self.users[user["session"]]
        self.test_for_users()
    
    def test_for_users(self):
        """check the number of connected users to start/stop the recording"""
        if self.mumble.users.count() > USER_COUNT:
            self.recording = True
        else:
            self.recording = False
    
    def message_received(self, message):
        """receive a text message from the server"""
        from re import match
        
        global USER_COUNT
        
#TODO: check if message is sent only to me
        if message == "/start":  # force the recording
            self.force_start = True
            self.force_stop = False
            self.mumble.users.myself.comment("Recording forced." + COMMENT_SUFFIX)
        elif message == "/stop":  # prevent the recording
            self.force_start = False
            self.force_stop = True
            self.mumble.users.myself.comment("Recording blocked." + COMMENT_SUFFIX)
        elif message == "/auto":  # go in auto mode
            self.force_start = False
            self.force_stop = False
            self.mumble.users.myself.comment("Auto mode (starting with %i users)." % USER_COUNT + COMMENT_SUFFIX)
        elif match("^/auto=\d+$", message):  # go in auto mode and change the connected users threshold
            USER_COUNT=int(message.split("=")[1])
            self.force_start = False
            self.force_stop = False
            self.mumble.users.myself.comment("Auto mode (starting with %i users)." % USER_COUNT + COMMENT_SUFFIX)
        elif message == "/newfile":  # stop the current audio file and start a new one
            self.force_newfile = True
            self.mumble.users.myself.comment("Auto mode (starting with %i users)." % USER_COUNT + COMMENT_SUFFIX)
        elif message == "/exit":  # Stop the application
            self.exit = True
        elif message == "/gamestart":  # signal a game start to be recorded in the chapter webvtt file
            if self.chapters is not None and time.time()-self.last_chapter_time > CHAPTER_MIN_INTERVAL:
                self.last_chapter_time = time.time()
                if self.current_chapter is not None:
                    self.current_chapter.end()
                usernames = list()
                for user in self.mumble.users.values():
                    if user["name"] != USER:
                        usernames.append(user["name"])
                title = "{time} ({users})".format(time=time.ctime(), users=",".join(usernames))
                self.current_chapter = self.chapters.add_cue(title)
        elif message == "/gamestop":  # signal a game stop to be recorded in the chapter webvtt file
            self.last_chapter_time = 0
            if self.chapters is not None:
                if self.current_chapter is not None:
                    self.current_chapter.end()
        elif match("^/timestamp=.*$", message):  # create a timestamp in the chapters webvtt file
            text = message.split("=", 1)[1]
            text = text[:50]
            if self.chapters is not None:
                self.chapters.add_cue(text, region="timestamp", duration=0)
   
    def loop(self):
        """Master loop""" 
        import os.path
        import audioop
        
        silent = "\x00" * STEREO_CHUNK_SIZE
        
        self.mumble.users.myself.comment("Auto mode (starting with %i users)." % USER_COUNT + COMMENT_SUFFIX)
        self.mumble.users.myself.texture(self.load_bitmap(STOP_BITMAP))
        
        while self.mumble.is_alive() and not self.exit:
            if  ( ( self.recording and not self.force_stop ) or self.force_start ) and not self.force_newfile: 
                if not self.audio_file:
                    # Start recording
                    self.mumble.set_receive_sound(True)  # ask the pymumble library to handle incoming audio 
                    self.mumble.users.myself.recording()  # signal the others I'm recording (to be fair)
                    self.mumble.users.myself.texture(self.load_bitmap(START_BITMAP))  # Change the recorder avatar
                    self.cursor_time = time.time() - BUFFER  # time of the start of the recording
                    #create the files
                    audio_file_name = os.path.join(SAVEDIR, "mumble-%s" % time.strftime("%Y%m%d-%H%M%S"))
                    self.audio_file = AudioFile(audio_file_name)
                    self.chapters = webvtt.WebVtt(audio_file_name + "-chapters.vtt")
                    self.captions = webvtt.WebVtt(
                                        audio_file_name + "-captions.vtt",
                                        regions=[
                                                "Region: id=left width=50% regionanchor=0%,100% viewportanchor=0%,100%",
                                                "Region: id=right width=50% regionanchor=100%,100% viewportanchor=100%,100%",
                                                ]
                                        )
                    usernames = list()
                    for user in self.mumble.users.values():
                        if user["name"] != USER:
                            usernames.append(user["name"])
                    title = "<c.system>Recording started with users {users}".format(users=",".join(usernames))
                    self.captions.add_cue(title, duration=2)

                if self.cursor_time < time.time() - BUFFER:  # it's time to check audio
                    base_sound = None
                    
                    for user in self.mumble.users.values():  # check the audio queue of each users
                        session = user["session"]
                        while ( user.sound.is_sound() and
                                user.sound.first_sound().time < self.cursor_time):
                            user.sound.get_sound(FLOAT_RESOLUTION)  # forget about too old sounds
                        
                        if user.sound.is_sound():
                            if "caption" not in self.users[session]:
                                self.users[session]["caption"] = self.captions.add_cue("<v {user}>{user}".format(user=user["name"]))
                                
                            if ( user.sound.first_sound().time >= self.cursor_time and
                               user.sound.first_sound().time < self.cursor_time + FLOAT_RESOLUTION ):
                                # available sound is to be treated now and not later
                                sound = user.sound.get_sound(FLOAT_RESOLUTION)
                                    
    
                                if sound.target == 0:  # take care of the stereo feature
                                    stereo_pcm = audioop.tostereo(sound.pcm, 2, *self.users[session]["stereo"])
                                    self.users[session]["caption"].set_region(self.users[session]["region"])
                                else:
                                    stereo_pcm = audioop.tostereo(sound.pcm, 2, 1, 1)
                                if base_sound == None:
                                    base_sound = stereo_pcm 
                                else:
                                    #base_sound = audioop.add(base_sound, sound.pcm, 2)
                                    base_sound = self.add_sound(base_sound, stereo_pcm)
                        else:
                            if "caption" in self.users[session]:
                                self.users[session]["caption"].end()
                                del self.users[session]["caption"]

                    if base_sound:
                         self.audio_file.write(base_sound)
                    else:
                        self.audio_file.write(silent)
                        
                    self.cursor_time += FLOAT_RESOLUTION
                else:
                    time.sleep(FLOAT_RESOLUTION)
                                
            else:
                if self.audio_file:
                    # finish recording
                    self.mumble.users.myself.unrecording()
                    self.mumble.users.myself.texture(self.load_bitmap(STOP_BITMAP))
                    self.mumble.set_receive_sound(False)
                    self.cursor_time = None
                    self.audio_file.close() 
                    self.audio_file = None
                    if self.current_chapter is not None:
                        self.current_chapter.end()
                    self.current_chapter = None
                    self.chapters = None
                    for user in self.users.values():
                        if "caption" in user:
                            user["caption"].end()
                            del user["caption"]
                    self.captions = None    
            
                self.force_newfile = False   
                time.sleep(0.5)

                    
    def add_sound(self, s1, s2):
        """add 2 stereo PCM audio streams"""
        import struct
        from sound_add import sound_add
        
        if len(s1) != len(s2):
            raise Exception("both sound must have same length")
        
        return sound_add(s1, s2)
        
    def load_bitmap(self, file):
        """read the bitmap info to update the avatar"""
        bitmap = open(file, "rb")
        
        result = ""
        
        rec = bitmap.read(4096)
        while rec != "":
            result += rec
            rec = bitmap.read(4096)
        
        bitmap.close()
        return result
    

class AudioFile():
    """
    Manage the audio saving, through a pipe or in a WAV file
    """
    def __init__(self, name):
        from subprocess import Popen, PIPE
        import wave
        
        self.name = name
        self.type = None
        self.file_obj = None
        
        try:
            final_name = ENCODER % name
            proc = Popen(final_name.split(" "), shell=False, bufsize=-1, stdin=PIPE)
            self.file_obj = proc.stdin
            self.type = "pipe"
        except:
            self.name += ".wav"
            self.file_obj = wave.open(self.name, "wb")
            self.file_obj.setparams((2, 2, BITRATE, 0, 'NONE', 'not compressed'))
            self.type = "wav"
        
    def write(self, data):
        if self.type == "pipe":
            self.file_obj.write(data)
        else:
            self.file_obj.writeframes(data)
    
    def close(self):
        self.file_obj.close()

def printHex(string):
    mystr=''
    for i in range(len(string)):
        mystr += "%02x" % ord(string[i])

    return mystr


if __name__ == "__main__":
    recbot = MumbleRecBot()
             
        
