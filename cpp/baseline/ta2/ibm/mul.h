//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description         Definition of IBM AND Gate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Aug 2012   yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_MUL_H_
#define CPP_BASELINE_TA2_IBM_MUL_H_

#include "binary-gate.h"

class Mul : public BinaryGate {
 public:
  // Returns the bit-wise AND operation of its left and right inputs
  virtual BitArray EvaluateImpl() {
    return left_input()->Evaluate() & right_input()->Evaluate();
  }
};
#endif
