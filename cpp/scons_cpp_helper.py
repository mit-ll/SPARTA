import SCons.Script as scons
import sys
import os.path
import subprocess
import copy
import collections
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import scons_common as common

class DependancyRegistry(object):
    """Class for maintaining build dependancies."""
    def __init__(self):
        # self.__deps[x] is the set() of all things upon which x directly
        # depends.
        self.__deps = {}

    def add(self, node, *args):
        """Inidcate that node depends on everything in args."""
        if not node in self.__deps:
            self.__deps[node] = set()
        self.__deps[node] = self.__deps[node].union(args)

    def __get_incoming_for_subgraph(self, start_nodes, set_dd):
        """Given start_nodes, the 1st set of dependancies to a program, populate
        set_dd, a collections.defaultdict(set) instance, so that set_dd[x] is
        the set of things that depend upon x starting from start_nodes."""
        for n in start_nodes:
            if n in self.__deps:
                self.__get_incoming_for_subgraph(self.__deps[n], set_dd)
                for d in self.__deps[n]:
                    set_dd[d].add(n)

    def get_ordered_deps(self, *nodes):
        """Uses a modified version of Kahn's topological sort algorithm to
        return a correctly ordered list of dependancies starting with the
        libraries listed in nodes. Pseudo-library (those the begin with '@' --
        see the README) will be correctly resolved but will not be in the
        returned list."""
        # The set of starting nodes is just nodes, but we need to know how many
        # things depend on each node for this particular sub-graph (the subgraph
        # where we start with the nodes passed).
        depends_on = collections.defaultdict(set)
        self.__get_incoming_for_subgraph(nodes, depends_on)

        # As the algorithm progress this is always the list of nodes that have
        # no unprocess things depending on them. They can thus be inserted into
        # the resulting list and expanded.
        to_process = [n for n in nodes if not n in depends_on]
        result = []
        while len(to_process) > 0:
            n = to_process.pop()
            # Don't insert "pseduo-libs" into the set of returned dependancies.
            if not isinstance(n, str) or not n.startswith('@'):
                result.append(n)
            if n in self.__deps:
                for nd in self.__deps[n]:
                    depends_on[nd].remove(n)
                    if len(depends_on[nd]) == 0:
                        del(depends_on[nd])
                        to_process.append(nd)

        if len(depends_on) != 0:
            print ('Error. The dependancy graph starting with '
                   '%s contains cycles!' % map(str, nodes))
            sys.exit(1)
        return result

# If passed unit tests run via SconsCPPHelper.__RunSingleUnitTest are run under
# valgrind.
scons.AddOption('--valgrind', dest='valgrind', action='store_true',
        default=False, help = 'When given in combination with '
        '--test this runs unit tests under valgrind.')
# Compiles a version for profiling with gprof
scons.AddOption('--gprof', dest='gprof', action='store_true',
        default=False, help='Compile with gprof support. If '
        'given running the program will produce a gmon.out file '
        'on exit which can be used with gprof')

class SconsCPPHelper(object):
    """Main class for building libraries, programs, and unit tests. See the
    README for details."""
    def __init__(self):
        self.env = common.env
        self.__deps = DependancyRegistry()

        self.env['CCFLAGS'].extend(['-Wall'])
        # The no-deprecated-declarations flag is because C++11 deprecates some
        # standard libary class and methods (most notably auto_ptr). Until we
        # convert all our code we'll need this flag.
        self.env.Append(CPPPATH = ['#/cpp',])
        self.env['CCFLAGS'].extend(['-std=c++0x',
                       '-Wno-deprecated-declarations'])
        if scons.GetOption('opt'):
          # Note: -msse2 only works on x86_64. If we ever try to run on other
          # architectures we'll have to disable this.
          self.env['CCFLAGS'].extend(
                  ['-O2', '-DNDEBUG', '-ftree-vectorize', '-msse2',])
          self.build_dir = 'opt'
        else:
          self.env['CCFLAGS'].extend(['-g'])
          self.build_dir = 'debug'

        if scons.GetOption('gprof'):
            self.env['CCFLAGS'].extend(['-pg'])
            self.env['LINKFLAGS'].extend(['-pg'])
            # output is the concatenation of the normal location (debug or opt)
            # with -profile so the opt-profile directory contains an optimized
            # build with profiling and the debug-profile dir contains debug
            # build with profiling.
            self.build_dir = self.build_dir + '-profile'

        self.__AutoConf()

        common.GenericTestBuilder(
                'cpp_test', 'BoostTest', self.__RunSingleUnitTest)

        # Scons has trouble keeping track of the current directory when you use
        # VariantDir (the way we put the output of a build in a debug, opt, etc.
        # subdirectory). If using variant dirs simple things like calling
        # os.getcwd() return different results on different runs depending on
        # wheather the variant dir has been created yet or not. Even worse,
        # scons built-ins like File() and Dir() return *incorrect* results in
        # nested dirs and in inconsistent ways dues to race conditions so that
        # one call might return cpp/common/knot-impl/debug (correct), while the
        # next might return cpp/commong/debug/knot-impl/debug (note the extra
        # "debug" in the path name). One thing that *does* seem to consistently
        # work is getting the srcnode() of the sconscript file *before* calling
        # the sconscript file. We therefore use that trick to maintain our own
        # current source and working directory in cur_src_dir and cur_var_dir.
        # As long as you use the SConscript() method of this class to call
        # subsidiary SConstruct files, those files can rely on these variables
        # to give accurate paths.

        # The '#' character means the root directory of the entire scons build.
        # This is the cpp subdirectory of that.
        self.cur_src_dir = os.path.join(str(scons.Dir('#')), 'cpp')
        self.cur_var_dir = os.path.join(self.cur_src_dir, self.build_dir)
            
    def __getattr__(self, attr):
        """Scons provides lots of builder methods and we don't need to override
        all of them but we would like to make them all available to users. If we
        haven't explicitly overridden it and our environment (self.env) has the
        method we'll expose it like it's a method of this class. That way our
        environment configuration is inherited and we can always override the
        functionliaty in the future without needing to change any of our build
        files."""
        if hasattr(self.env, attr):
            return getattr(self.env, attr)
        else:
            raise AttributeError('"%s" is not a valid builder method.' % attr)

    def __AutoConf(self):
        """This does the equivalent of GNU autoconf - it tries to make the build
        platform independent.

        Note that I've only done the minimum amount necessary to get things to
        compile on Ubuntu and CentOS (and specific versions of those to boot).
        If you want to compile on anything else you will likely need to update
        this."""
        context = scons.Configure(self.env)
        self.__lib_names = {}
        # Check for boost libraries with various names
        boost_libs = ['boost_thread', 'boost_regex',
                      'boost_unit_test_framework']
        for lib in boost_libs:
            # It appears that as of 2010 or so, the -mt suffix on Boost
            # libraries to signify multithreading support was dropped for many
            # libraries as multithreading was integrated into a single library.
            # No longer looking for -mt versions of libraries, but noting this
            # in case it ever causes problems.
            if context.CheckLib(lib, language = 'C++'):
                self.__lib_names[lib] = lib
            else:
                print 'Error. Library %s not available' % lib
                scons.Exit(1)

        # If neither version of the mariadb lib is available add the CentOS path
        # to it to LIBPATH
        maria_r_check = context.CheckLib('mariadbclient_r', language = 'C++')
        maria_check = context.CheckLib('mariadbclient', language = 'C++')
        if (not maria_r_check and maria_check):
            self.env.Append(LIBPATH = '/usr/lib64/mysql')

        # Use the re-entrant ("_r") version more than one is available (Ubuntu
        # only has the re-entrant version and doesn't use the _r suffix)
        if maria_r_check:
            self.__lib_names['mariadbclient'] = 'mariadbclient_r'
        elif maria_check: 
            self.__lib_names['mariadbclient'] = 'mariadbclient'
        else:
            print "Error. Libarary libmariadbclient not available"
            scons.Exit(1)
        self.env = context.Finish()

    def __get_platform_libs(self, libs):
        result = []
        for lib in libs:
            if str(lib).startswith('#'):
                result.append(self.__get_platform_lib(lib[1:]))
            else:
                result.append(lib)
        return result

    def __get_platform_lib(self, lib):
        """Some libraries can have different names/paths on different systems.
        This takes a "canonical" library name and returns the platform-specific
        name. For example, boost_thread is call boost_thread on Ubuntu but
        boost_thread-mt on CentOS."""
        if lib not in self.__lib_names:
            print "Error! Library %s not found." % lib
            sys.exit(1)
        else:
            return self.__lib_names[lib]

    def Library(self, name, sources, libs = [], *args, **kwargs):
        """Build a library from the given sources. name is the name to give the
        library. libs is the set of libraries this library depends on. *args and
        **kwargs are passed directly to the scons Library rule."""
        new_lib = self.env.Library(target = name, source = sources,
                *args, **kwargs)
        self.__deps.add('@' + name, new_lib[0])
        self.__deps.add(new_lib[0], *libs)

    def Program(self, name, sources, libs = [], *args, **kwargs):
        """Build a program from the given sources. name is the name to give the
        library. libs is the set of libraries this program depends on. *args and
        **kwargs are passed directly to the scons Library rule."""
        all_libs = self.__deps.get_ordered_deps(*libs)
        # For some libraries we use a "canonical" name. This maps that to the
        # platoform-specific name.
        all_libs = self.__get_platform_libs(all_libs)
        program = self.env.Program(name, sources,
                LIBS = all_libs, *args, **kwargs)
        return program

    def Lemon(self, src):
        """Run lemon to compile a .y file into a .cc and a .h file. The genrated
        files have the same base name as src but end with .cc or .h.

        Args:
            src: the name of the source file. Assumed to be in the same
            directory as the SConscript file from which builder.Lemon() was
            called.

        Returns:
            scons node object for the .cc file generated. This can then be used
            as input to other build rules. This does not return the .h file as
            that is typically not used in build rules. The single file is
            returned in a list as that is scons convention.

        The output files will be put into a variant subdirectory (e.g. ./debug
        for a debug build). We could put the files into the same directory as
        the .y file but that clutters the directory. More importantly, lemon has
        some command line flags that allows us to build optimized parsers. We're
        not using the currently, but in the future the generated source for a
        release build might be different from the source generate for a debug
        build.
        """

        assert os.path.basename(src) == src
        # We need a 3-step build process here:
        # 1) Lemon always puts the generated .c and .h file in the same
        #    directory as the source so we first copy the source file into the
        #    variant dir.
        # 2) Run lemon to generate the the .c and .h files
        # 3) rename the .c file to a .cc file so scons realizes it's C++ and
        #    builds it with g++ instead of gcc.
        # However, we don't want to do any of these things unless the .y file
        # has changed. So we create a single command with a single dependancy.
        # Scons will then run our function only if necessary.

        src_path = os.path.join(self.cur_src_dir, src)
        var_path = os.path.join(self.cur_var_dir, src)
        variant_dir = os.path.join(os.path.dirname(src_path), self.build_dir)

        # The name of the source file without the ".y"
        src_base_filename = os.path.splitext(src)[0]
        # The path to the generated .c file
        generated_c_path = os.path.join(self.cur_var_dir,
                src_base_filename + '.c')
        # The path to the generated .h file
        generated_h_path = os.path.join(self.cur_var_dir,
                src_base_filename + '.h')
        # Where we should copy the .c file to get a .cc file.
        desired_cc_path = os.path.join(self.cur_var_dir,
                src_base_filename + '.cc')
        # Copy self.cur_var_dir, which may refer to a different string by the
        # time run_lemon gets invoked by scons, into a new varible so it gets
        # copy into the run_lemon closure
        var_dir = self.cur_var_dir
        # Closure that will be run to generate the .cc and .h files if
        # necessary
        def run_lemon(target, source, env):
            """The targets, source, and environment are passed by scons but we
            can ignore them as we don't need them."""
            # Copy the .y file into the variant dir
            shutil.copy(src_path, var_dir)
            ret = scons.Execute('lemon ' + var_path)
            if ret != 0:
                scons.Exit(1)
            # now rename the .c file to a .cc file
            shutil.move(generated_c_path, desired_cc_path)

        # This command indicates that the .cc and .h files are generated from
        # the .y file by running run_lemon. Scons will then call that function
        # if and only if the .y file has changed.
        res = scons.Command(
                [desired_cc_path, generated_h_path], src_path, run_lemon)
        return [desired_cc_path,]

    def Flex(self, flex_file):
        """Runs flex to convert a .l file into .cpp and .h files. This has the
        same issues as Lemon when it comes to variant dirs and such - see the
        docs on that method."""
        assert os.path.basename(flex_file) == flex_file
        src_file = os.path.join(self.cur_src_dir, flex_file)
        # Make a copy of the src and variant dirs so they get copied into the
        # closure below
        src_dir = self.cur_src_dir
        var_dir = self.cur_var_dir

        # name of the flex file without the ".l"
        flex_file_base = os.path.splitext(flex_file)[0]
        generated_cpp_file = os.path.join(self.cur_var_dir,
                flex_file_base + '.yy.cpp')
        generated_h_file = os.path.join(self.cur_var_dir,
                flex_file_base + '.yy.h')
        # Flex puts its output in it's current working directory. Thus we need
        # to change dirs before running it and change back after. We don't want
        # to do that unless we actually need to do the build so we use the
        # closure/command trick that's used in the Lemon rule above. Thus the
        # build process is:
        # 1) cd to variant_dir
        # 2) Run flex over the .l file in the source dir
        # 3) cd back to where we started
        def run_flex(target, source, env):
            start_dir = os.getcwd()
            os.chdir(var_dir)
            res = scons.Execute('flex  ' + src_file,
                    chdir = var_dir)
            if res != 0:
                scons.Exit(1)
            os.chdir(start_dir)
        scons.Command(
                [generated_cpp_file, generated_h_file], src_file, run_flex)
        # Here we return a File node that points to the generated file as if it
        # were generated in the non-variant dir. This is because scons knows
        # it's a build output and so automatically appends the variant dir.
        return [generated_cpp_file,]

    def SConscript(self, sconscript_path, exports = ''):
        """Run the build rules specified in the subdirectory specified by
        sconscript_path. Export the variables listed in exports to that
        SConscript file in addition to exporting builder."""

        builder = self
        exports += ' builder'
        src_sconscript_dir = os.path.abspath(os.path.dirname(
                str(scons.File(sconscript_path).srcnode())))
        var_sconscript_dir = os.path.join(src_sconscript_dir, self.build_dir)
        sconscript_filename = os.path.basename(sconscript_path)

        # See the comments on these instance variables in __init__.
        old_src_dir = self.cur_src_dir
        self.cur_src_dir = src_sconscript_dir
        old_var_dir = self.cur_var_dir
        self.cur_var_dir = var_sconscript_dir

        scons.VariantDir(var_sconscript_dir, src_sconscript_dir, duplicate = 0)
        scons.SConscript(os.path.join(var_sconscript_dir, sconscript_filename),
                exports)

        self.cur_src_dir = old_src_dir
        self.cur_var_dir = old_var_dir

    @staticmethod
    def __RunSingleUnitTest(test, log_file):
        """This is called by the GenericTestBuilder to run a single unit
        test."""
        test_str = test + ' --log_level=test_suite'
        if scons.GetOption('valgrind'):
            command_str = \
                    'valgrind --error-exitcode=1 --leak-check=yes ' + test_str
        else:
            command_str = test_str

        ret = subprocess.call(command_str, stdout=log_file,
                stderr=subprocess.STDOUT, shell=True)
        return ret

    def AddBoostTest(self, test_filename, libs = []):
        """Build a unit test from the file test_filename and register it with
        the unit test running framework."""
        libs = copy.copy(libs)
        libs.append('boost_unit_test_framework')
        #libs.append('boost_system')
        # The statics library supplies the Initialize() function that every
        # unittest should include (usually via test-init.h).
        libs.append('@statics')
        test = self.Program(os.path.splitext(test_filename)[0],
                test_filename, libs)
        self.env.BoostTest('run_' + str(test[0]),
                test[0].get_abspath(), test[0])

