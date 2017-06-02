//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        IBM Baseline 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 25 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_IBM_BASELINE_H_
#define CPP_BASELINE_TA2_IBM_IBM_BASELINE_H_

#include "baseline/ta2/common/baseline.h"

class IbmCircuitParser;

class IbmBaseline : public Baseline {

 public:
  // Initialize the baseline by passing it the IbmCircuitParser
  IbmBaseline(IbmCircuitParser* p);

 private:
  virtual void ReadInputAndEvaluate();

};

#endif
