//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Abstract base class for a generic numbered command
//                     implementation.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************

#ifndef CPP_TEST_HARNESS_GENERIC_NUMBERED_COMMAND_H_
#define CPP_TEST_HARNESS_GENERIC_NUMBERED_COMMAND_H_

#include <string>

#include "test-harness/common/numbered-command-sender.h"
#include "common/general-logger.h"
#include "common/line-raw-data.h"

class EventMessageMonitor;

class GenericNumberedCommand {
 public:
  GenericNumberedCommand(std::string command_name, 
                         NumberedCommandSender* command_sender,
                         EventMessageMonitor* event_monitor = nullptr)
      : command_name_(command_name), command_sender_(command_sender),
        event_monitor_(event_monitor) {}

  /// Given data, this wraps it in a command and schedules it to be executed
  /// by a NumberedCommandSender. 
  ///
  /// The returned ResultsFuture will hold the data received from the SUT in its
  /// results_received field.
  NumberedCommandSender::ResultsFuture Schedule(const LineRawData<Knot>& data);

  /// The same as the above, but will also log when the command is sent and the
  /// results are received with the passed logger. Different subclasses may rely
  /// on data being in a certain format for this method to work properly. 
  NumberedCommandSender::ResultsFuture Schedule(const LineRawData<Knot>& data, 
                                                GeneralLogger* logger, 
                                                int local_id = -1,
                                                const std::string& desc = "");

  /// Returns command name string.
  std::string GetCommandName() {
      return command_name_;
  }

 protected:
  /// Builds the command syntax that will go between the COMMAND/ENDCOMMAND
  /// tokens. Subclasses must implement this method.
  virtual void GetCommand(const LineRawData<Knot>& data, Knot* output) = 0;

 private:
  /// Called when a command completes via a ResultsFuture and logs the command
  /// completion time if the Schedule(..., GeneralLogger*) method was used to
  /// schedule the command.
  static void LogResults(NumberedCommandSender::SharedResults result,
                         GeneralLogger* logger, int local_id = -1);
  /// Specifies command type for the command implementation. Subclasses should
  /// set this with the GenericNumberedCommand constructor.
  std::string command_name_;
  /// Sender responsible for writing commands whenever a ready signal is
  /// received.
  NumberedCommandSender* command_sender_;
  EventMessageMonitor* event_monitor_;
};

#endif
