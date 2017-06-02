# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD, NJH
#  Description:        Main method for the remote_runner script.
# *****************************************************************

"""
Runs a set of tasks on both remote and local hosts. Tasks are defined in
Components in a config file that is passed in via command line. See the README
for details on how to configure Components.

See remote_runner_test.py for an example of how to call remote_runner
methods from python.
"""

import argparse
import config_classes
import config_util
import logging
import os
import os.path
import ssh_manager
import subprocess
import sys
import operator
import time

LOGGER = logging.getLogger(__name__)

def canonicalize_paths(config, config_dir):
    """Go through all paths in the config object. If they're relative on the
    local machine make them relative to config_dir. If they're relative on the
    remote server make them relative to the components base_dir."""
    for component in config.all_remote_components():
        assert component.base_dir is not None
        if not os.path.isabs(component.executable):
            component.executable = \
                canonicalize_path(component.executable,
                                  component.base_dir)
        for src, dest in component.files.viewitems():
            update = False
            if not os.path.isabs(dest):
                update = True
                dest = canonicalize_path(dest, component.base_dir)

            if not os.path.isabs(src):
                update = True
                del(component.files[src])
                src = canonicalize_path(src, config_dir)
            if update:
                component.files[src] = dest

    for component in config.all_local_components():
        if not os.path.isabs(component.executable):
            component.executable = \
                canonicalize_path(component.executable, config_dir)
        if len(component.files) > 0:
            LOGGER.critical('Local component %s has non-empty files '
                    'attribute: %s', component.name, component.files)
            sys.exit(1)

def canonicalize_path(path, start):
    """Canonicalize path by prepending start to path."""
    assert not os.path.isabs(path)
    return os.path.abspath(os.path.join(start, path))

def kill_old_sessions(config, options, ssh_mgr):
    """For every host in the config send the "quit" command to any screen
    sessions named options.screen."""
    command = 'screen -S %s -X quit' % options.screen
    LOGGER.info('Stopping old screen sessions.')
    for host in config.all_hosts():
        if host == 'localhost':
            subprocess.call(command, shell = True)
        else:
            ssh_mgr.run_command(host, command)
    ssh_mgr.wait_for_empty_queues()
    LOGGER.info('All old screen sessions terminated.')

def start_screens(config, options, ssh_mgr):
    """Start a screen session on all hosts as per options."""
    command = 'screen -d -m -S %s' % options.screen
    command_zombie = None
    if not options.no_zombie:
        command_zombie = 'screen -S %s -X zombie q' % options.screen

    LOGGER.info('Starting screen sessions on all hosts.')
    for host in config.all_hosts():
        if host == 'localhost':
            subprocess.check_call(command, shell = True)
            if command_zombie is not None:
                subprocess.check_call(command_zombie, shell = True)
        else:
            ssh_mgr.run_command(host, command)
            if command_zombie is not None:
                ssh_mgr.run_command(host, command_zombie)
    LOGGER.info('Screens queued to start on all hosts.')

def assert_names_unique(components):
    '''Verifies that each component has a unique name
    
    Returns True on success, raises an AssertionError on failure'''
    names_list = [(c.name, c.host) for c in components]
    names_set = set(names_list) # removes duplicates
    assert len(names_list) == len(names_set), \
        "(host,name) pairs for remote runner components must be unique"
    return True

def run_commands_in_order(config, options, ssh_mgr):
    """Run all the commands indicated by the start_index."""
    components = [c for c in config.all_components()]
    assert len(components) > 0
    assert_names_unique(components)
    components.sort(key=operator.attrgetter('start_index', 'host'))

    # We can start all the command with the same index at the same time so we
    # keep track of the current index. When the index changes we wait for all
    # pending commands to complete.
    cur_idx = components[0].start_index
    LOGGER.info('Starting commands with index %s.', cur_idx)
    for component in components:
        if component.start_index != cur_idx:
            assert component.start_index > cur_idx
            LOGGER.info(
                    'Waiting for all command with index %s to start', cur_idx)
            ssh_mgr.wait_for_empty_queues()
            cur_idx = component.start_index
            LOGGER.info('Starting command with index %s', cur_idx)

        args_str = ' '.join(['"%s"' % x for x in component.args])
        today = time.strftime("%y%m%d") #YYMMDD
        timeofday = time.strftime("%H%M%S") #hhmmss
        # TODO fix capture of output for remote runner output; doesn't seem to
        # be working (creates the file but it is empty, at least on completely
        # local invocations)
        #filename = "rr_output_%s_%s_%s_%s.txt" % (component.host,
        #        component.name, today, timeofday)
        #if (options.remote_done_dir):
        #    filename = os.path.join(options.remote_done_dir, filename)
        #args_str += " >> %s 2>&1" % filename
        command = 'screen -S %s -X screen %s %s' % (
                options.screen, component.executable, args_str)
        if component.base_dir:
            # Set the default directory for the new window to component.base_dir
            # before spawning the command.
            command = 'screen -S %s -X chdir %s; %s' % \
                      (options.screen, component.base_dir, command)
        LOGGER.debug('Sending command [%s] to %s', command, component.host)
        if component.host == 'localhost':
            subprocess.call(command, shell = True)
        else:
            ssh_mgr.run_command(component.host, command)
        # Adding sleep to see if it helps with stability issues on local runs.
        # Seemed to have trouble consistently starting all screen sessions for
        # completely local runs; some screen sessions would never show up
        time.sleep(1)

def get_parser():
    parser = argparse.ArgumentParser('remote_runner command line options')
    parser.add_argument('-c', '--config', dest = 'config_file',
            required = True, help = 'Location of the configuration file')
    parser.add_argument('-u', '--user', dest = 'ssh_user', default = None,
            help = 'The username for all ssh connections. If not given '
            'defaults to the current user.')
    parser.add_argument('-p', '--pass', dest = 'ssh_pass', default = None,
            help = 'The password for all ssh connections or private keys in '
            'the .ssh directory.')
    parser.add_argument('-l', '--log-level', dest = 'log_level',
            choices = ('DEBUG', 'INFO', 'WARNING', 'ERROR'),
            default = 'INFO', help = 'Print logging information at '
            'this severity or above.')
    parser.add_argument('--screen', dest = 'screen', default = 'runner',
            help = 'The name given to the screen sessions (via the -S '
            'argument to screen) where all commands are run')
    parser.add_argument('--no-kill', dest = 'kill_first',
            action = 'store_false',
            help = 'By default, all screens on all hosts with the same name as '
            'the value passed to the --screen option are given the "quit" '
            'command. If this argument is given, prior screen sessions '
            'won\'t be terminated')
    parser.add_argument('-t', '--terminate', action='store_false',
                        help='Terminate all (non-wait) components upon completion '
                        'of all components that are being waited on')
    parser.add_argument('--always-copy', dest = 'always_copy',
            action = 'store_true',
            help = 'Normally, we check to see if a file has changed before '
            'copying it. This flag causes the file to be copied '
            'unconditionally')
    parser.add_argument('--no-zombie', dest = 'no_zombie',
            action = 'store_true', help = 'When a command finishes '
            'in a screen session, screen normally removes the corresponding '
            'window. By default, remote_runner puts screen in "zombie" mode so '
            'that such windows are not removed (they can be removed by hitting '
            'the "q" key from within the screen session). If this argument '
            'is given, the normal screen behavior is restored.')
    parser.add_argument('-m', '--muddler', dest = 'muddler', default = None,
            help = 'A muddler changes the configuration file components after '
            'it has been parsed and processed. The standard use for a muddler '
            'is to cause some components to be run by a test harness instead '
            'of on their own.')
    parser.add_argument('--extra-args', dest = 'extra_args', 
            default = None, help = 'A string specifying any other custom '
            'parameters that should be made available to the configuration '
            'file or muddler. Every configuration file and muddler is provided '
            'with the command line options provided to remote_runner. This '
            'allows additional arbitrary parameters to be defined for use in '
            'the configuration file or muddler. This string should be '
            'formatted like a typical command line string that the argparse '
            'module would understand (i.e. just like this help message '
            'instructs).') 
    parser.add_argument('-a', '--arg-parser', dest = 'arg_parser', 
            default = None, help = 'An arg parser is required ifs --extra-args '
            'is specified. This file is used to parse the items in '
            '--extra-args into an object that the config and muddler files '
            'can use to retrieve argument values.')
    parser.add_argument('--remote-done-dir', dest = 'remote_done_dir', 
            default = None, help = 'Location where status files will be '
            'placed to assess the completion of components on remote hosts. '
            'User must have permissions to this directory on all remote hosts.')
    return parser


def parse_args():
    """Parse and validate command line options for main method."""
    parser = get_parser()
    options = parser.parse_args()
    return options

def validate_args(options):
    # Validate command line options
    options.config_file = os.path.realpath(os.path.expanduser(\
        os.path.expandvars(options.config_file)))
    assert os.path.isfile(options.config_file), \
           'Could not find %s' % options.config_file
    if options.muddler:
      options.muddler = os.path.realpath(os.path.expanduser(\
          os.path.expandvars(options.muddler)))
      assert os.path.isfile(options.muddler), \
             'Could not find %s' % options.muddler
    if options.remote_done_dir:
      options.remote_done_dir = os.path.realpath(os.path.expanduser(\
          os.path.expandvars(options.remote_done_dir)))
      assert os.path.isdir(options.remote_done_dir), \
             'Could not find %s' % options.remote_done_dir
    if options.extra_args:
      assert options.arg_parser, ('--arg-parser option must be specified if '
                                  '--extra-args is used')
      options.arg_parser = os.path.realpath(os.path.expanduser(\
          os.path.expandvars(options.arg_parser)))
      assert os.path.isfile(options.arg_parser), \
             'Could not find %s' % options.arg_parser

def run(config, options, config_dir):
    for component in config.all_components():
        component.check_all_set()
    config.check_names_unique()

    ssh_mgr = ssh_manager.SSHManager(config, options)
    try:
        LOGGER.info('Starting SSH threads.')
        ssh_mgr.connect_all()
        if options.kill_first:
            kill_old_sessions(config, options, ssh_mgr)
        LOGGER.debug('Modifying any components that need to be waited for.')
        ssh_mgr.prepare_for_waits()
        LOGGER.debug('Ensuring base dirs are defined for every component.')
        ssh_mgr.set_base_dirs()
        # Now that we've got a base_dir for each component we can canoncialize
        # all the file paths to make everything easier.
        LOGGER.debug('Canonicalizing base dirs for every component.')
        canonicalize_paths(config, config_dir)
        LOGGER.debug('Starting screen sessions.')
        start_screens(config, options, ssh_mgr)
        LOGGER.info('Starting file transfers.')
        ssh_mgr.copy_all()
        LOGGER.info('Starting component execution.')
        run_commands_in_order(config, options, ssh_mgr)
        LOGGER.info('Waiting for components requiring wait to complete.')
        ssh_mgr.wait_for_commands()
        LOGGER.info('All components requiring wait complete.')
    finally:
        if options.terminate:
            ssh_mgr.killall(config) # kills all running components
        ssh_mgr.done()


def main():
    """Main method."""
    options = parse_args()

    # set logging based on log_level option
    log_level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR}
    logging.basicConfig(
            level = log_level_mapping[options.log_level],
            format = '%(levelname)s: %(message)s')

    validate_args(options)

    # If necessary, parse options.extra_args
    extra_options = None
    if options.extra_args:
      LOGGER.info('Parsing --extra-args with %s.', options.arg_parser)
      argparser_globals = {}
      execfile(options.arg_parser, argparser_globals)
      assert 'parse_args' in argparser_globals
      assert callable(argparser_globals['parse_args'])
      extra_options = argparser_globals['parse_args'](options.extra_args,
                                                      options.ssh_user)

    LOGGER.info('Loading %s.', options.config_file)
    config_globals = {
            # This is the config object the configuration file must use
            'config': config_classes.Config(),
            # This puts the Component class in the config file's namespace
            'Component': config_classes.Component,
            # This puts the config_util in the config file's namespace
            'util': config_util,
            # This puts the user's command line options in the config file's
            # namespace
            'options': options,
            # This puts the user's parsed extra_args in the config file's
            # namespace
            'extra_options': extra_options,
    }
    # Set the current dir to the one where the config file is so that all file
    # operations in the config file are relative to that file
    options.config_file = os.path.abspath(options.config_file)
    config_dir = os.path.dirname(options.config_file)
    old_pwd = os.getcwd()
    os.chdir(config_dir)
    execfile(options.config_file, config_globals)
    # Now change back to the original dir
    os.chdir(old_pwd)
    config = config_globals['config']

    if options.muddler is not None:
        LOGGER.info('Calling muddler from %s.', options.muddler)
        muddler_globals = {
            # This puts the Component class in the config file's namespace
            'Component': config_classes.Component,
            # This puts the config_util in the config file's namespace
            'util': config_util,
            'options': options,
            'extra_options': extra_options,
        }
        execfile(options.muddler, muddler_globals)
        assert 'muddle' in muddler_globals
        assert callable(muddler_globals['muddle'])
        # Calls the muddle function with both the config and user's command
        # line options
        muddler_globals['muddle'](config)

    run(config, options, config_dir)

if __name__ == '__main__':
    main()

