#!/bin/bash

# Switch to the base virtualenv
source $WORKON_HOME/base/bin/activate

# Make the sparta virtualenv; this needs to be put in $WORKON_HOME for
# virtualenvwrapper functionality to work
virtualenv $WORKON_HOME/sparta

# Switch to the sparta virtualenv
source $WORKON_HOME/sparta/bin/activate

# Install everything in our requirements files into the sparta virtualenv
cd ../spar_python/
pip install -r requirements-0.txt
pip install -r requirements-1.txt

# Exit the virtualenv
deactivate
