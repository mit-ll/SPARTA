# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        A class providing Enum-like functionality for python
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  07 Dec 2011   omd            Original Version
# *****************************************************************

class Enum(object):
    """Provides enum like functionality. Simple use:

    ANIMALS = Enum('DOG', 'CAT', 'TIGER', 'WOLF')
    print ANIMALS.DOG  # prints 0
    print ANIMALS.CAT  # prints 1
    print ANIMALS.to_string(1) # prints 'CAT'

    # Print all the animals in order relative to their value
    for animal in ANIMALS.values_generator:
        print animal

    You can also specify indices for some or all of the items:

    ANIMALS = ENUM('DOG', 'CAT', LAMA = 10, HAMSTER = 0)

    Then HAMSTER == 0, DOG == 1 (the 1st value greater than 0 not specified in
    the kwargs), CAT == 2, and LAMA == 10.
    """
    def __init__(self, *args, **kwargs):
        """Construct an enum. If kwargs are supplied they should be of the form
        VALUE = integer like 'LAMA = 10' to indicate that Enum.LAMA == 10. After
        the kwargs are processed each of the args is examined in order and
        assigned the lowest possible integer value that does not conflict with a
        value specified in kwargs."""
        # Only called with empty args and kwargs by from_dict_list factory
        # method.
        if len(args) > 0 or len(kwargs) > 0:
            self.__setup(kwargs, args)

    def __setup(self, dict_vals, list_vals):
        """Does the real work of construction. Factored out so we can construct
        via standard constructor or via static from_dict_list method."""
        # __setattr__ is overridden below so we have to call __setattr__ on the
        # base class.
        #
        # Note: value_to_number and number_to_value are private and so should be
        # named __number_to_value and __value_to_number but that doesn't work
        # right with __setattr__ and since all accessors are overridden they are
        # adquately protected.
        if len(dict_vals) == 0 and len(list_vals) == 0:
            raise Exception('Can not construct an Enum with no values.')
        object.__setattr__(self, 'value_to_number', {})
        object.__setattr__(self, 'number_to_value', {})
        for k, v in dict_vals.items():
            if v in self.number_to_value:
                existing = self.number_to_value[v]
                raise ValueError("Can't assign two items to the same value. "
                        "Both %s and %s have been assigned %s" %
                        (existing, k, v))
            self.value_to_number[k] = v
            self.number_to_value[v] = k
        next_index = 0
        for k in list_vals:
            if k in self.value_to_number:
                raise ValueError("Can't assign two items the same name. "
                        '"%s" appears twice.' % k)
            while next_index in self.number_to_value:
                next_index += 1
            self.value_to_number[k] = next_index
            self.number_to_value[next_index] = k
            next_index += 1
       
    #for pickling       
    def __getstate__(self):
        return self.__dict__
    def __setstate__(self, d):
        object.__setattr__(self, 'value_to_number', d['value_to_number'])
        object.__setattr__(self, 'number_to_value', d['number_to_value'])
    
    @staticmethod
    def from_dict_list(dict_vals, list_vals = []):
        """Python has a limit of 255 arguments to a function. That means you
        can't construct an Enum with more than 255 values. There are some (rare)
        circumstances where it is desirable to have an enum with more values
        than that in which case you can construct an enum with this method.

        args:
            dict_vals: a dictionary mapping strings to integers. The is the
                analog of using kwargs in the normal constructor.
            list_vals: a list of strings. This is the analog of passing a list
                of strings to the constuctor.
        """
        e = Enum()
        e.__setup(dict_vals, list_vals)
        return e

    @staticmethod
    def from_enum(base_enum, *args, **kwargs):
        """Allows you to create a new enum from an existing one. The new enum
        will have all the name/value pairs as base_enum. In addition, *args and
        **kwargs will be processed as normal so that the new enum is a merge of
        the old one, any values in *args, and any key/value pairs in kwargs."""
        mapping = {}
        for name, val in zip(base_enum.values_generator(),
                base_enum.numbers_generator()):
            mapping[name] = val

        for name, val in kwargs.iteritems():
            if name in mapping:
                raise ValueError("'%s' can't be added to the enum as it is "
                        "in the base enum." % (name,))
            mapping[name] = val

        return Enum.from_dict_list(mapping, args)

    def __getattr__(self, name):
        """Returns the integer value associated with the attribute."""
        return self.value_to_number[name]

    def __setattr__(self, name, value):
        """Just throw an exception as enum attributes are constant."""
        raise ValueError("You can not change the values of enums")

    def __delattr__(self, name):
        raise ValueError("Enum values are constant and can not be changed.")

    def to_string(self, number):
        """Return the string representing the given value.""" 
        return self.number_to_value[number]

    def to_string_lower(self, number):
        """Return the string representing the given value in lower case.""" 
        return self.number_to_value[number].lower()
    
    def to_string_upper(self, number):
        """Return the string representing the given value in upper case.""" 
        return self.number_to_value[number].upper()
    
    def values_generator(self):
        """A generator that generates all the string values of the enum in order
        of their integer values."""
        for n in self.numbers_generator():
            yield self.number_to_value[n]

    def numbers_generator(self):
        """A generator that generates all the assigned numeric values in
        order."""
        numbers = self.number_to_value.keys()
        numbers.sort()
        for n in numbers:
            yield n
            
    def values_list(self):
        return [x for x in self.values_generator()]

    def numbers_list(self):
        return [x for x in self.numbers_generator()]

    def __str__(self):
        return str(self.number_to_value)

    def size(self):
        return len(self.number_to_value)
