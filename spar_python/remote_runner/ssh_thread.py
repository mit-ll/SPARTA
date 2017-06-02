# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        A thread that handles command for a single host via SSH.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Jan 2013   omd            Original Version
# *****************************************************************

import logging
import os
import paramiko
import sys
import threading

logger = logging.getLogger(__name__)
paramikoLogger = logging.getLogger(paramiko.__name__)
paramikoLogger.setLevel(logger.getEffectiveLevel())

class SSHThread(threading.Thread):
    """We maintain one thread for each host we're working with. An SSHThread is
    a thread for talking to a single host via ssh. Once constructed and started
    this loops pulling items from the Queue that was passed to its constructor.
    Each item is assumed to be a function that takes a SSHClient as an argument.
    The item is then called with the SSHClient for this threads Host. This
    continues until a None item is pulled out of the queue at which point the
    thread exits.
    """
    def __init__(self, host, ssh_user, ssh_pass, queue):
        """Connect to host using ssh_user and ssh_pass as the username and
        password. As per the paramiko connect call these can be None for use
        with passwordless login, passwords for a secret key, etc. See the
        paramiko docs for details.

        queue is a Queue.Queue instance that is used to communicate work items
        to the thread.
        """
        self.__host = host
        self.__ssh_user = ssh_user
        self.__ssh_pass = ssh_pass
        self.__client = None
        self.__queue = queue
        super(SSHThread, self).__init__()
        # Make this a daemon thread so calls to sys.exit() or os._exit don't
        # wait for this thread to complete before allowing the program to
        # complete.
        self.daemon = True
        self.setDaemon(True)

    def run(self):
        """Pulls items of the queue and runs them until a None is found on the
        queue."""
        try:
            logger.debug('Connecting to %s.', self.__host)
            self.__connect()
            logger.debug('Connected to %s.', self.__host)
            while True:
                item = self.__queue.get()
                if item is None:
                    break
                assert callable(item)
                item(self.__client)
                self.__queue.task_done()
        except Exception as e:
            # If there was an uncaught exception in this thread call sys.exit so
            # the entire executable exits instead of hanging.
            logger.exception('Uncaught exception in thread for %s', self.__host)
            # The main thread in a Python application isn't a deamon thread and
            # exceptions don't get propagated from other threads to the main
            # thread. Thus the main thread wouldn't exit and the program
            # wouldn't exit unless we call os._exit. Calling sys.exit only
            # causes the current thread to exit which also wouldn't be enough.
            logging.info('Calling _exit')
            os._exit(1)

    def __connect(self):
        """Establish an ssh connection using the information passed to the
        constructor."""
        assert self.__client is None
        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__client.connect(self.__host, username = self.__ssh_user,
                password = self.__ssh_pass)
