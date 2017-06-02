The following explains a bit about using SConscript files to build C++ code with
our scons setup:

Dependency Handling
====

Scons isn't particularly good about handling C++ dependencies. In particular, if
you have a library, A, the depends on libraries B and C and you link A into your
binary that will not link B and C if you use standard scons functionality.
Instead, scons wants you to list A, B, and C as Dependencies of the program.
This means that if you add a dependency to a library you must update the build
rules for every binary that depends on it. Furthermore, the list of dependencies
passed to scons gets passed directly to the linker where the order matters.
Specifically, if A depends on B but you pass B to the linker before A the linker
will not see anything using the function in B so they will be stripped, then it
will process A and discover that it can't resolve its functions and linking will
fail.

To fix these issues all build files use the SconsCPPHelper class. SConscript
files are always passed an instance of the builder as the variable 'builder'.
You should use the Library, AddBoostTest, and Program methods of that class to
build things. The SconsCPPHelper will make sure dependencies are properly
handled for you.

Note that the builder uses "pseduo-libraries" for some things. This make it
easier to handle linking libraries from one directory to another. If you build
a library named 'foo' like:

builder.Library('foo', ['foo_impl.cc',], libs = ['A', 'B'])

you can refer to that library as '@foo' in any build file and it will resolve
to the full path to libfoo.a. Thus a program rule might be:

builder.Program('main', ['main.cc',], libs = ['@foo',])

Platform Independence
====

Our scons setup also handles libraries that might have different names or paths
on different platforms. Note that we've only added the platforms we've tried
compiling on. All bets are off on other platforms. To add new platforms or use
new libraries that may be platform dependent modify SconsCPPHelper::__AutoConf
as appropriate.

To reference a library in a build rule when that library may depend on the
platfrom pre-pend the library name with a #. Thus, for example, refer to the
mysqlclient library as '#mysqlclient'. SconsCPPHelper will take care of mapping
this to the platform-specific name and will, if necessary, add -L flags so the
library can be found by the linker.


Build Issues
====
`common/check_test.cpp` fails on occasion.
