# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Python script to configure an NTP server and run it 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  30 Apr 2012   omd            Original Version
# *****************************************************************

import subprocess
import os
import os.path

NTP_DIR = '/tmp/ntp'
replace_dict = {
        '~~NTP-DIR~~': NTP_DIR,
        '~~NTP-SUBNET~~': '192.168.100.0',
        '~~NTP-SUBNET-MASK~~': '255.255.255.0'
        }

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

config_template = file(os.path.join(THIS_DIR, 'ntp.server.conf'), 'r')

try:
    os.makedirs(NTP_DIR)
except OSError, e:
    # Error 17 indicates the directory already exists which is fine.
    if e.errno != 17:
        raise e

config_file = file(os.path.join(NTP_DIR, 'ntp.server.conf'), 'w+')

for line in config_template:
    for search, replace in replace_dict.iteritems():
        line = line.replace(search, replace)
    config_file.write(line)

config_file.close()
config_template.close()

# We may eventually need to specify the -I option here to bind ntp the
# backchannel network's interface
#
# The -N option causes ntpd to run at the highest possible priority so that we
# the time is as accurate as possible.
subprocess.Popen(['/usr/sbin/ntpd', '-c',
    os.path.join(NTP_DIR, 'ntp.server.conf'),
    '-l', os.path.join(NTP_DIR, 'ntp.log'), '-N'])
