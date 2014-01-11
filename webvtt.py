# -*- coding: utf-8 -*-

import codecs
import collections
import time

class WebVtt:
    """
    Create a webvtt formatted file
    """
    def __init__(self, filename, regions=None):
        self.file = codecs.open(filename, "w", "utf_8_sig")
        self.file.write(u"WEBVTT\n")
        if regions is not None:
            if isinstance(regions, list):
                for region in regions:
                    self.file.write(region + '\n')
            else:
                sef.file.write(regions + '\n')
        self.file.write(u"\n")

        self.pending = collections.deque()
        self.zero_time = time.time()
        
    def add_cue(self, text, id=None, region=None, duration=None):
        cue = Cue(self, text, id=id, region=region, duration=duration)
        self.pending.append(cue)
        if duration is not None:
            self.check_end()
        return(cue)
    
    def check_end(self):
        while len(self.pending) > 0 and self.pending[0].stop is not None:
            cue = self.pending.popleft()
            self.file.write(cue.get_string())
    
    def __del__(self):
        for cue in self.pending:
            cue.end(False)
        self.check_end()
        self.file.close()
        

class Cue:
    def __init__(self, parent, text, duration=None, id=None, region=None):
        self.parent = parent
        self.text = text
        self.id = id
        self.region = region
        self.start = time.time() - self.parent.zero_time
        if duration is None:
            self.stop = None
        else:
            self.stop = self.start + duration
        
    def end(self, check=True):
        self.stop = time.time() - self.parent.zero_time
        if check:
            self.parent.check_end()
            
    def set_region(self, region):
        self.region = region
            
    def get_string(self):
        if self.stop is None:
            return(u"")
        
        ret = u""
        if self.id:
            ret += id + u"\n"

        ret += self.convert_time(self.start) + u" --> " + self.convert_time(self.stop)
        if self.region:
            ret += u" region:{region} ".format(region=self.region)
        ret += u"\n"
        
        ret += self.text + u"\n\n"
        
        return(ret)
        
    def convert_time(self, seconds):
        micro = int((seconds - int(seconds)) * 1000)
        seconds = int(seconds)
        
        minutes = int(seconds/60)
        seconds -= minutes*60
        
        hours = int(minutes/60)
        minutes -= hours*60
        
        return("{hours:02}:{minutes:02}:{seconds:02}.{micro:03}".format(hours=hours, minutes=minutes, seconds=seconds, micro=micro))
    
