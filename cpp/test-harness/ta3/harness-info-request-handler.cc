//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of HarnessInfoRequestHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "harness-info-request-handler.h"

using std::string;

void HarnessInfoRequestHandler::Execute(LineRawData<Knot>* command_data) {
  LOG(DEBUG) << "Executing HarnessInfoRequestHandler";
  Knot harness_info(new string(*harness_id_ + " " + itoa(*num_suts_)));
  LineRawData<Knot> results;
  results.AddLine(harness_info);
  LOG(DEBUG) << "HarnessInfoRequestHandler writing results";
  WriteResults(results);
  LOG(DEBUG) << "HarnessInfoRequestHandler done writing results";
  delete command_data;
  Done();
}

HarnessInfoRequestHandler* HarnessInfoRequestHandlerFactory(
    string* harness_id, size_t* num_suts) {
  return new HarnessInfoRequestHandler(harness_id, num_suts);
}
