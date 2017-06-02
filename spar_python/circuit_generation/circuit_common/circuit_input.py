
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        TA2 input class
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  14 Nov 2012   SY             Original Version
# *****************************************************************

# this class is meant to standardize input printing.

class Input(list):
    """
    This class represents a batched input.
    """
    def __str__(self):
        display_string =  ",".join([str(inp_elt) for inp_elt in self])
        return "".join(["[", display_string, "]"])

    def get_num_values(self, value):
        """returns the number of instances of value in the input"""
        num_values = 0
        func_name = "get_num_values"
        for elt in self:
            try:
                num_values += elt.get_num_values(value)
            except AttributeError:
                if elt == value:
                    num_values += 1
        return num_values

    def get_num_zeros(self):
        """returns the number of 0s in the input"""
        return self.get_num_values(0)

    def get_num_ones(self):
        """returns the number of 1s in the input"""
        return self.get_num_values(1)
