//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of RootModeLocalScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 06 Nov 2012   omd            Original Version
//*****************************************************************

#include "root-mode-local-script.h"

#include <memory>

#include "root-mode-command-sender.h"
#include "th-run-script-command.h"
#include "sut-running-monitor.h"
#include "common/general-logger.h"

using std::string;

RootModeLocalScript::RootModeLocalScript(
    const string& command_string, RootModeCommandSender* command_sender,
    SUTRunningMonitor* sut_running, GeneralLogger* logger)
    : command_string_(command_string), command_sender_(command_sender),
      sut_running_monitor_(sut_running), logger_(logger) {
}

void RootModeLocalScript::Run() {
  logger_->Log(string("Sending ") + command_string_ +
               " to local SUT");
  if (command_string_ == "SHUTDOWN") {
    sut_running_monitor_->SetShutdownExpected(true);
  }
  RootModeCommandSender::RootModeResultsFuture f =
      command_sender_->SendCommand(command_string_);
  // TODO(odain) This is kind of hacky. There should probably be a separate
  // shutdown script, but this is *much* easier and much less code...
  if (command_string_ == "SHUTDOWN") {
    sut_running_monitor_->WaitForShutdown();
    std::shared_ptr<LineRawData<Knot> > fake_result(
        new LineRawData<Knot>);
    fake_result->AddLine(Knot(new string("DONE")));
    f.Fire(fake_result);
  } else {
    const LineRawData<Knot>* from_client = f.Value().get();
    if (from_client->Size() != 1 || from_client->Get(0) != "DONE") {
      LOG(FATAL) << "Error executing root mode comand locally. Command: "
          << command_string_ << ". Error:\n"
          << from_client->LineRawOutput().ToString();
    }
  }
  logger_->Log(command_string_ + " on the local SUT complete.");

}
