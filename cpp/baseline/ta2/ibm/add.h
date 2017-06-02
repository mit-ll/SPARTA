//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        An IBM addition gate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_ADD_H_
#define CPP_BASELINE_TA2_IBM_ADD_H_

#include "binary-gate.h"

class Add : public BinaryGate {
 public:
  // Returns the bit-wise XOR operation of its left and right inputs
  virtual BitArray EvaluateImpl() {
    return left_input()->Evaluate() ^ right_input()->Evaluate();
  }
};

#endif
