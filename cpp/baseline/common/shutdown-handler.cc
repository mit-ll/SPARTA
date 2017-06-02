//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ShutdownHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************

#include "shutdown-handler.h"

#include "baseline/common/numbered-command-receiver.h"
#include "common/event-loop.h"
#include "common/logging.h"

const int kStdInFD = 0;

void ShutdownHandler::OnProtocolStart(Knot start_line) {
  CHECK(start_line == "SHUTDOWN");
  if (receiver_->NumPendingCommands() > 0) {
    LOG(DEBUG) << "SHUTDOWN received but still some pending commands. "
        << "Waiting for " << receiver_->NumPendingCommands()
        << " to complete.";
  }
  receiver_->WaitForAllCommands();
  // Stop reading events from stdin, otherwise the event loop won't ever exit.
  event_loop_->RemoveFileDataCallback(kStdInFD);
  event_loop_->ExitLoop();
}

void ShutdownHandler::LineReceived(Knot data) {
  LOG(FATAL)
      << "ShutdownComand expects just a single line containining SHUTDOWN";
}

void ShutdownHandler::RawReceived(Knot data) {
  LOG(FATAL)
      << "ShutdownComand expects just a single line containining SHUTDOWN";
}
