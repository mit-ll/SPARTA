[Back to top-level README](../../README.md)

remote_runner.py
================================================================================
`remote_runner` is a Python script for copying files and starting commands on a number of different hosts.

For advanced usage, call `remote_runner.py` with the `--help` command. The basic usage pattern is described here.

When run, `remote_runner`, by default, does the following:
- Reads the configuration file provided by the `-c` argument
- Creates an SSH connection to all hosts
- Kills the screen sessions from any prior remote_runner executions
- Calls the muddler if one was passed via the `-m` option
- Starts screen on all hosts in "zombie mode"
- Copies all files needed by all components to their destinations
- Starts all components in order according to their `start_index`

These steps are explained in more detail below.

Some of these steps can be altered via command line flags. See `--help` for details.

Requirements
================================================================================
Following the [Installation Instructions](../INSTALL.md) is easiest, but in general, `remote_runner` requires:

1. A relatively modern version of Python
2. The Python paramiko module. On Ubuntu this can be installed via `apt-get install python-paramiko`
3. `openssl` must be installed on all remote hosts. This is used to compute SHA1 hashes of files to determine if they've changed and need to be re-copied. On Ubuntu this can be installed via `apt-get install openssl`

Configuration Files
================================================================================
`remote_runner` reads the configuration file passed to it's `-c` argument. That file describes a set of "components". Each components consists of an executable, the arguments to that executable, the host on which the executable is to run, and the files the executable needs.

Note that if the path to the executable is relative (does not start with a `/` character"), then it is assumed to be relative to `base_dir` and change accordingly. If the path is absolute then the path is not altered. That means that running commands that are normally in `$PATH`, like "ls" or "grep", requires that the executable attribute be provided with an absolute path to the executable.

Note that the arguments to the executable, provided in the args attribute, are provided as a list. They are double-quoted before being sent to the shell so that arguments with spaces are OK. However, additional quoting may confuse the shell or the executable.

Note that configuration files are Python programs and users can take full advantage of this. For example, it is possible to use loops, globs, etc. to make configuration easier.

For example, a relatively simple configuration file might look like:

```
main = Component()
main.name = 'My main'

# If base_dir is not set a temporary directory on the host will be created for
# this component.
main.base_dir = '/home/me/subdir'

# The path to the executable on the remote host relative to base_dir. If this
# path starts with a '/' it's an absolute path on the remote host.
main.executable = 'executable'
# The arguments that executable should be called with
main.args = ['-a', 'something', '-b', 'more']

# Move all files in /path/to/d and it's subdirectories to base_dir
main.files = util.recursive_files_dict('/path/to/d', '.')

# Also move all files in /path/to/other/d to /abs/dest
main.files.update(util.recursive_files_dict('/path/to/other/d', '/abs/dest')

# The executable isn't automatically transferred. If it needs to be transferred
main.files['path/to/executable'] = 'executable'

# This is where we want this component to be run.
main.host = '192.168.2.20'

# This component should be started first
main.start_index = 1

config.add_component(main)

# other is just like main. Since it has the same start_index it can be started
# at the same time as main
other = main
other.name = 'My other'
other.host = '192.168.2.50'

config.add_component(other)

local = other
local.host = localhost
local.args = ['I run locally',]

# This has a larger start_index than main or other and so will be started after
# they are started.
local.start_index = 5
local.name = 'Local thing'

# Local components can't ask to have any files transferred!
local.files = {}

config.add_component(local)
```

This configuration file sets up 3 components. One will run on 192.168.2.20, one will run on the host 192.168.2.50, and one will run on the localhost. Note that 'localhost' means the host where remote_runner is run. In all cases the executable that will be run is `path/to/executable`. Since this path is relative it is assumed to be relative to the location of the configuration file. All *local* file paths that don't start with a `/` are relative to the configuration file. Similarly, all remote file paths that don't start with a `/` are relative to the components `base_dir` value.

The files attribute is a Python dictionary mapping local file locations to their desired remote locations. The `util` module, which is exported to the config file, provides the `recursive_files_dict` method to make it easy to add entire directory structures to the set of files that need to be transferred.

A complete, working example that starts 2 executables on several different hosts and uses some Python loops to configure several similar components can be found in the `example` directory.

SSH Authentication
================================================================================

remote_runner uses `paramiko`'s very flexible SSH authentication mechanisms. It will try the following authentication mechanisms in order:

1) If `ssh-agent` is running it will be contacted to get a key.
2) any `id_rsa` or `id_dsa` key in `~/.ssh` will be used. If this key is encrypted the password provided to the `--pass` argument will be used to decrypt it.
3) The username and password provided via the `--user` and `--pass` arguments will be used.

Screen Sessions
================================================================================

`remote_runner` starts all commands in `screen` sessions. That has several advantages:

1) You can `ssh` to any remote host and attach to the `screen` session to monitor an executable while it's running.
2) It provides a convenient way to keep executables running after the `ssh` session terminats.
3) Since all executables on a host are run in different windows in the same `screen` session it is (usually) possible to easily kill all of them by simply quitting that `screen` session.

The screen session that `remote_runner` creates is put in "zombie" mode. This way executables that complete (either by finishing sucessfully or by crashing) remain visible in the `screen` session. To close a window containining the output of a
completed executable hit the `q` key. The `screen` copy-mode works in zombie screens so it is possible to scroll back, copy and paste, save the session output, etc.

When `remote_runner` starts it kills any previous `screen` session on all hosts with the same name to ensure that each run is isolated unless the --no-kill option is provided.

Muddlers
================================================================================

`remote_runner` is a general-purpose tool for running any set of executables on any hosts. For the SPAR program we very often want to use a test harness to control certain components. To enable this use case while keeping `remote_runner` general purpose we use "muddlers". A muddler gets passed a configuration and can modify it.

For example, the TA3 muddler reads a configuration file and changes any components whose name starts with `publisher` so they run under the control of the test harness (it changes the executable to be the test harness and passes the original executable as a command line argument to the harness).

Arg Parsers
================================================================================

For added flexibility, `remote_runner` allows one to specify arbitrary command-line options that will get passed to the config files and muddlers. If the `--extra-args` option is used for this purpose, an `--arg-parser` must also be specified. This is a Python file with a `parse_args()` method defined that returns an `optparse` `Namespace`.

``*KNOWN ISSUE*`` If an extra argument begins with a parameter that is also used by `remote_runner` itself, strange things happen. There is a StackOverflow discussion here: https://stackoverflow.com/questions/16174992 and a python bug report here: http://bugs.python.org/issue9334

File Copies
================================================================================

As noted above, all files listed in a component's `files` attribute are copied to the remote host and their file permissions are preserved. Since copying files is slow and many applications require large files, `remote_runner` tries to determine if the target file and the source file are the same before copying.

If the target file does not exist, or has a different size the source file is copied to the destination. If both files exist and have the same size `remote_runner` computes the SHA1 hash of both files (computing the remote hash on the remote host) and only transfers the files if these differ. Since the SHA1 of a 250MB file can be computed in less than a second but it would take many minutes to transfer the file this can be a big savings. However, if all files are small the checks can slow things down. In that case, pass the `--always-copy` option.

Also note that `remote_runner` does not check file permissions when checking if files are the same. Thus if the only thing that has changed about a file are it's permissions the `--always-copy` option will be necessary.

Starting Executables
================================================================================

All the components in a configuration file are sorted by `start_index` and started in that order. Components that have the same `start_index` can be started in parallel, but `remote_runner` will wait until the start command has completed for one index before starting any components with a larger index.

[Back to top-level README](../../README.md)
