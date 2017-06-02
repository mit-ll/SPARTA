#!/bin/bash

# Helper function to find the location of virtualenvwrapper (we don't use this
# right now, but keeping this here for future reference.
function find_virtualenvwrapper {
   # no consistent way to find 'virtualenvwrapper.sh', so try various methods
   # is it directly available in the path?
   virtualenvwrapper_path=$(which virtualenvwrapper.sh)
   if [ $? -eq 0 ]; then
      echo $virtualenvwrapper_path
      exit
   fi
   # nope; how about something that looks like it in our path?
   # http://stackoverflow.com/questions/948008/linux-command-to-list-all-available-commands-and-aliases
   virtualenvwrapper_cmd=$(compgen -ac | grep -i 'virtualenvwrapper\.sh' | sort | uniq | head -1)
   if [ -n "$virtualenvwrapper_cmd" ]; then
      virtualenvwrapper_path=$(which $virtualenvwrapper_cmd)
      if [ $? -eq 0 ]; then
         echo $virtualenvwrapper_path
         exit
      fi
   fi
   # still not; Debubuntu puts it in /etc/bash_completion.d
   virtualenvwrapper_path='/etc/bash_completion.d/virtualenvwrapper'
   if [ -e "$virtualenvwrapper_path" ]; then
      echo $virtualenvwrapper_path
      exit
   fi
   # any other methods to find virtualenvwrapper can be added here
   echo "unable to find virtualenvwrapper.sh or anything that looks like it"
   exit 1
}

# This needs to be in a user's .bashrc or somehow in their bash startup
# sequence; temporarily done here to get the initial sparta virtualenv defined
export WORKON_HOME=~/.virtualenvs

./base-virtualenv-setup.sh
./sparta-virtualenv-setup.sh
