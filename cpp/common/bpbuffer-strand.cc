//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of BPBufferStrand 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Aug 2012   omd            Original Version
//*****************************************************************

#include "bpbuffer-strand.h"

FixedSizeMemoryPool BPBufferStrand::memory_pool_(sizeof(BPBufferStrand));
