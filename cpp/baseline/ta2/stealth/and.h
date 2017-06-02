//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    A boolean AND gate for Stealth circuits.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   yang           Original Version
//****************************************************************

#ifndef CPP_BASELINE_TA2_STEALTH_AND_H_
#define CPP_BASELINE_TA2_STEALTH_AND_H_

#include "multi-input-gate.h"

// This class defines a boolean AND gate which performs a
// logical AND operation on all of its inputs.
class And : public MultiInputGate {
 public:
  virtual ~And() {}

 protected:
  // Returns true if all inputs are true, false otherwise.
  virtual bool EvaluateImpl(bool short_circuit);

};

#endif
