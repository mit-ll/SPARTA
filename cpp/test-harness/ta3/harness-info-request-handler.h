//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        A NumberedCommandHandler for harness info requests.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TA3_HARNESS_ID_REQUEST_HANDLER_H_
#define CPP_TA3_HARNESS_ID_REQUEST_HANDLER_H_

#include <string>

#include "baseline/common/numbered-command-receiver.h"

/// NumberedCommandHandler that writes harness info (the harness' ID and number
/// of SUTs the harness is driving, separated by a space) to the handler's
/// output.
class HarnessInfoRequestHandler : public NumberedCommandHandler {
 public:
  HarnessInfoRequestHandler(std::string* harness_id, size_t* num_suts) : 
    harness_id_(harness_id), num_suts_(num_suts) {}

  virtual ~HarnessInfoRequestHandler() {}

  virtual void Execute(LineRawData<Knot>* command);

 private:
  std::string* harness_id_;
  size_t* num_suts_;
};

HarnessInfoRequestHandler* 
  HarnessInfoRequestHandlerFactory(std::string* harness_id, size_t* num_suts);

#endif
