# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            OMD
#  Description:        An exmaple muddler. 
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  09 Jan 2013   omd            Original Version
# *****************************************************************

def muddle(config):
    """All this muddler does is add the word "muddled" to the end of each
    components argument string."""
    for c in config.all_components():
        c.args.append('muddled')
