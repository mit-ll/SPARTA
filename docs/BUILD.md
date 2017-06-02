[Back to top-level README](../README.md)

SPARTA Build Process
===============================================================================

The SPAR code is built using [SCons](www.scons.org). This document assumes a basic understanding of that system. Please go through the introduction section of the manual before reading further.

Our build is organized as follows:

- The top-level directory contains no real code. All code is in a language specific   directory. cpp for C++ code, spar_python for Python code (not called just Python since this is part of the module path and that would be confusing), and java for java code.
- Under each language specific directory there are directories for source files.
- In the top-level directory there is a SConstruct file that does some common functionality by importing scons-common.py. Aside from this, it just runs the SConscript files in each of the language-specific directories.
- The SConscript files in each language directory define language specific functionality and run the SConscript files in their respective subdirectories.

Basic SCons Usage
===============================================================================

**`NOTE`** All the following commands, unless otherwise noted, should be run from the top-level directory.

For a debug build (i.e., unoptimized but with plenty of helpful verbose debug messages on stdout) of all products in all languages:

```
scons
```

To install executables and scripts into the `bin/` directory, run:
```
scons install
```

To create an optimized build (the meaning of optimized is language specific, but generally means no stdout printouts or assertion checks):
```
scons --opt
```

You can also add the ``--opt`` flag to other commands to run the optimized version of that command, such as:
```
scons --opt test
```

To run all unit tests for all languages, run the following. Note that you will want to have previously run ``workon sparta`` (if you followed the installation instructions) to be in the ``sparta`` Python virtualenv and have all the proper Python dependencies loaded.
```
scons test
```

To run a specific unit test, you can specify the pseudo-target for that test. For C++ unit tests, this is generally of the form ``run_<unit_test_name>``. For example, to run the tests for ``cpp/common/util.cc`` contained in ``cpp/common/util_test.cc``:
```
scons run_util_test
```

Note that the naming conventions for unit tests are language specific. Refer to the language directories for details.

Some languages provide other command line options specifically for that language. For example, to run the C++ unit tests under Valgrind run:
```
scons --valgrind cpp_test
```

To build just a subdirectory go to that subdirectory and run ``scons -u``. For example, to build just the C++ code:
```
cd cpp
scons -u
```

Similarly, each language defines its own target for all that language's unit tests. So to run all the C++ tests on an optimized build you could do either this:
```
cd cpp
scons -u --opt cpp_test
```

or this, from the top-level directory:
```
scons --opt cpp_test
```

To get a list of the command line options, including those specific to our build system, run:
```
scons --help
```

Running Python Unit Tests
===============================================================================

Python unit tests are run with nose, a Python unit test framework. When unit tests are executed via ``scons test``, SCons simply calls nose to find and execute the Python unit tests. Again, remember to be in the ``sparta`` virtualenv by running ``workon sparta`` before running any Python unit tests.

You can exeure Python unit tests directly using the `nosetests` script.  This script will recursivley search the directories from where it is executed for unit tests and execute all that it finds.  To run a specific test, you can pass the file name to nose with `nosetests path/to/test/my_file_test.py1 and all tests within the file will be executed.

When debugging tests, you may want to see stdout printed by the test.  Nose usually swallows this output and generates it's own formatted output for each test that fails.  You'll never see any output for a test that passes.  To see output from your test, run nosetests with the `-s` flag: `nosetests -s path/to/test/my_print_file_test.py`

Generating Documentation
===============================================================================
To generate documentation from source, run `./makesourcedocs.sh` in the `docs/doc-gen` directory.  This will run Doxygen on the C++ code, javadoc on the Java code, and epydoc  on the Python code.  The output from these commands will be in the `cppdocs/`, `javadoc/`, and `pydocs/` directories within the `docs/doc-gen` folder.


**`KNOWN ISSUE`** This generates a lot of errors and warnings since our code commenting is 100% standard compliant. There also appear to be import issues for the Python code in particular that need to be resolved.

[Back to top-level README](../README.md)
