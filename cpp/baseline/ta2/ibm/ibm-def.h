//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Auxilliary structs used by the lemon parser
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_IBM_DEF_H_
#define CPP_BASELINE_TA2_IBM_IBM_DEF_H_

#include "ibm-circuit-gates.h"

struct ParserState {
  boost::shared_ptr<Gate> output_gate;
  std::vector<WirePtr>* wires;
  int length;
};

struct InputToken {
  int type;
  const char* str_val;
  int int_val;
};

struct GateToken {
  Gate* gate;
};

struct BitsToken {
  BitArray* bits;
};

#endif
