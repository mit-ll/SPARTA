//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Baseline that implements the Stealth circuit evaluation 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_STEALTH_STEALTH_BASELINE_H_
#define CPP_BASELINE_TA2_STEALTH_STEALTH_BASELINE_H_

#include "baseline/ta2/common/baseline.h"

class StealthCircuitParser;

class StealthBaseline : public Baseline {

 public:

  // Initalize the Baseline by passing it the StealthCircuitParser
  StealthBaseline(StealthCircuitParser* p);

 private:

  virtual void ReadInputAndEvaluate();

};

#endif
