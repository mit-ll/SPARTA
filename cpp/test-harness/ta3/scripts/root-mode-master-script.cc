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

#include <vector>
#include <boost/thread.hpp>

#include "test-harness/ta3/master-harness-network-listener.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "common/general-logger.h"

using namespace std;

RootModeMasterScript::RootModeMasterScript(
    const std::string& command_string, RootModeCommandSender* command_sender,
    SUTRunningMonitor* sut_monitor,
    MasterHarnessNetworkListener* listener, GeneralLogger* logger)
    : RootModeLocalScript(command_string, command_sender, sut_monitor, logger),
      listener_(listener) {
}

void RootModeMasterScript::Run() {
  LOG(INFO) << "Calling " << command_string_ << " on all clients";
  logger_->Log(string("RootModeMasterScript calling ") + command_string_ +
               " on all clients");
  vector<string> slave_harness_ids = 
    *(listener_->GetAllSlaveHarnessIDs());
  vector<THRunScriptCommand::ResultsFuture> slave_done_fs;
  for (size_t i = 0; i < slave_harness_ids.size(); i++) {
    MasterHarnessProtocolStack* master_ps = 
      listener_->GetProtocolStack(slave_harness_ids[i]);
    THRunScriptCommand* run_script_command = master_ps->GetRunScriptCommand();
    THRunScriptCommand::ResultsFuture start_f, done_f;
    LOG(INFO) << "Calling " << command_string_ << " on all SUTs for "
              << "slave harness " << slave_harness_ids[i];
    logger_->Log(string("Requesting ") + command_string_ + " be executed"
                 " on all SUTs driven by slave harness " + 
                 slave_harness_ids[i]);
    LineRawData<Knot> command_data;
    const char kRootModeLocalScriptName[] = "RootModeMultiClientLocalScript";
    const int kRootModeLocalScriptNameLen = strlen(kRootModeLocalScriptName);
    Knot root_mode_local_script_name;
    root_mode_local_script_name.AppendOwned(kRootModeLocalScriptName,
                                            kRootModeLocalScriptNameLen);
    command_data.AddLine(root_mode_local_script_name);
    command_data.AddLine(Knot(new string(command_string_)));
    run_script_command->SendRunScript(command_data, start_f, done_f);
    start_f.Wait();
    slave_done_fs.push_back(done_f);
  }

  RootModeLocalScript::Run();

  for (size_t i = 0; i < slave_harness_ids.size(); i++) {
    slave_done_fs[i].Wait();

    const LineRawData<Knot>* from_server = 
      &slave_done_fs[i].Value()->results_received;
    if (from_server->Size() != 1 || from_server->Get(0) != "FINISHED") {
      LOG(FATAL) << "Error executing root mode commands on slave harness " +
                    slave_harness_ids[i] + ". Command: " << command_string_ << 
                    ". Error:\n" << from_server->LineRawOutput().ToString();
    }
    LOG(INFO) << command_string_ << " on all SUTs driven by slave harness "
              << slave_harness_ids[i] << " completed.";
    logger_->Log(command_string_ + " on all SUTs driven by slave harness " + 
                 slave_harness_ids[i] + " completed.");
  }
  logger_->Flush();
}
