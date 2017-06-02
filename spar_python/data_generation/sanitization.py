# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JCH
#  Description:        Logic for removing invalid/illegal strings from 
#                      distributionsd
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Oct 2013  jch             Original file
# *****************************************************************
import re


import spar_python.data_generation.spar_variables as spar_vars

# The following characters should not appear outside RAW/ENDRAW fields
FORBIDDEN_CHARACTERS = ['|', '"']

# List of (forbidden line, replacement) pairs
FORBIDDEN_LINES = [('RAW', "FOO")]


def sanitize_distribution(dist_holder):
    """
    Excises all forbidden characters and lines from the given dist_holder.
    Note: returns None, works by *changing* the input value. Raises 
    AssertionError if sanitization is not possible
    """
    
    
    # Unfortunately, this is going to be complicated. Why? What we ultimately
    # want to sanitize is what is possible in the line-raw files. This means
    # that we need to operate on the line-raw form of a value, which is not
    # known to the distribution objects. Furthermore, the sanitization logic 
    # depends on the *type* of the variable-- notes, enum, int, etc.
    # Therefore, we need to divide all the variables in the dist_holder into
    # the different types and sanitize each type in a different way.
    
    for var in dist_holder.var_order:
        
        dist = dist_holder.dist_dict[var]
        
        ##################################################################
        #
        # Sanitizing districutions over enum values
        #
        ##################################################################
        
        
        if var in spar_vars.ENUM_VARS:
            
            # If a forbidden character or line is found here,
            # there is not much we can do.
            
            converter = spar_vars.VAR_CONVERTERS[var].to_line_raw
            support = dist.support()
            
            for value in support:
                
                str_val = converter(value)
                
                for forbidden_character in FORBIDDEN_CHARACTERS:
                    assert forbidden_character  not in str_val
                    
                for (forbidden_word, _) in FORBIDDEN_LINES:
                    assert str_val != forbidden_word
        
        
        
        ##################################################################
        #
        # Sanitizing districutions over int values
        #
        ##################################################################
        
        
        elif (var in spar_vars.INT_VARS) or (var == spar_vars.VARS.SSN):
            
            # Although SSNs are strings, they are strings of the format
            # "DDDDDDDDD" (i.e, 9 digits). Therefore they get the same
            # sanitization as integer variables. And this sanitizaton one is
            # pretty simple (perhaps overly so: check that none of the forbidden
            # characters are numeric and that none of the forbidden lines are
            # integers
            
            for forbidden_character in FORBIDDEN_CHARACTERS:
                assert forbidden_character not in "0123456789"
        
            for (forbidden_word, _) in FORBIDDEN_LINES:
                try:
                    int(forbidden_word)
                    assert False, "Tried to forbid integer value %s" % forbidden_word
                except ValueError:
                    # This means it couldn't be converted to an int, which 
                    # means it's okay.
                    pass
                
        
        
        ##################################################################
        #
        # Sanitizing other districutions with easily enumerable supports 
        # and the remap() method
        #
        ##################################################################
        
        
        elif var in spar_vars.REMAPABLE_VARS:
            
            for (forbidden_word, replacement) in FORBIDDEN_LINES:
                dist.remap(forbidden_word, replacement)
            
            # Okay, now check that no fibidden characters show up in these
            # distributions
            converter = spar_vars.VAR_CONVERTERS[var].to_line_raw
            support = dist.support()
            for value in support:
                
                str_val = converter(value)
                
                for forbidden_character in FORBIDDEN_CHARACTERS:
                    assert forbidden_character  not in str_val
                            
        
        
        #####################################################################
        #
        # And now all the corner cases
        #
        ####################################################################
        
        
        elif var == spar_vars.VARS.STREET_ADDRESS:
            
            
            for forbidden_char in FORBIDDEN_CHARACTERS:
                assert forbidden_char not in '0123456789 APT'
            
            # For this distribution, support() actually returns the set
            # of street names
            for street in dist.support():
                for forbidden_char in FORBIDDEN_CHARACTERS:
                    assert forbidden_char not in street
                    
            # Not going to test against FORBIDDEN_LINES in this version

        
        elif var == spar_vars.VARS.XML:
            
            # This got so complicated that we needed to move it into the
            # XmlGenerator object. Next line will raise AssertError if
            # any of the forbidden characters could be in the XML string.
            
            dist.check_forbidden_characters(FORBIDDEN_CHARACTERS)
            
            # WE're not checking the forbidden-lines against XML in this phase

        
        elif var == spar_vars.VARS.DOB:
            
            # Since dates are printed in YYYY-MM-DD format, 
            # we can do this directly:
            
            for forbidden_char in FORBIDDEN_CHARACTERS:
                assert forbidden_char not in '0123456789-'
                
            for (forbidden_line, _) in FORBIDDEN_LINES:
                iso_re = re.compile("^\d{4}-\d{2}-\d{2}")
                match_obj = iso_re.match(forbidden_line)
                if match_obj:
                    assert False, "Cannot forbid date-string %s" % forbidden_line
                    
                            

        #####################################################################
        #
        # Checking that we didn't miss anything
        #
        ####################################################################
        
        else:
            
            # The only vars we shouldn't need to sanitize are the ones in 
            # RAW/ENDRAW delimiters:
            
             assert var in spar_vars.RAW_VARS
            
    
    
    
