//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        An IBM constant addition gate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_ADD_CONST_H_
#define CPP_BASELINE_TA2_IBM_ADD_CONST_H_

#include "unary-gate.h"

class AddConst : public UnaryGate {
 public:
  // returns the bit-wise XOR of the input with the specified constant 
  virtual BitArray EvaluateImpl() {
    return constant() ^ input()->Evaluate();
  }
};
#endif
