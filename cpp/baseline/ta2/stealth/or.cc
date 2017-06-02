//****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of OR gate
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   yang           Original Version
//****************************************************************

#include "or.h"
#include "../../../common/check.h"

bool Or::EvaluateImpl(bool short_circuit) {
  CHECK(NumInputs() >= 2) << "Not enough inputs";
  bool value = false;
  for (int i = 0; i < NumInputs(); ++i) {
    if (GetInput(i)->Evaluate(short_circuit)) {
      value = true;
      if (short_circuit) {
        // At least one input is true. Short circuit and return.
        return value;
      }
    }
  }
  // All inputs are false
  return value;
}
