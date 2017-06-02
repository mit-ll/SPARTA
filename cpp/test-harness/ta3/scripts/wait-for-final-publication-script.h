//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Jan 2013   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_WAIT_FOR_FINAL_PUBLICATIONS_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_WAIT_FOR_FINAL_PUBLICATIONS_SCRIPT_H_

#include "test-harness/common/test-script.h"

#include "test-harness/ta3/publication-received-handler.h"
#include "common/check.h"

class GeneralLogger;

/// TODO(njhwang) create unit tests
class WaitForFinalPublicationScript : public TestScript {
 public:
  WaitForFinalPublicationScript(
      int timeout, PublicationReceivedHandler* pub_handler, 
      GeneralLogger* logger);

  virtual ~WaitForFinalPublicationScript() {};

  virtual void Run();

 private:
  int timeout_;
  PublicationReceivedHandler* pub_handler_;
  GeneralLogger* logger_;
};

#endif
