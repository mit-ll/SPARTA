//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class for running a script when the RUNSCRIPT command
//                     is received.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 20 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_TH_RUN_SCRIPT_HANDLER_H_
#define CPP_TEST_HARNESS_COMMON_TH_RUN_SCRIPT_HANDLER_H_

#include <memory>

#include "baseline/common/numbered-command-receiver.h"
#include "test-script.h"

class ScriptManager;

/// To be used with a NumberedCommandReceiver we'll need a factory function. That
/// function is defined here (though the ScriptManager will have to be bound to
/// it via boost::bind before it can be passed to
/// NumberedCommandReceiver::AddHandler).
NumberedCommandHandler* ConstructTHRunScriptHandler(ScriptManager* manager);

/// Recieves RUNSCRIPT commands from another test harness component and runs the
/// specified script.
class THRunScriptHandler : public NumberedCommandHandler {
 public:
  /// Does not take ownership of manager.
  THRunScriptHandler(ScriptManager* manager);
  virtual ~THRunScriptHandler() {}

  virtual void Execute(LineRawData<Knot>* command_data);

 private:
  /// Called when the script completes. This sends the FINISHED token and calls
  /// Done().
  void ScriptComplete(bool result);

  ScriptManager* script_manager_;
  std::auto_ptr<TestScript> script_;
};


#endif
