# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Timer object 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 May 2012   omd            Original Version
# *****************************************************************

import datetime

class Timer(object):
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def Start(self):
        self.start_time = datetime.datetime.now()

    def Stop(self):
        self.end_time = datetime.datetime.now()

    NUM_MICROS_PER_SECOND = 1000000.0
    def Elapsed(self):
        elapsed = self.end_time - self.start_time
        elapsed_sec = (elapsed.seconds + 
                float(elapsed.microseconds) / self.NUM_MICROS_PER_SECOND)
        return elapsed_sec

