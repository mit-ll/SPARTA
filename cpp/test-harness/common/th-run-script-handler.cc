//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of THRunScriptHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 20 Sep 2012   omd            Original Version
//*****************************************************************

#include "th-run-script-handler.h"

#include <string>

#include "script-manager.h"
#include "th-run-script-command.h"

using std::string;

NumberedCommandHandler* ConstructTHRunScriptHandler(ScriptManager* manager) {
  return new THRunScriptHandler(manager);
}

THRunScriptHandler::THRunScriptHandler(ScriptManager* manager)
    : script_manager_(manager) {
}


void THRunScriptHandler::Execute(LineRawData<Knot>* command_data) {
  // Should be RUNSCRIPT, the script name, some optional arguments and then
  // ENDRUNSCRIPT so at least 3 lines.
  DCHECK(command_data->Size() >= 3);
  CHECK(command_data->Get(0) == "RUNSCRIPT");
  CHECK(command_data->Get(command_data->Size() - 1) == "ENDRUNSCRIPT");


  string script_name(command_data->Get(1).ToString());
  command_data->SetStartOffset(2);
  command_data->SetEndOffset(1);

  if (command_data->Size() > 0) {
    script_ = script_manager_->GetScript(script_name, *command_data);
  } else {
    script_ = script_manager_->GetScript(script_name);
  }

  Future<bool> run_result = script_->RunInThread();
  run_result.AddCallback(
      boost::bind(&THRunScriptHandler::ScriptComplete, this, _1));

  WriteResults(THRunScriptCommand::kStartedToken);

  delete command_data;
}

void THRunScriptHandler::ScriptComplete(bool result) {
  WriteResults(THRunScriptCommand::kFinishedToken);
  Done();
}
