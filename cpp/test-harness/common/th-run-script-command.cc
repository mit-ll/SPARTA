//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of THRunScriptCommand 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Sep 2012   omd            Original Version
//*****************************************************************

#include "th-run-script-command.h"

#include <boost/bind.hpp>
#include <cstring>

const char* THRunScriptCommand::kCommandHeader = "RUNSCRIPT\n";
const int THRunScriptCommand::kCommandHeaderLen = strlen(kCommandHeader);

const char* THRunScriptCommand::kCommandFooter = "ENDRUNSCRIPT\n";
const int THRunScriptCommand::kCommandFooterLen = strlen(kCommandFooter);

const char* THRunScriptCommand::kStartedToken = "STARTED\n";
const int THRunScriptCommand::kStartedTokenLen = strlen(kStartedToken);

const char* THRunScriptCommand::kFinishedToken = "FINISHED\n";
const int THRunScriptCommand::kFinishedTokenLen = strlen(kFinishedToken);

THRunScriptCommand::THRunScriptCommand(
    MultiNumberedCommandSender* nc_extension)
  : nc_extension_(nc_extension) {
}

void THRunScriptCommand::SendRunScript(
      const LineRawData<Knot>& command_data,
      ResultsFuture command_start_future,
      ResultsFuture command_complete_future) {
  Knot command;

  command.AppendOwned(kCommandHeader, kCommandHeaderLen);
  command_data.AppendLineRawOutput(&command);
  command.AppendOwned(kCommandFooter, kCommandFooterLen);

  int command_id;
  LOG(DEBUG) << "THRunScriptCommand scheduling command";
  nc_extension_->SendCommand(
      command,
      boost::bind(&THRunScriptCommand::ResultsForCommand, this, _1,
                  command_start_future, command_complete_future),
      &command_id);
  LOG(DEBUG) << "THRunScriptCommand scheduled command";
}

void THRunScriptCommand::ResultsForCommand(
      MultiNumberedCommandSender::SharedResults results,
      ResultsFuture command_start_future,
      ResultsFuture command_complete_future) {
  CHECK(results->results_received.Size() > 0);
  CHECK(!results->results_received.IsRaw(0));

  // We subtract 1 from the length here as the token won't have the final '\n'.
  if (results->results_received.Get(0).Equal(
          kStartedToken, kStartedTokenLen - 1)) {
    DCHECK(!command_start_future.HasFired());
    command_start_future.Fire(results);
  } else {
    // We subtract 1 from the length here as the token won't have a '\n'.
    CHECK(results->results_received.Get(0).Equal(
            kFinishedToken, kFinishedTokenLen - 1))
        << "Unexpected results: "
        << results->results_received.Get(0);

    LOG(DEBUG) << "THRunScriptCommand calling RemoveCallback for: "
        << results->command_id;
    nc_extension_->RemoveCallback(results->command_id);
    DCHECK(!command_complete_future.HasFired());
    command_complete_future.Fire(results);
  }
}
