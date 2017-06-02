# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        Reads in lineraw rows to be modifed for 
#                      modification tests
# *****************************************************************

import os
import sys
# Note that realpath (as opposed to abspath) also expands symbolic
# links so the path points to the actual file. This is important when
# installing scripts in the install directory.  Scripts will be
# symbolic linked to the install directory. When a script is run from
# the install directory, realpath will convert it to the actual path
# where the script lives. Appending base_dir to sys.path (as done
# below) allows the imports to work properly.
this_dir = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import spar_python.data_generation.output_ordering as oo
import spar_python.data_generation.spar_variables as sv

STARTROW = "INSERT"
ENDROW = "ENDINSERT\n"
STARTRAW = "RAW\n"
ENDRAW = "ENDRAW\n"

def get_field_order(schema_file):
    return oo.get_output_order(schema_file)

def get_next_lineraw_entry(handle):
    line = handle.readline()
    if (line == ''): #EOF
        raise EOFError()

    if line == ENDROW:
        return None

    if line == STARTRAW:
        return get_raw(handle)
    
    return line.strip()

def get_raw(handle):
    length = int(handle.readline())
    line = handle.read(length)
    if line[-1] == "\n":
        line = line[:-1]
    nexttoken = handle.readline()
    if (nexttoken != ENDRAW):
        raise ValueError("Did not get expected ENDRAW token")
    return STARTRAW + str(length) + "\n" + line + ENDRAW[:-1]
    
    
def get_row(handle, order, rowid = None):
    '''
    rowid is optional, when specified will replace the actual row id
    with this number
    '''
    row_dict = {}
    raw_lines = []
    
    try:
        token = get_next_lineraw_entry(handle)
    except EOFError:
        return None
    if (token != STARTROW):
        raise ValueError("Did not get expected INSERT token")
    
    for field in range(len(order)):
        entry = get_next_lineraw_entry(handle)
        if (entry == None):
            raise ValueError("Received early ENDINSERT token")
        field = sv.enum_to_sql_name(order[field])
        # renumber rowid if requested
        if rowid and field == 'id':
            entry = rowid
        row_dict[field] = entry
        raw_lines.append(entry)
    
    
    token = get_next_lineraw_entry(handle)
    if (token != None):
        raise ValueError("Got %s instead of expected ENDINSERT token" % token)
    
    row_dict['raw_data'] = '\n'.join(raw_lines)
    return row_dict



def test_main():
    schema_file  = "./test_schema.csv"
    order = get_field_order(schema_file)
    handle = open("./lineraw.out", "r")
    i = 0
    while True:
        row = get_row(handle, order)
        if row == None:
            break
        print row
        i += 1
        
    print "read %d rows\n" % i
    print "DONE"


if __name__ == "__main__":
    test_main()
    
