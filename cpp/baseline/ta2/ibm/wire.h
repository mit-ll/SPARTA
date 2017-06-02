//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        IBM Constant Gate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Aug 2012   yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_CIRCUIT_EVALUATION_IBM_CONST_H_
#define CPP_BASELINE_TA2_CIRCUIT_EVALUATION_IBM_CONST_H_

#include "gate.h"
#include "common/logging.h"

// A Wire is the baseline's representation of a wire. It has no inputs and
// always outputs the same bit-array, set using the SetInput() method.
class Wire : public Gate {
 public:

  void SetInput(BitArray input) {
    SetOutput(input);
  }

  virtual BitArray Evaluate() {
    return output();
  }
 
  virtual void Reset() {}

};
typedef boost::shared_ptr<Wire> WirePtr;

#endif
