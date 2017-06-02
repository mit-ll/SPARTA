[Back to top-level README](../README.md)

SPARTA Developer Guidelines
===============================================================================

Unit Testing
===============================================================================
The following unit testing frameworks are used:
- C++: Boost Test Library
- Java: JUnit
- Python: nosetests

Coding Style Conventions
===============================================================================
The following coding standards are used:
- C++: http://google-styleguide.googlecode.com/svn/trunk/cppguide.xml. 
    - In addition we have some rules about which libraries and C++11 features may be used. See below for details.
- Java: http://www.oracle.com/technetwork/java/javase/documentation/codeconvtoc-136057.html
    - This is enforced by automatically invoking the checkstyle library during the build process to alert the developer of any non-compliant code.
- Python: https://www.python.org/dev/peps/pep-0008/PEP-8
    - No automatic style checking has been incorporated, though ``pep8`` should be easy enough to install and run.

Library Usage
===============================================================================
In general, try to minimize the use of external libraries, particularly those that are subject to frequent changes as these can cause build failures.

If a library provides useful functionality that would be difficult to reproduce it is definitely worth considering using it. However, make sure the library isn't under heavy development and that its installation requirements are minimal.

C++ Libraries C++11
===============================================================================
Boost is an excellent source for libraries but not all Boost libraries are stable. Many are under heavy development, so the next `apt-get update` may break the build. In general, try to follow these rules:
- Most Boost TR1 libraries are now part of the C++11 standard library (written in late 2012), sometimes with slight modifications. Use the new standard libs instead (note that older code makes heavy use of Boost TR1 but it will be slowly migrated.)
- We use boost::program_options. Try not to use other Boost libs unless you can verify that they are not part of the C++11 standard and they are very stable (e.g. not being heavily developed).

C++11 has some great new features (written in late 2012) but not all compilers support them yet. The current rule is to avoid any features not supported by the latest MSVC and those that haven't been supported by g++ for at least a year. That means the following features are allowed (as of October 2012) - all others should be
  avoided:
- decltype and auto
- lambdas (though keep them short - if longer than 4 lines or so write a real function)
- nullptr
- r-value references and std::move
- delegating constructors
- range based loops
- static assert

Having New Binaries Be Installed to bin/
===============================================================================
To have a C++ or Python program installed in `bin/` via SCons, look at the invocations of `Install` and `LinkInstall` in `cpp/test-harness/ta1/SConscript` and `spar_python/SConscript` for examples, and add additional lines as needed.

If you need to change the name of the install directory, update the definition of `INSTALL_DIRECTORY` in `scons_common.py`. 


Adding New Unit Tests
===============================================================================

Adding unit tests to be run from the main `SConstruct` file requires you to use the unit test running framework defined in `scons-common.py`. See that file and the usage in `cpp/SConstruct` for details. The system is fairly flexible and should make it easy to mix and match unit test frameworks, different languages, etc.

For Python unit tests via nose, tests are defined by files containing a class that inherits from `unittest.TestCase` and contains methods named `test_yourtestname`.  If the method name is not prefixed with `test`, nose will not run it.  This allow you to enable/disable tests and write methods that are called by tests but should not
be executed as tests themselves.

Rough example of a Python test case:

```
import unittest
class MyTest(unittest.TestCase):
  def _helper_func(param1, param2):
    # Do stuff for other methods
    # Nose will not directly call me

  def test_check_something(self):
    """
    Test1 description printed by nose
    """
    # Nose will run this method as a test

  def test_check_somthing_else(self):
    """
    Test2 description printed by nose
    """
    # Nose will run this method as a test, too
```

[Back to top-level README](../README.md)
