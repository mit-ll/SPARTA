# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        A class to simply condition variables 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  04 Apr 2012   omd            Original Version
# *****************************************************************

import threading

class SimpleCondition(object):
    """When working with threads it's a common pattern to want to wait until a
    variable has attained a certain value. This requires a fair amount of
    boiler-plate code involving both the value to be watched, a Condition()
    object, locks, wait() calls, etc. This class makes that much easier. For
    example:

        class CondExample(object):
            def __init__(self):
                # Initialize an integer with value 0
                self.num_connections = SimpleCondition(0)

            def connection_made(self):
                # This is called from a different thread when a connection is
                # made
                self.num_connections.set(self.num_connections.get() + 1)

            def wait_for_ten(self):
                # This waits until 10 connections have been made
                self.num_connections.wait(10)

    Note that this works with any type, not just integers."""
    def __init__(self, value):
        """Create a SimpleCondition with initial value given by the value
        parameter."""
        self.__value = value
        self.__cond = threading.Condition()

    def set(self, value):
        """Change the value of this SimpleCondition. If any thread is waiting
        for the condition to attain this new value that thread will be
        awakened."""
        with self.__cond:
            self.__value = value
            self.__cond.notifyAll()

    def get(self):
        """Return the current value of the SimpleCondition."""
        with self.__cond:
            return self.__value

    def wait(self, value):
        """Block until this attains the given value."""
        self.wait_and_lock(value)
        self.__cond.release()

    def wait_and_lock(self, value):
        """Like wait but doesn't release the mutex once the condition is met.
        The caller must call unlock() on this object after this method
        returns."""
        self.__cond.acquire()
        while self.__value != value:
            self.__cond.wait()


    def lock(self):
        """Allows you to lock the state so other statements can be issued
        knowing that the condition here won't change."""
        self.__cond.acquire()

    def unlock(self):
        self.__cond.release()

    def __enter__(self):
        return self.__cond.__enter__()

    def __exit__(self, *args):
        self.__cond.__exit__(*args)
