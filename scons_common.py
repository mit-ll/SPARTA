# Infrastructure that mainly allows SCons build rules to execute unit tests.
# Also sets up generic functionality for SCons builds (e.g., running optimized
# builds, configuring the number of cores to use when building, etc.).

from SCons.Script import *
import tempfile
import sys
import os.path
import multiprocessing
import atexit
import os
import fnmatch

# This sets up the environment. All the SConstruct files should use this.
env = DefaultEnvironment()

# Add INSTALL_DIRECTORY to the env
# Note that the '#' before 'bin' means the top-level SConstruct directory
# and '#bin' is equivalent to: os.path.join(env.GetLaunchDir(),'bin')
env['INSTALL_DIRECTORY'] = '#bin'
env.Alias('install','$INSTALL_DIRECTORY')

# Command line flags here determine debug and release build info. This info is
# propagated down to the language-specific builders which then set compiler
# flags and such as appropriate.
AddOption('--opt', dest='opt', action='store_true', default=False,
   help='Optimized build')
AddOption('--test_to_err', dest='test_to_err', action='store_true',
        default=False, help = 'Send unit test output to stderr '
        'instead of in a temporary file')
# Command line flag that requires a certain number of successful runs for each
# unit test before it is considered a success. Defaults to 1.
AddOption('--test_reps', dest='test_reps', type='int',
        default=1, help = 'Number of times to repeat each unit test')
if GetOption('test_reps') > 1:
  print ('NOTE: all unit tests must pass %d repetitions to be considered '
       + 'successful.') % GetOption('test_reps')

# If the user has not specified -j or --jobs we will figure out the number of
# available CPUs and run that many parallel jobs. To disable the user can
# specify -j to limit the cpu count.
num_cores = multiprocessing.cpu_count()
env.SetOption('num_jobs', num_cores)
if env.GetOption('num_jobs') == num_cores:
    print 'Running with -j %s. Specify -j or --jobs to override.' % num_cores

def _linkFunc(dest, source, env):
    """Link a file from source to dest.
    source is the file to link. It will have a path from the top level 
    scons directory (the directory where this file lives). 
    dest is the file to create. The path for dest is relative from the top 
    level scons directory. If you are installing into bin/ then dest will 
    always start with bin/.  
    For example: in the case of generate_data.py, 
    dest= bin/generate_data.py and 
    source=spar_python/data_generation/generate_data.py 
    and both are relative from the top level directory (where this file lives)"""
    if os.path.isdir(source):
        raise SCons.Errors.UserError("Source must be a file, not a directory")
    elif os.path.isdir(dest):
        raise \
          SCons.Errors.UserError("Destination must be a file, not a directory")
    else:
        # Cannot use os.path.exists here (does not work for broken symlinks);
        # cannot use os.path.lexists either (not present in older Pythons)
        try:
            os.unlink(dest)
        except OSError:
            pass
        if os.path.isabs(source) or os.path.isabs(dest):
            raise SCons.Errors.UserError( \
              "Source and Destination should not be relative paths")
        else:
            # If both paths are relative to top-level directory, figure out how
            # to get from dest to the top level, then make a relative symlink:
            updirs = len(os.path.normpath(dest).split(os.path.sep)) - 1
            uppath = os.path.sep.join([os.path.pardir] * updirs)
            os.symlink(os.path.join(uppath, source), dest)
    return 0

def LinkInstall(env, target, source):
    """Like the standard Install builder, but using symlinks if available."""
    if hasattr(os, 'symlink'):
        return env.Install(target, source=source, INSTALL=_linkFunc)
    else:
        return env.Install(target, source=source)

def LinkInstallAs(env, target, source):
    """Like the standard InstallAs builder, but using symlinks if available."""
    if hasattr(os, 'symlink'):
        return env.InstallAs(target, source=source, INSTALL=_linkFunc)
    else:
        return env.InstallAs(target, source=source)

env.AddMethod(LinkInstall, 'LinkInstall')
env.AddMethod(LinkInstallAs, 'LinkInstallAs')

class UnitTestRunner(object):
    """There is one object of this class for each unit test that we are going to
    run. The class variables keep track of the total number of tests and the
    total number that have passed and failed. When all tests have run a summary
    is printed out."""
    num_tests = 0
    num_pass = 0
    num_fail = 0
    def __init__(self, test_fun, test_target, kwargs):
        """This will run a unit test by calling test_fun with test_target
        and a log file path as arguments. test_fun must be a function that
        returns True if the test passes and False otherwise. It should write any
        test output to the passed log file so users can look at the test
        output.
        
        Arguments:
            test_fun: a function that accepts a target, a log file, and any
                optional kwargs as input, runs a test and returns true iff the
                test passes.
            test_target: the target that should be passed to test_fun
            kwargs: An optional dict that will be passed to test_fun
                as **kwargs
        """
        self.__test_target = test_target
        self.__test_fun = test_fun
        self.__kwargs = kwargs
        UnitTestRunner.num_tests += 1

    def run(self, target = None, source = None, env = None):
        """This runs the test using the arguments passed to __init__. The
        arguments the method takes are meaningless - they are only here because
        this is wrapped up as a scons Action and Action functions must accept
        these arguments."""
        if GetOption('test_reps') > 1:
          # Run the test for GetOptions('test_reps') repetitions
          self.__run_repeated_test(target, source, env)
        else:
          # Run the test once, and update the class' pass/fail counters.
          if self.__run_test_once(target, source, env) == 0:
            UnitTestRunner.num_pass += 1
          else:
            UnitTestRunner.num_fail += 1

    def __run_test_once(self, target, source, env, rep_count = None):
        """This runs a test once; if provided with a rep_count value, it
        will print out the repetition count for the test being run (otherwise,
        it is assumed that the test is not being repeated)."""
        if GetOption('test_to_err'):
            log_file = sys.stderr
        else:
            log_file = tempfile.NamedTemporaryFile(delete=False)
        running_str = 'Test: %s. ' % self.__test_target
        if GetOption('test_reps') > 1:
          running_str += 'Repetition: %d. ' % rep_count
        running_str += 'Output: %s. Result: ' % log_file.name

        ret = self.__test_fun(self.__test_target, log_file, **self.__kwargs)

        print '%s [%s]\n' % (running_str, ('PASSED' if ret == 0 else 'FAILED'))
        sys.stdout.flush()
        return ret

    def __run_repeated_test(self, target, source, env):
        """This runs a test GetOptions('test_reps') times, and tracks how many
        iterations pass and how many fail. Prints how many repetitions have
        failed if any failures occur. Increments the class' num_pass counter if
        every reptition passes; otherwise, increments the class' num_fail
        counter."""
        num_pass_reps = 0  
        num_fail_reps = 0
        # Execute the test test_reps times
        for i in range(GetOption('test_reps')):
          if self.__run_test_once(target, source, env, i) == 0:
            num_pass_reps += 1
          else:
            num_fail_reps += 1
        if num_pass_reps == GetOption('test_reps'):
          UnitTestRunner.num_pass += 1
        else:
          print '%s FAILED %d out of %d repetitions.' % \
                (self.__test_target, num_fail_reps, GetOption('test_reps'))
          UnitTestRunner.num_fail += 1

    @classmethod
    def print_summary(cls):
        """Prints a summary of all tests run."""
        if cls.num_fail == 0:
            print '\n\n%d Tests PASSED%s. None Failed. SUCCESS!\n' % \
                (cls.num_pass, 
                (' with %d Repetitions' % GetOption('test_reps') \
                 if GetOption('test_reps') > 1 else ''))
        else:
            print '\n\n%d of %d Tests FAILED%s.' % \
                (cls.num_fail, cls.num_pass + cls.num_fail,
                (' with %d Repetitions' % GetOption('test_reps') \
                 if GetOption('test_reps') > 1 else ''))

# Always print a summary if any unit tests were run at the very end.
@atexit.register
def print_unit_test_summary():
    if UnitTestRunner.num_pass > 0 or UnitTestRunner.num_fail > 0:
        UnitTestRunner.print_summary()

class GenericTestBuilder(object):
    """scons Builder objects are kind of a pain and don't quite work right. This
    class does not, in fact, create a builder but it makes it *seem* as if it
    does. To use construct an object of this class passing the builder_name and
    the other options as specified in __init__. This will attach a method with
    the builder name to the environment and it can be used like a builder that
    runs unit tests.
    
    Using this "builder" creates 3 aliases for every test added via a call to
    __add_test:
        
        1) The alias passed to __add_test can be used to run just that one test.
        2) The alis passed to __init__ can be used to run all tests constructed
           via this object. 
        3) The alias "test" can be used to run all tests added via any
           GenericTestBuilder.
    
    See the BUILD.README for more info."""
    # Every time you construct a new instance of this class it adds itself to
    # this list. Then when you call create_all_targets it uses this list to
    # create all the aliases.
    all_builders = []
    TEST_PROG_PREFIX = 'test_prg_'

    def __init__(self, alias_name, builder_name, test_fun):
        """Creates a builder like method so that a call to env.builder_name(foo)
        will create a test target alias to run the unit test foo. foo is assumed
        to be a target and the unit test depends on that target first being
        built.

        Arguments:
            alias_name: all unit tests added to this builder can be run via this
                alias. For example, the java/SConscript file uses an instances
                of this class with alias_name == "java_test" so that all java
                tests can be run via that alias.
            builder_name: The "builder" function added to the environment will
                have this name.
            test_fun: The test function that will called to actually run the
                unit tests.
        """
        self.tests_alias = alias_name
        self.all_tests = []
        self.builder_name = builder_name
        self.test_fun = test_fun
        GenericTestBuilder.all_builders.append(self)
        self.setup_builder()

    def __add_test(self, env, alias, target, deps, **kwargs):
        """The "builder" method calls this to schedule a test to run and
        properly set up the dependencies.
        
        Arguments:
            env: This method gets attached to the environment so it appears to
                be a builder. The environment is thus automatically passed
                though it is not used.
            alias: The name of the resulting target. For example, if you pass
                "foo" here "scons foo" would cause this test to be run.
            target: The target that gets passed to the test function supplied to
                the constructor. For C++ tests this is the path to the test
                executable, for Java tests its the name of the test class, etc.
            deps: An iterable of targets that must be built before this test can
                be run. If there is only a single dependancy you can pass it
                alone rather than wrap it in a list or tuple. You can also pass
                None if there are no dependancies (e.g. Python tests)
            kwargs: Any additional keyword arguments that should be passed to
                the test function.
        """
        # Create a UnitTestRunner object to run the test for this target.
        test_runner = UnitTestRunner(self.test_fun, target, kwargs)
        # To make this work with scons you must first wrap up the function
        # in an Action, then wrap that function in an Alias since Actions
        # can't have dependencies or be set to run. Then we specify that the
        # Alias has a depencency with target so we make sure the unit test
        # gets built before its run. Finally we specify that our alias
        # should always run otherwise scons will note that none of its
        # depenancies have changed so it won't run it.
        test_act = Action(test_runner.run, 'Running ' + str(target))
        test_alias = env.Alias(alias, deps, test_act)
        env.AlwaysBuild(test_alias)
        self.all_tests.append(test_alias)

    def setup_builder(self):
        """Adds the __add_test method to the environment with the builder_name
        specified in the constructor. For all intentes an purposes this creates
        a builder with the specified name."""
        env.AddMethod(self.__add_test, self.builder_name)


    @classmethod
    def create_all_targets(cls):
        """This should be called after all SConscript files have been sourced.
        This goes through all of the individual GenericTestBuilder objects and
        creates their target aliases and the global test alias."""
        all_tests = []
        for bldr in cls.all_builders:
            alias = Alias(bldr.tests_alias, bldr.all_tests)
            AlwaysBuild(alias)
            all_tests.append(alias)
        alias = Alias('test', all_tests)
        AlwaysBuild(alias)

# from http://www.scons.org/wiki/BuildDirGlob
def Glob( pattern, dir = '.', dirsonly = True, recurse=False):
    files = []
    for file in os.listdir( Dir(dir).srcnode().abspath ):
        if fnmatch.fnmatch(file, pattern) :
            if ((dirsonly is False) or (os.path.isdir(os.path.join(dir, file)))): 
	        files.append( os.path.join( dir, file ) )
        if (recurse and os.path.isdir(os.path.join(dir, file))):
            files.extend(Glob(pattern, os.path.join(dir, file), dirsonly, recurse))
    return files
    
