# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        An example configuration file. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Jan 2013   omd            Original Version
# *****************************************************************

# Variables for site-specific values like ip addresses and host names
SPARMINI01 = '172.25.87.96'
SPARMINI02 = '172.25.87.48'
SPARMINI03 = '172.25.87.53'
SPARMINI04 = '172.25.87.200'
SPARMINI05 = '172.25.87.184'
local = 'localhost'

# Stuff that's common to all components
component = Component()
component.executable = 'script.sh'
component.base_dir = '/home/odain/testing'
# Use recursive_files_dict to get a list of all the files in dir1 (relative to
# the location of this configuration file) and have them put in base_dir
# (becuase I'm using '.' as a relative path so it'll be relative to base_dir).
component.files = util.recursive_files_dict('dir1', '.')
# Also copy the main executable
component.files['script.sh'] = 'script.sh'

# Use a nested loop to run two copies of the script.sh executable on every host.
# The 1st loop sets an argument that will be passed to the script (either '1' or
# '2'). The 2nd sets the host for the component.
for arg in xrange(1, 3):
    for h in (SPARMINI01, SPARMINI02, SPARMINI03, SPARMINI04, SPARMINI05):
        # start all the components with arg == 1 before any of the components
        # with arg == 2
        component.start_index = arg
        component.host = h
        component.name = 'script-%s-%s' % (arg, h)
        component.args = [str(arg), 'hello']
        component.args.extend(["--apple", extra_options.apple])
        component.args.extend(["--bread", extra_options.bread])
        component.args.extend(["--chese", extra_options.cheese])

        component.wait = False
        if arg == 2:
            # The 2nd command runs from a temporary directory that will be
            # created by remote_runner.
            component.base_dir = None
        config.add_component(component)

# Then add a component for things that will run locally.
component.name = 'local-script'
component.host = local
component.base_dir = '/tmp'
component.args = ['run', 'locally']

# Local components can't have anything in their files attribute. It is assumed
# that all files are already where they need to be on the local machine.
component.files = {}
config.add_component(component)
