//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
//*****************************************************************

#include "root-mode-master-script.h"

#include "common/general-logger.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/th-run-script-command.h"

using std::string;

RootModeMasterScript::RootModeMasterScript(
    const std::string& command_string, RootModeCommandSender* command_sender,
    SUTRunningMonitor* sut_monitor,
    THRunScriptCommand* run_script_command, GeneralLogger* logger)
    : RootModeLocalScript(command_string, command_sender, sut_monitor, logger),
      run_script_command_(run_script_command) {
}

void RootModeMasterScript::Run() {
  THRunScriptCommand::ResultsFuture start_f, done_f;
  logger_->Log(string("Calling ") + command_string_ +
               " on the server");
  LineRawData<Knot> command_data;
  const char kRootModeLocalScriptName[] = "RootModeLocalScript";
  const int kRootModeLocalScriptNameLen = strlen(kRootModeLocalScriptName);
  Knot root_mode_local_script_name;
  root_mode_local_script_name.AppendOwned(kRootModeLocalScriptName,
                                          kRootModeLocalScriptNameLen);
  command_data.AddLine(root_mode_local_script_name);
  command_data.AddLine(Knot(new string(command_string_)));
  LOG(INFO) << "Sending " << kRootModeLocalScriptName
      << " to the server harness";
  run_script_command_->SendRunScript(command_data, start_f, done_f);
  done_f.Wait();
  LOG(INFO) << "Server harness done executing " << kRootModeLocalScriptName;

  const LineRawData<Knot>* from_server = &done_f.Value()->results_received;
  if (from_server->Size() != 1 || from_server->Get(0) != "FINISHED") {
    LOG(FATAL) << "Error executing root mode command on server. Command: "
       << command_string_ << ". Error:\n"
       << from_server->LineRawOutput().ToString();
  }
  logger_->Log(command_string_ + " on server complete.");

  RootModeLocalScript::Run();
  logger_->Flush();
}
