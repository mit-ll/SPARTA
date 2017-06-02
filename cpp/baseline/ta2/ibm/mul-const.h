//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        An IBM constant multiplication gate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_MUL_CONST_H_
#define CPP_BASELINE_TA2_IBM_MUL_CONST_H_

#include "unary-gate.h"

class MulConst : public UnaryGate {
 public:
  // Returns the bit-wise AND operation of the constant and input
  virtual BitArray EvaluateImpl() {
    return constant() & input()->Evaluate();
  }
};

#endif
