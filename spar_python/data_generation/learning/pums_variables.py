# *****************************************************************
#  Copyright 2011 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        Code to parse, store, and manipulate variables from the
#      PUMS data 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  07 Dec 2011   omd            Original Version
# *****************************************************************


"""
This file contains two type of classes:

1) Parser classes know how to parse values out of the PUMS data. They
return a compact (generally integer) representation of the variable
value. We keep the returned value small since we've got TONS of data
and we don't want to waste space.

2) Manipulator classes know how to interpret the values returned by
the parser. For example, if the field is an enum the manipulator knows
how to map the integer value to its string representation. It also
knows the variables name, etc.

The idea is that we want to parse records from the PUMS data and since
those records are so large we want to store them very
efficiently. Thus a parser class returns a compact representation of
the value. The manipulator class (and there is only one per variable
so the overhead is minimal) can interpret these values and provide
reasonable string representations, tell you the type of the variable,
etc.
"""

from spar_python.common.enum import Enum


VARIABLE_TYPES = Enum('CATEGORICAL', 'ORDINAL', 'INTEGER')
RECORD_SOURCE = Enum('PERSON', 'HOUSEHOLD')

class ParseException(Exception):
    def __init__(self, *args, **kwargs):
        super(ParseException, self).__init__(*args, **kwargs)

class IntParser(object):
    """Parser for simple integer values."""
    def __init__(self, field_start, field_end,
            allow_empty = False, source = RECORD_SOURCE.PERSON):
        """field_start is inclusive. field_end is exclusive.

        args:
            field_start: the character position at which the filed starts
            field_end: the character psoition at which it ends 

            allow_empty: some PUMS variables (such as income) can contain 
                blanks (such as for persons under 15). Unless allow_empty is 
                set to True, such blanks will cause a ParseError to be raised.
                If allow_empty is set to True, however, such blanks will
                return None. (Note: this is the only situation under which
                this class will return non-integer values.)
            source: RECORD_SOURCE.PERSON or RECORD_SOURCE.HOUSEHOLD indicating


                which line in the PUMS file contains this data.
        
        Important Note: both field_start and field_end are 0-based indices. The
        PUMS documentation which indicates character positions gives them in
        1-based indices and gives the end index as inclusive so you must
        convert!"""
        self._start = field_start
        self._end = field_end
        self.__allow_empty = allow_empty
        self.__source = source

    def source(self):
        """Does this data come from the person record or the household record.

        Values are from the RECORD_SOURCE enum."""
        return self.__source

    def parse(self, line):
        """Given a line of data from a PUMS file return the value corresponding
        to this field."""
        string_value = line[self._start:self._end]
        if all((x == ' ' for x in string_value)):
            if self.__allow_empty:
                return None
            else:
                raise ParseException(
                        'Unexpected  empty integer field '
                        '%s:%s in record:\n%s' %
                        (self._start, self._end, line))
        int_value = int(string_value)
        return int_value

class IntParserWithNull(IntParser):
    """Some variables have a special value which is treated as a missing value.
    This is a regular IntParser except you can also specify a value to be
    treated as NULL. When that value is encountered None is returned instead."""
    def __init__(self, null_value, *args, **kwargs):
        """Constructor.

        args:
            null_value: the integer value that should be treated as NULL.
            
            all other args are passed through directly to the IntParser
            constructor.
        """
        self.__null_value = null_value
        super(IntParserWithNull, self).__init__(*args, **kwargs)

    def parse(self, line):
        val = IntParser.parse(self, line)
        if val == self.__null_value:
            return None
        else:
            return val

class IntParserWithDefault(IntParser):
    """
    Some variables can be blank to indicate 'N/A'. The IntParser class
    can handle these variables (with the allow_empty argument to the 
    constructor) but will map them to None. This class acts exactly like
    IntParser, but 
    
    1) Sets allow_empty to True always, and
    2) Requires the user to provide a value to be used when a blank is
       encountered.
    """
    def __init__(self,  field_start, field_end,
                 default_value, source = RECORD_SOURCE.PERSON):
        """Constructor.

        args:
            default_value: value to be used when blank is encountered.
            
            all other args are as in the constructor to IntParser
        """
        super(IntParserWithDefault, self).__init__(field_start,
                                                   field_end,
                                                   allow_empty = True,
                                                   source = source)
        self.__default_value = default_value

    def parse(self, line):
        int_value = IntParser.parse(self, line)
        if int_value is None:
            int_value = self.__default_value
        return int_value
    

class IntManipulator(object):
    """Manipulator for simple integers. Since integers are so simple this does
    almost nothing but it has the same API as other manipulators thus making it
    easy to blindly do the same thing (e.g. convert to string) all values in a
    record."""
    def __init__(self, description):
        self.__description = description

    def description(self):
        return self.__description

    def to_string(self, int_value):
        return str(int_value)

    def type(self):
        return VARIABLE_TYPES.INTEGER

    def dimension(self):
        return 1

class EnumParser(IntParser):
    def __init__(self, enum, field_start, field_end,
            source = RECORD_SOURCE.PERSON):
        """Same as IntParser except that it also includes an Enum indicating
        how to map the integer values in the PUMS data to what they stand
        for."""
        IntParser.__init__(self, field_start, field_end, source = source)
        self.__enum = enum
        self.__legal_values = set(self.__enum.numbers_generator())

    def parse(self, line):
        int_value = IntParser.parse(self, line)
        assert int_value in self.__legal_values, \
            ('Illegal enum value in this record:\n\n%s\n\nPosition %s:%s '
             'is %s but legal values are %s') % \
                     (line, self._start, self._end, int_value, str(self.__enum))
        return int_value

class RemapEnumParser(EnumParser):
    """Like EnumParser but include a way to remap some values to others. For
    example, the census data for language maps anything in the range 0 - 600 to
    the value "NOT_IN_UNIVERSE" so this class lets you create an enum with a
    single value for NOT_IN_UNIVERSE and then a simple expression saying to
    remap all values in the range 0, 600 to that one value."""
    def __init__(self, remap_list, enum, *args, **kwargs):
        """Constructor. All arguments are as for EnumParser except remap_list.
        That is a list of tuples such that remap_list[i][0] is an object that
        supports the "in" operator (i.e. "10 in remap_list[i][0]" is a valid
        expression) and remap_list[i][1] is a value. If the parsed integer value
        is contained in the  remap_list[i][0] it will be mapped to
        remap_list[i][1]. This sounds complex but isn't. For example, the
        following tuples would map the range [0, 20) to 100 and [50, 100) to 7:

        [(range(0, 20), 100), (range(50, 100), 7)]
        """
        super(RemapEnumParser, self).__init__(enum, *args, **kwargs)
        # sanity check
        for num in enum.numbers_generator():
            for mapper in remap_list:
                assert not num in mapper[0]
        self.__remap_list = remap_list

    def parse(self, line):
        int_value = IntParser.parse(self, line)
        for mapper in self.__remap_list:
            if int_value in mapper[0]:
                return mapper[1]

        return super(RemapEnumParser, self).parse(line)

class EnumManipulator(IntManipulator):
    def __init__(self, enum, description):
        IntManipulator.__init__(self, description)
        self.__enum = enum

    def to_string(self, int_value):
        return self.__enum.to_string(int_value)

    def type(self):
        raise Exception(
            'Must use either CategoricalManipulator or OrdinalManipulator')

    def enum(self):
        return self.__enum

    def dimension(self):
        return self.__enum.size() - 1

class CategoricalManipulator(EnumManipulator):
    def __init__(self, *args, **kwargs):
        EnumManipulator.__init__(self, *args, **kwargs)

    def type(self):
        return VARIABLE_TYPES.CATEGORICAL

class OrdinalManipulator(EnumManipulator):
    def __init__(self, *args, **kwargs):
        EnumManipulator.__init__(self, *args, **kwargs)

    def type(self):
        return VARIABLE_TYPES.ORDINAL
