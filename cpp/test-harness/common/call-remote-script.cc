//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of CallRemoteScript. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Nov 2012   omd            Original Version
//*****************************************************************

#include "call-remote-script.h"

#include <fstream>

#include "th-run-script-command.h"
#include "common/general-logger.h"

CallRemoteScript::CallRemoteScript(
    THRunScriptCommand* run_script_command, GeneralLogger* logger,
    LineRawData<Knot>* command_data)
    : run_script_command_(run_script_command), logger_(logger),
      command_data_(command_data) {
}

void CallRemoteScript::Run() {
  THRunScriptCommand::ResultsFuture start_f, done_f;

  logger_->Log("Initiating call to remote server");
  run_script_command_->SendRunScript(*command_data_, start_f, done_f);

  start_f.Wait();
  logger_->Log("Remote script started.");

  done_f.Wait();
  logger_->Log("Remote script complete.");
  logger_->Flush();
}


TestScript* CallRemoteScriptFileFactory::operator()(
    const std::string& config_line, const std::string& dir_path,
    GeneralLogger* logger) {
  CHECK(dir_path.empty() || dir_path.at(dir_path.size() - 1) == '/');
  std::ifstream data_file(dir_path + config_line);
  CHECK(data_file.good()) << "Error opening remote script file: "
    << dir_path << "/" << config_line;
  LineRawData<Knot>* command_data = new LineRawData<Knot>;
  LineRawDataFromFile(&data_file, command_data);
  return new CallRemoteScript(run_script_command_, logger, command_data);  
}
