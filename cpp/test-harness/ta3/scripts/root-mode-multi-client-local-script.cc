//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implmentation of RootModeMultiClientLocalScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "root-mode-multi-client-local-script.h"

#include <memory>

#include "test-harness/ta3/multi-client-sut-protocol-stack.h"
#include "test-harness/ta3/client-sut-protocol-stack.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/sut-running-monitor.h"
#include "common/general-logger.h"
#include "common/event-loop.h"

using std::string;

RootModeMultiClientLocalScript::RootModeMultiClientLocalScript(
    const string& command_string, MultiClientSUTProtocolStack* sut_protocols,
    GeneralLogger* logger, std::vector<SUTRunningMonitor*> sut_monitors)
    : command_string_(command_string), sut_protocols_(sut_protocols),
      logger_(logger), sut_monitors_(sut_monitors) {
}

void RootModeMultiClientLocalScript::Run() {
  LOG(INFO) << "Sending " << command_string_
            << " to all local SUTs";
  logger_->Log(string("Sending ") + command_string_ +
               " to all local SUTs");
  for (size_t i = 0; i < sut_protocols_->GetNumClientSUTs(); i++) {
    ClientSUTProtocolStack* client_protocols = 
      sut_protocols_->GetProtocolStack(i);
    RootModeCommandSender* command_sender = 
      client_protocols->GetRootModeCommandSender();
    LOG(INFO) << "Sending " << command_string_
              << " to SUT " << itoa(i);
    logger_->Log(string("Sending ") + command_string_ +
                 " to SUT " + itoa(i));
    if (command_string_ == "SHUTDOWN") {
      LOG(INFO) << "RootModeLocalScript encountered SHUTDOWN; expecting EOF";
      sut_monitors_[i]->SetShutdownExpected(true);
      logger_->Flush();
    }
    RootModeCommandSender::RootModeResultsFuture f =
        command_sender->SendCommand(command_string_);
    // TODO(odain) This is kind of hacky. There should probably be a separate
    // shutdown script, but this is *much* easier and much less code...
    if (command_string_ == "SHUTDOWN") {
      sut_monitors_[i]->WaitForShutdown();
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
    LOG(INFO) << command_string_ << " on the local SUT complete.";
    logger_->Log(command_string_ + " on the local SUT complete.");
  }
  logger_->Flush();
}
