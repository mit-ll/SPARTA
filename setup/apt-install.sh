#!/bin/bash

# Install packages
sudo apt-get -y update
sudo apt-get -y upgrade
# Basic utilities
sudo apt-get -y install screen scons moreutils openssl
# C++ build libraries
sudo apt-get -y install g++ libboost-all-dev libevent-dev libssl-dev
sudo apt-get -y install libncurses5-dev libmariadbclient-dev libsqlite3-dev
# Parsing utilities
sudo apt-get -y install lemon flex bison
# Java packages
sudo apt-get -y install openjdk-6-jdk openjdk-6-jre 
# Database packages (mariadb-server is installed via a separate script)
sudo apt-get -y install mariadb-client sqlite3 
# Python package management utilities
sudo apt-get -y install python-pip python-virtualenv virtualenvwrapper 
# LaTeX utilities
sudo apt-get -y install texlive texlive-latex-extra 
# numpy and matplotlib dependencies
sudo apt-get -y install libfreetype6-dev libpng-dev libblas-dev liblapack-dev gfortran libxft-dev
# Performance monitoring utilities
sudo apt-get -y install collectl tcpdump
# Documentation packages
sudo apt-get -y install python-epydoc doxygen
