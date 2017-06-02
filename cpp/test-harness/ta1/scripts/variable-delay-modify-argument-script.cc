//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************

#include "variable-delay-modify-argument-script.h"

#include <boost/thread.hpp>
#include <cstring>

#include "test-harness/common/generic-numbered-command.h"
#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/common/delay-generators.h"
#include "common/future-waiter.h"

VariableDelayModifyArgumentScript::VariableDelayModifyArgumentScript(
    InsertCommand* insert_command, UpdateCommand* update_command,
    DeleteCommand* delete_command, GeneralLogger* logger,
    const LineRawData<Knot>& command_data)
    : ModifyArgumentScript(insert_command, update_command,
                           delete_command, logger) {
  LOG(INFO) << "Starting VariableDelayModifyArgumentScript";
  size_t cur_idx = 0;
  ParseCommandModID(command_data);
  ++cur_idx;

  CHECK(cur_idx < command_data.Size());
  CHECK(!command_data.IsRaw(cur_idx));
  if (command_data.Get(cur_idx) == "NO_DELAY") {
    delay_function_ = &ZeroDelay;
  } else {
    CHECK(command_data.Get(cur_idx) == "EXPONENTIAL_DELAY");
    ++cur_idx;
    CHECK(cur_idx < command_data.Size());
    CHECK(!command_data.IsRaw(cur_idx));
    int mean_delay_us = atoi(command_data.Get(cur_idx).ToString().c_str());
    // Fixed seed of 0 for repeatability
    delay_function_ = ExponentialDelayFunctor(mean_delay_us, 0);
  }

  ParseCommandData(cur_idx + 1, command_data);
}

void VariableDelayModifyArgumentScript::Run() {
  FutureWaiter<NumberedCommandSender::SharedResults> waiter;
  for (int command = 0; command < NumCommands(); ++command) {
    std::string desc_message = 
      GetCommandDescMessage(command,
			    GetCommandHandler(command)->GetCommandName());
    waiter.Add(GetCommandHandler(command)->Schedule(*GetCommandData(command),
						    GetLogger(),
						    command, desc_message));
    int delay_us = delay_function_();
    if (delay_us > 0) {
      boost::this_thread::sleep(boost::posix_time::microseconds(delay_us));
    }
  }

  waiter.Wait();
  LOG(INFO) << "Finished VariableDelayModifyArgumentScript";
  logger_->Flush();
}
