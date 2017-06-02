# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Classes that define a configuration. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  08 Jan 2013   omd            Original Version
# *****************************************************************

import copy
import logging
import sys

logger = logging.getLogger(__name__)

class ConfigClassesBase(object):
    """All config classes are inherited from this.
    
    In order to reduce the chances of hard to debug configuration errors all
    configuration objects are immutable: users can set only those properites
    defined by a subclasses LEGAL_ATTRS class variable. This base class takes
    care of that enforcement.

    LEGAL_ATTRS must be an object that supports the 'in' operator. Since it is
    often searched a class like set() that supports this quickly is
    recommended.
    """
    def __init__(self, *args, **kwargs):
        """Does nothing."""
        assert len(args) == 0
        assert len(kwargs) == 0

    def __setattr__(self, name, value):
        if name in self.LEGAL_ATTRS:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError('The only legal attributes for this '
                    'object are %s' % self.LEGAL_ATTRS)

    def all_set(self):
        """Returns True if all the required attirbutes in LEGAL_ATTRS exist and
        are not None. False otherwise."""
        for a in self.LEGAL_ATTRS:
          try:
              getattr(self, a)
          except AttributeError:
              return False
        return True

    def get_missing_attributes(self):
        """Return a list of any attributes in LEGAL_ATTRS that aren't set on the
        current object."""
        missing = []
        for attr in self.LEGAL_ATTRS:
            try:
                getattr(self, attr)
            except AttributeError:
                missing.append(attr)

        return missing

    def check_all_set(self):
        """Checks that all attributes are set. If not, an error message is
        printed and sys.exit(1) is called."""
        if not self.all_set():
            logger.critical('All attributes on the %s object must be set. '
                    'Missing attributes: %s', self.__class__.__name__,
                    self.get_missing_attributes())
            sys.exit(1)

class Component(ConfigClassesBase):
    """A component refers to an executable, it's arguments, and any data files
    it needs.
    
    All "source" paths (e.g. the path to the executable attribute or the keys in
    the files dict) are either absolute or are assumed to be relative to the
    configuration file."""
    # In the following, base_dir refers the path specified in the base_dir
    # attribute. If that attribute is not set then a temprorary directory will
    # be created on the remote host and base_dir refers to that directory.
    LEGAL_ATTRS = set([
        'name',            # A human readable string printed in various status
                           # messages and such.

        'executable',      # Path to the executable. This will *not* be copied
                           # to the remote host unless it also appears in the
                           # files map.

        'args',            # An iteratable of the arguments to pass to
                           # the executable.

        'base_dir',        # See the comments above LEGAL_ATTRS

        'files',           # A dict-like object mapping source paths to remote
                           # paths. Each source path will be transferred to the
                           # corresponding remote_path on the remote host. If
                           # the remote path is a relative path (it doesn't
                           # start with a '/') it is relative to base_dir.

        'host',            # The hostname or ip address of the host where this
                           # component should be run.

        'start_index',     # All components are sorted by start_index and
                           # started in that order. The start_index need not be
                           # a total ordering, but must define a partial
                           # ordering.

        'wait',            # If True, remote-runner will not return until this
                           # Component's executable has returned.
        ])

    def __init__(self):
        super(Component, self).__init__()
        self.base_dir = None
        self.files = {}
        self.args = []

class Config(object):
    """The main configuration object.

    Each configuration file is called with a single instance of this class in
    it's global namespace. It must fill in all values in the object for the
    configuration to be valid.
    """
    LOCAL_HOST = 'localhost'
    def __init__(self):
        self.__components = []

    def add_component(self, component):
        """Add component to the set of components in the configuration.

        Note that this will make a *copy* of the component. That way it's safe
        to use one "template" component and keep modifying a few attributes of
        it (e.g. the IP address)."""
        self.__components.append(copy.deepcopy(component))

    def clear_components(self):
        self.__components = []

    def all_components(self):
        """Returns an iterator that will yield all the components."""
        return iter(self.__components)

    def all_remote_components(self):
        for c in self.__components:
            if c.host != self.LOCAL_HOST:
                yield c

    def all_local_components(self):
        for c in self.__components:
            if c.host == self.LOCAL_HOST:
                yield c

    def all_hosts(self):
        """Returns a set() of all the unique hosts in all components."""
        ret = set()
        for c in self.__components:
            ret.add(c.host)
        return ret

    def check_names_unique(self):
        names_list = [c.name for c in self.__components]
        names_set = set(names_list)
        if len(names_list) != len(names_set):
          logger.critical('All component names must be unique.')
          sys.exit(1)

