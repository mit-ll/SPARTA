# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD, NJH
#  Description:        Wrappers around paramiko for this use case. 
# *****************************************************************

import collections
import subprocess
import ssh_thread
import functools
import tempfile
import logging
import os.path
import hashlib
import shutil
import Queue
import errno
import time
import sys
import os

logger = logging.getLogger(__name__)

class SSHManager(object):
    """Provides methods that copy data, perform commands via ssh, etc.

    This is *not* intended to be a general-purpose ssh class. Rather this
    provides just the functions that are useful to remote_runner.py.

    Since SSH can be slow this uses a set of threads to enable parallel
    execution of commands on multiple hosts. It thus maintains a dict,
    __ssh_threads, mapping hosts to SSHThread instances that are used to run all
    actual commands.
    """
    def __init__(self, config, options):
        """
        Args:
            config:  a config_classes.Config object.
            options: the options the user provided on the command line.
        """

        self.__config = config
        self.__options = options
        self.__done_dirs = {}
        self.__done_scripts = {}

    def done(self):
        """Put a signal in the queue to each thread asking them to exit. Block
        until all threads complete."""
        logger.info('Stopping all threads.')
        for t, q in self.__ssh_threads.itervalues():
            q.put(None)
        for t, q in self.__ssh_threads.itervalues():
            t.join()
        logger.info('All threads stopped.')

    def killall(self, config):
        """Kills all components via the killall command"""
        for component in config.all_remote_components():
            logger.info("killing %s on %s" % (component.executable,component.host))
            command = "killall %s" % (component.executable,)
            self.run_command(component.host, command)
        for component in config.all_local_components():
            logger.info("killing %s on %s" % (component.executable,component.host))
            command = "killall %s" % (component.executable,)
            subprocess.call(command, shell = True)

    def connect_all(self):
        """Spawn a thread for each unique host in the set of components. Have
        that thread initiate an ssh connection to the host."""
        # __connections is a map from host to an SSHClient instance.
        self.__ssh_threads = {}
        self.__wait_threads = {}
        for component in self.__config.all_remote_components():
            if component.wait:
                logger.debug('Requesting wait thread for %s', component.name)
                self.__wait_threads[component.name] = \
                  self.__connect_thread(component)
            if not component.host in self.__ssh_threads:
                logger.debug('Requesting task thread for %s', component.host)
                self.__ssh_threads[component.host] = \
                  self.__connect_thread(component)

    def __connect_thread(self, component):
        queue = Queue.Queue()
        thread  = ssh_thread.SSHThread(component.host,
                self.__options.ssh_user, self.__options.ssh_pass, queue)
        thread.start()
        return (thread, queue)

    def run_command(self, host, command):
        """Queue command to be run on host. Return immediately without waiting
        for the command to actually complete."""
        t, q = self.__ssh_threads[host]
        q.put(functools.partial(SSHManager.__run_command, command))

    def prepare_for_waits(self):
        # Ensure this hasn't already been called
        assert len(self.__done_dirs) == 0
  
        # Make temporary directories to host pid/done files
        for c in self.__config.all_remote_components():
            if c.wait:
                t, q = self.__ssh_threads[c.host]
                q.put(functools.partial(self.__set_done_dir, c, 
                                        self.__done_dirs))
        self.wait_for_empty_queues()
        for c in self.__config.all_local_components():
            if c.wait:
                self.__done_dirs[c.name] = tempfile.mkdtemp()
  
        # Convert Components that need to wait to use special Bash scripts that
        # can detect when Component executables complete
        for c in self.__config.all_components():
            if c.wait:
                args_str = ' '.join(['"%s"' % x for x in c.args])
                bash_file = tempfile.NamedTemporaryFile(delete=False)
                bash_file.write( \
                  "#!/bin/bash\n" + \
                  'SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" ' + \
                      '&& pwd )"\n')
                # TODO include better handling if the executable doesn't exist
                # or fails
                if c.host == 'localhost' or c.host == '127.0.0.1':
                  if os.path.dirname(c.executable):
                    bash_file.write("%s %s &\n" % (c.executable, args_str))
                  else:
                    bash_file.write("./%s %s &\n" % (c.executable, args_str))
                elif c.executable.startswith('/'):
                  bash_file.write( \
                    "%s %s &\n" % (c.executable, args_str))
                else:
                  bash_file.write( \
                    "$SCRIPT_DIR/%s %s &\n" % (c.executable, args_str))
                bash_file.write( \
                  "PID=$!\n" + \
                  "echo $PID >> %s\n" % os.path.join(self.__done_dirs[c.name],
                                                     "%s.pid" % c.name) + \
                  "wait $PID\n" + \
                  "touch %s\n" % os.path.join(self.__done_dirs[c.name],
                                              "%s.done" % c.name)
                )
                bash_file.close()
                os.chmod(bash_file.name, 0775)
                logger.debug('Wrote polling bash script for %s to %s', c.name,
                             bash_file.name)
                c.args = []
                if c.host == 'localhost' or c.host == '127.0.0.1':
                  basedir = os.path.dirname(bash_file.name)
                  newpath = os.path.join(basedir, 
                                         "%s-remote-runner-script.sh" % c.name)
                  shutil.move(bash_file.name, newpath)
                  self.__done_scripts[c.name] = newpath
                  c.executable = newpath
                else:
                  self.__done_scripts[c.name] = bash_file.name
                  c.executable = "%s-remote-runner-script.sh" % c.name
                  c.files[bash_file.name] = c.executable
  
    def wait_for_commands(self):
        for c in self.__config.all_remote_components():
            if c.wait:
                t, q = self.__wait_threads[c.name]
                q.put(functools.partial(self.__wait_for_done, c, 
                                        self.__done_dirs))
                logger.debug('Scheduled wait for %s.' % c.name)
        self.wait_for_wait_queues()
        logger.debug('Done waiting for remote components.')
        for c in self.__config.all_local_components():
            if c.wait:
                while not os.path.exists( \
                        os.path.join(self.__done_dirs[c.name], 
                                     '%s.done' % c.name)):
                    time.sleep(1)
        logger.debug('Done waiting for local components.')
        
    @staticmethod
    def __wait_for_done(component, done_dirs, ssh_client):
        stdin, stdout, stderr = ssh_client.exec_command( \
            'while [[ ! -e %s ]]; do sleep 1; done' % \
              os.path.join(done_dirs[component.name], 
                           '%s.done' % component.name))
        stdout_contents = [x for x in stdout]
        if len(stdout_contents):
            logger.warning( \
               'Error occurred when waiting for %s to complete: %s' % \
                  (component.name, stdout_contents))
        logger.info('Done waiting for %s.', component.name)

    @staticmethod
    def __run_command(command, ssh_client):
        # We ignore the output of the command here.
        # TODO(odain) If the command returns a lot of output this will block
        # forever as the results aren't read :(
        stdin, stdout, stderr = ssh_client.exec_command(command)

    def set_base_dirs(self):
        """If any component has a base_dir attribute of None, create a temporary
        directory on its host and put the path to that dir in its base_dir
        attribute."""
        for c in self.__config.all_remote_components():
            if c.base_dir is None:
                t, q = self.__ssh_threads[c.host]
                q.put(functools.partial(self.__set_base_dir, c))
        self.wait_for_empty_queues()

    def wait_for_empty_queues(self):
        """Wait until all work on all ssh queues has been completed."""
        for t, q in self.__ssh_threads.itervalues():
            q.join()

    def wait_for_wait_queues(self):
        """Wait until all work on all wait queues has been completed."""
        for t, q in self.__wait_threads.itervalues():
            q.join()

    @staticmethod
    def __set_done_dir(component, done_dirs, ssh_client):
        """Create a temporary directory on the remote host."""
        stdin, stdout, stderr = ssh_client.exec_command('mktemp -d')
        new_dir = SSHManager.__get_single_line_response(stdout)
        done_dirs[component.name] = new_dir
        logger.debug('Set done dir for %s to %s', component.name,
                     done_dirs[component.name])

    @staticmethod
    def __set_base_dir(component, ssh_client):
        """Create a temporary directory on the remote host."""
        stdin, stdout, stderr = ssh_client.exec_command('mktemp -d')
        new_dir = SSHManager.__get_single_line_response(stdout)
        component.base_dir = new_dir
        logger.info('Set base dir for %s to %s', component.name, new_dir)

    @staticmethod
    def __get_single_line_response(output_f):
        """Paramiko exec_command calls return a file-like object. In many cases
        we expect that file to contain just a single line of output. This
        ensures that is the case and it returns that single line."""
        all_out = [x for x in output_f]
        assert len(all_out) == 1, all_out
        return all_out[0].rstrip()

    def copy_all(self):
        """Copy all files specified in the configuration to the correct remote
        host."""
        # Build a map from host to a list of (soucrce, dest) tuples indicating
        # source files and the desired location on the destination machine. Note
        # that a single source file may be copied to more than one location on
        # the remote host.
        host_to_files = collections.defaultdict(list)
        for c in self.__config.all_remote_components():
            host_to_files[c.host].extend([(s, d) for s, d in
                c.files.iteritems()])
        # Now run the __copy_files function on each remote host
        for h, f in host_to_files.iteritems():
            t, q = self.__ssh_threads[h]
            q.put(functools.partial(self.__copy_files, f,
                self.__options.always_copy, h))
        logger.info('All transfers started. Waiting for completion.')
        self.wait_for_empty_queues()
        logger.info('All transfers complete.')

    @staticmethod
    def __file_has_changed(ssh_client, sftp_client, src, dest, host):
        """Tries to determine if src and dest have the same contents as quickly
        as possible."""
        assert os.path.exists(src)
        try:
            remote_stat = sftp_client.stat(dest)
        except IOError as e:
            if e.errno == errno.ENOENT:
                if os.path.isdir(src):
                    logger.debug('Directory %s does not exist on %s. '
                            'Will create it', dest, host)
                else:
                    logger.debug('File %s does not exist on %s. '
                            'Will copy it', dest, host)
                return True
            else:
                raise e

        if not remote_stat.st_size == os.stat(src).st_size:
            logger.debug('Sizes are unequal for %s and %s on %s. '
                    'Will copy file', src, dest, host)
            return True

        # Directories should not be hashed; as long as they exist and have the
        # same size, we can assume that the 'file' has not changed.
        if os.path.isdir(src):
            return False

        # The file exists and both files are the same size. Since some files are
        # really big we don't want to copy if we can help it. Thus we compute
        # the file's hash on the remote machine and compare it to a local hash.
        # On a 500MB file this takes about 1 second compared to the many minutes
        # it'd take to copy it so this is a good trade-off.
        #
        # TODO(odain): Perhaps make this an option or only bother doing it for
        # bigger files. For small files this probably takes longer than it would
        # to just copy the file over.
        stdin, stdout, stderr = ssh_client.exec_command(
                'openssl dgst -sha1 %s' % dest)
        dest_hash = SSHManager.__get_single_line_response(stdout)
        assert dest_hash.startswith('SHA1(')
        dest_hash = dest_hash.split(' ')[1]

        sha = hashlib.sha1()
        with open(src, 'r') as f:
            for chunk in iter(lambda: f.read(sha.block_size * 128), b''):
                sha.update(chunk)
        src_hash = sha.hexdigest()
        logger.debug('Hashes. Local: %s. Remote: %s:%s', src_hash,
                host, dest_hash)

        if src_hash == dest_hash:
            return False
        else:
            return True

    @staticmethod
    def __copy_files(files_list, always_copy, host, ssh_client):
        sftp = ssh_client.open_sftp()
        for src, dest in files_list:
            logger.debug('Processing source file %s for %s to %s.', 
                          src, host, dest)
            if not os.path.isdir(src) and not os.path.isfile(src):
                logger.critical('Cannot find source file or directory %s.', src)
                # TODO below does not appear to be sufficient to kill the
                # entire call stack
                sys.exit(1)
            # Handle directories
            if os.path.isdir(src) and \
                SSHManager.__file_has_changed(ssh_client, sftp, 
                                              src, dest, host):
                stdin, stdout, stderr = ssh_client.exec_command(
                        'mkdir -p %s' % dest)
                err = [x for x in stderr]
                if len(err) > 0:
                    logger.critical('Unable to create directory: %s. '
                            'Error:\n%s', dest, err)
                    sys.exit(1)
            # Handle files
            elif os.path.isfile(src) and \
                (always_copy or SSHManager.__file_has_changed(ssh_client, sftp, 
                                                              src, dest, host)):
                try:
                    remote_dir = os.path.dirname(dest)
                    remote_stat = sftp.stat(os.path.dirname(dest))
                except IOError as e:
                    if e.errno == errno.ENOENT:
                        logger.debug('Remote directory %s does not exist '
                                'on %s. Creating it.', remote_dir, host)
                        stdin, stdout, stderr = ssh_client.exec_command(
                                'mkdir -p %s' % remote_dir)
                        err = [x for x in stderr]
                        if len(err) > 0:
                            logger.critical('Unable to create directory: %s. '
                                    'Error:\n%s', remote_dir, err)
                            sys.exit(1)
                    else:
                        raise e
                try:
                    logger.debug('Copying %s to %s:%s.', src, host, dest)
                    sftp.put(src, dest)
                    sftp.chmod(dest, os.stat(src).st_mode)
                    logger.debug('Copy of %s to %s:%s complete.', src,
                            host, dest)
                except Exception as e:
                    logger.critical('Copying of %s to %s:%s failed. Error:\n%s',
                            src, host, dest, e)
                    sys.exit(1)
            else:
                logger.debug('%s:%s unchanged. Skipping copy.', host, dest)

