# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            JL
#  Description:        This code takes in two integers and compares
#                      them based on a contained function.  If the two
#                      integers meet the criteria, then it will return
#                      the boolean value True
#                      
#                      
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  31 July 2012  JL             Original Version
# *****************************************************************

def baa_criteria(a_num, b_num):

    "This returns true if and only if a_num <= 10*b_num + 15"    
   
    assert a_num > 0
    assert b_num > 0

    #This function could easily changed if a different criterion is determined.
    
    if 10 * b_num + 15 >= a_num:
        return True
    else:
        return False

    

