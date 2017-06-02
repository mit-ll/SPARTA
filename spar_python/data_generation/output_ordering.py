# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            omd
#  Description:        Set up the order in which variables should be written to
#                      output files.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  35 Oct 2012   omd            Initial
# *****************************************************************

import os.path
import csv
import spar_variables

def get_output_order(schema_file):
    """
    Given name of schema file, return a list indicating the order in which the
    variables should be output. The returned list is just a list of integers
    indicating the spar_variables.VARS enum values of the fields to be generated.
    """
    assert(schema_file is not None)
    assert(os.path.exists(schema_file)), 'Could not find %s' % schema_file

    schema_f = open(schema_file, 'r')
    reader = csv.DictReader(schema_f)
    var_order = []
    for row in reader:
        # TODO(njhwang) This is not a pretty hack, but this was the most
        # painless way to fix our row hashing problem. An improvement would be
        # to have the 'hash' field reserved for the explicit purposes of row
        # hashing, and have a generator that includes these row hashes as part
        # of the data generator output. Currently, we haven't ported our C++
        # hash algorithm to Python, and doing so now would be risky. So the C++
        # code is still computing the hashes, and manually appending that to the
        # line raw data the data generator produces. For row hashes to be
        # included, the database schema *must* define the 'hash' column as the
        # *last* item. I've included a hack to skip the 'hash' column here.
        if row['name'] != 'hash':
            var_order.append(spar_variables.sql_name_to_enum(row['name']))
        
    return var_order
