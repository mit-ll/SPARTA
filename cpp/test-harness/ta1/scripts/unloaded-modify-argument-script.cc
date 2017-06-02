//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of UnloadedModifyArgumentScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************

#include "unloaded-modify-argument-script.h"

#include "test-harness/common/generic-numbered-command.h"
#include "test-harness/common/numbered-command-sender.h"
#include "common/future.h"

UnloadedModifyArgumentScript::UnloadedModifyArgumentScript(
    InsertCommand* insert_command, UpdateCommand* update_command,
    DeleteCommand* delete_command, GeneralLogger* logger,
    const LineRawData<Knot>& command_data)
    : ModifyArgumentScript(insert_command, update_command,
                           delete_command, logger) {
  LOG(INFO) << "Starting UnloadedModifyArgumentScript";

  size_t cur_idx = 0;
  ParseCommandModID(command_data);
  ++cur_idx;

  ParseCommandData(cur_idx, command_data);
}

void UnloadedModifyArgumentScript::Run() {
  for (int command = 0; command < NumCommands(); ++command) {
    std::string desc_message = 
      GetCommandDescMessage(command,
			    GetCommandHandler(command)->GetCommandName());
    NumberedCommandSender::ResultsFuture cf =
        GetCommandHandler(command)->Schedule(*GetCommandData(command), 
					     GetLogger(), command, 
					     desc_message);
    cf.Wait();
  }
  logger_->Flush();
}
