# This script "generates" the C/C++ generator extension module to be used by
# python for the fingerprint generation.  It depends on scons to be run first to
# generate all the object modules below from the repository.

from distutils.core import setup,Extension

setup(name='generator',
version='1.0',
ext_modules=[Extension('generator', ['generator.cpp',
'fingerprint-generator.cpp'],
libraries=['stdc++'],
include_dirs=['/usr/include/python2.7/'])])
