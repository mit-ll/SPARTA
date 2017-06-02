//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implemenation of RootModeCommand.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************
#include "root-mode-commands.h"

#include <boost/bind.hpp>

#include "generic-log-message-formats.h"

using namespace std;

RootModeCommandSender::RootModeResultsFuture RootModeCommand::Schedule() {
  return command_sender_->SendCommand(command_name_);
}

RootModeCommandSender::RootModeResultsFuture RootModeCommand::Schedule(
    GeneralLogger* logger) {
  RootModeCommandSender::RootModeResultsFuture result =
      RootModeCommand::Schedule();
  logger->Log(RootCommandSentMessage(command_name_));
  result.AddCallback(
      boost::bind(&RootModeCommand::LogResults, command_name_, _1, logger));
  return result;
}

void RootModeCommand::LogResults(
    string command_name,
    RootModeCommandSender::SharedRootModeResults result,
    GeneralLogger* logger) {
  logger->Log(RootCommandCompleteMessage(command_name, *result));
}
