//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of NumberedCommandCounter 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#include "numbered-command-counter.h"

#include "common/statics.h"

NumberedCommandCounter* NumberedCommandCounter::instance_;

void InitialzeNumberedCommandCounter() {
  NumberedCommandCounter::instance_ = new NumberedCommandCounter();
}

void FinalizeNumberedCommandCounter() {
  delete NumberedCommandCounter::instance_;
}

ADD_INITIALIZER("InitNumberedCommandCounter", 
                &InitialzeNumberedCommandCounter);
ADD_FINALIZER("FinalizeNumberedCommandCounter",
              &FinalizeNumberedCommandCounter);
