#!/bin/bash

# Make the base virtualenv; this is used as a baseline environment to
# reduce conflicts with versions of distribute across environments and
# platforms. All future virtualenvs should be made from within the boostrap
# virtualenv (i.e., 'source $WORKON_HOME/base/bin/activate' followed by 
# 'virtualenv $WORKON_HOME/VIRTUALENV_NAME).
virtualenv $WORKON_HOME/base

# Switch to the base virtualenv
source $WORKON_HOME/base/bin/activate

# Install the latest stable version of virtualenv to the base virtualenv;
# this instance of virtualenv should be used to create future virtualenv (it
# will automatically be in your path if you are inside the base
# virtualenv).
pip install virtualenv

# Exit the virtualenv
deactivate
