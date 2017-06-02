//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:        SPAR
// Authors:        Yang
// Description:    A logical XOR gate.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 07 Aug 2012   Yang           Original Version
//****************************************************************

#ifndef CPP_BASELINE_TA2_STEALTH_XOR_H_
#define CPP_BAsELINE_TA2_STEALTH_XOR_H_

#include "multi-input-gate.h"

// This class defines a logical XOR gate which performs a boolean
// XOR operation on all of its inputs.
class Xor : public MultiInputGate {
 public:
  virtual ~Xor() {}

 protected:
  // Returns false if all or none of its inputs are true,
  // true otherwise.
  virtual bool EvaluateImpl(bool short_circuit);
};

#endif
