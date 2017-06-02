//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    A logical OR gate.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   yang           Original Version
//****************************************************************

#ifndef CPP_BASELINE_TA2_STEALTH_OR_H_
#define CPP_BASELINE_TA2_STEALTH_OR_H_

#include "multi-input-gate.h"

// This class defines a logical OR gate which performs a
// boolean OR operation o nall of its inputs.
class Or : public MultiInputGate {
 public:
  virtual ~Or() {}

 protected:
  // Returns TRUE if one or more inputs are TRUE, FALSE otherwise.
  virtual bool EvaluateImpl(bool short_circuit);
};

#endif
