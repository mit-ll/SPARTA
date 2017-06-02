
# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            SY
#  Description:        IBM TA2 batch class 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  14 Nov 2012   SY             Original Version
# *****************************************************************

class IBMBatch(list):
    """
    This class represents a batched input.
    """
    def __str__(self):
        return "".join([str(int(inp_bit)) for inp_bit in self])

    def get_num_values(self, value):
        """returns the number of instances of value in the batch"""
        num_values = 0
        for elt in self:
            if elt == value:
                num_values += 1
        return num_values
