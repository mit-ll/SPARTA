//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Defines a base class and some subclasses for common root
//                     mode commands.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************

#ifndef CPP_TEST_HARNESS_ROOT_MODE_COMMAND_H_
#define CPP_TEST_HARNESS_ROOT_MODE_COMMAND_H_

#include <string>

#include "common/general-logger.h"
#include "test-harness/common/root-mode-command-sender.h"

/// A base class for root mode commands (commands that are *not* sent between
/// COMMAND n/ENDCOMMAND pairs). This class is used for defining root mode
/// commands that the test harness can send to the SUT.
class RootModeCommand {
 public:
  RootModeCommand(RootModeCommandSender* command_sender, 
                  std::string command_name)
      : command_sender_(command_sender), command_name_(command_name) {}

  /// Sends the command and schedules it to be executed by a
  /// RootModeCommandSender.
  ///
  /// The returned RootModeResultsFuture will hold the data received from the
  /// SUT.
  RootModeCommandSender::RootModeResultsFuture Schedule();
  /// The same as the above, but will also log when the command is sent and the
  /// results are received with the passed logger. 
  RootModeCommandSender::RootModeResultsFuture Schedule(GeneralLogger* logger);

 private:
  /// Called when command results are received if Schedule(GeneralLogger*) was
  /// used to schedule the command.
  static void LogResults(std::string command_name,
                         RootModeCommandSender::SharedRootModeResults results, 
                         GeneralLogger* logger);
  /// Sender responsible for writing commands whenever a ready signal is
  /// received.
  RootModeCommandSender* command_sender_;
  /// Name of command this instance implements.
  std::string command_name_;
};

class ClearcacheCommand : public RootModeCommand {
 public:
  ClearcacheCommand(RootModeCommandSender* command_sender)
      : RootModeCommand(command_sender, "CLEARCACHE") {}
};

class ShutdownCommand : public RootModeCommand {
 public:
  ShutdownCommand(RootModeCommandSender* command_sender)
      : RootModeCommand(command_sender, "SHUTDOWN") {}
};

#endif
