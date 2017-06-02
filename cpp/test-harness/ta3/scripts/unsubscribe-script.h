//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        A script for sending unsubscription requests to clients
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_UNSUBSCRIBE_SCRIPT_H_
#define CPP_TEST_HARNESS_TA3_UNSUBSCRIBE_SCRIPT_H_

#include "test-harness/common/test-script.h"

#include <vector>

#include "common/line-raw-data.h"
#include "common/knot.h"

class MultiClientSUTProtocolStack;
class GeneralLogger;

class UnsubscribeScript : public TestScript {
 public:
  UnsubscribeScript(
      LineRawData<Knot> command_data,
      MultiClientSUTProtocolStack* protocol_stack, 
      GeneralLogger* logger);

  virtual ~UnsubscribeScript();

  virtual void Run();

 private:
  void ParseUnsubscribeSequence(LineRawData<Knot> command_data);

  void LogUnsubscribeCommandStatus(
      size_t command_id, size_t sut_id, const char* state);

  MultiClientSUTProtocolStack* protocol_stack_;
  GeneralLogger* logger_;

  std::vector<LineRawData<Knot>*> commands_;
  std::vector<size_t*> sut_ids_;
};

/// A factory for use with ScriptsFromFile. Expects a line containing, in order,
/// the query_modify_pairs file, the background_queries file, and the delay
/// paramters (as per VariableDelayQueryScript).
class UnsubscribeScriptFactory {
 public:
  UnsubscribeScriptFactory(
      MultiClientSUTProtocolStack* protocol_stack, GeneralLogger* logger);

  TestScript* operator()(const LineRawData<Knot>& command_data);

 private:
  MultiClientSUTProtocolStack* protocol_stack_;
  GeneralLogger* logger_;
};

#endif
