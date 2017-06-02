//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of CallRemoteScript. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#include <fstream>
#include <vector>

#include "call-remote-script.h"
#include "test-harness/ta3/master-harness-network-listener.h"
#include "common/safe-file-stream.h"
#include "common/general-logger.h"

using namespace std;

void CallRemoteScript::Run() {
  MasterHarnessProtocolStack* master_ps =
    listener_->GetProtocolStack(harness_id_); 
  THRunScriptCommand* run_script_command = master_ps->GetRunScriptCommand();
  THRunScriptCommand::ResultsFuture start_f, done_f;

  LOG(INFO) << "CallRemoteScript executing against slave harness "
            << harness_id_;
  logger_->Log("CallRemoteScript initiating call to slave harness "
               + harness_id_);
  run_script_command->SendRunScript(*command_data_, start_f, done_f);
  LOG(DEBUG) << "CallRemoteScript target scheduled for slave harness "
            << harness_id_;

  start_f.Wait();
  logger_->Log("Slave harness started remote script.");

  done_f.Wait();
  logger_->Log("Slave harness completed remote script.");
  logger_->Flush();
}

TestScript* CallRemoteScriptFileFactory::operator()(
    const string& config_line, const string& dir_path,
    GeneralLogger* logger) {
  CHECK(dir_path.empty() || dir_path.at(dir_path.size() - 1) == '/');
  size_t space1 = config_line.find_first_of(' ', 0);
  string harness_id = config_line.substr(0, space1);
  string file_name = config_line.substr(space1 + 1, string::npos);
  LOG(INFO) << "CallRemoteScript will have the contents of "
            << dir_path + file_name + " executed on slave "
            << "harness " << harness_id;
  SafeIFStream data_file(dir_path + file_name);
  CHECK(data_file.good()) << "Error opening remote script file: "
    << dir_path << file_name;
  LineRawData<Knot>* command_data = new LineRawData<Knot>;
  LineRawDataFromFile(&data_file, command_data);
  return new CallRemoteScript(harness_id, listener_, logger, command_data);  
}
