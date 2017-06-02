# This is the top level SConstruct file. Below it is one SConscript file per
# langauge directory. You can build everything by building from this directory
# or you can go into any subdirectory and, using "scons -u", build just that
# directory. You can also, of course, specify specific targets regardless of the
# current directory.
#
# See the BUILD.README for details.

import scons_common as common

# Specify default targets - what gets built when you run "scons"
# without a target. Need this Default line or else it will always 
# build everything. We do not want it to build Install unless we say
# to. The arguments to Default are the directories to build
Default(['cpp','java','spar_python'])

SConscript(['cpp/SConscript', 'java/SConscript', 'spar_python/SConscript'],
        exports = 'common')

common.GenericTestBuilder.create_all_targets()

# make "distclean" a default target for scons -c
env = common.env
if (GetOption("clean")):
    env.Default("distclean")

# clean up files
env.Clean("distclean", "config.log") # config.log: scons artifact
env.Clean("distclean", common.Glob("*.pyc", dirsonly=False, recurse=True)) # .pyc files
env.Clean("distclean", "bin") #./bin and files contained within
env.Clean("distclean", "java/classes") # java class directory
env.Clean("distclean", common.Glob("debug", dirsonly=True, recurse=True)) # cpp build directories
env.Clean("distclean", common.Glob("opt", dirsonly=True, recurse=True)) # cpp build directories
env.Clean("distclean", "./spar_python/common/distributions/build") # cython generated
env.Clean("distclean", "./spar_python/common/distributions/text_generator.c") # cython generated
env.Clean("distclean", common.Glob("nosetests.xml", dirsonly=False, recurse=True)) # python unit tests
