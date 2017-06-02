//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class for sending RUNSCRIPT commands to other test
//                     harness components. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_TH_RUN_SCRIPT_COMMAND_H_
#define CPP_TEST_HARNESS_COMMON_TH_RUN_SCRIPT_COMMAND_H_

#include "common/future.h"
#include "multi-numbered-command-sender.h"

class MultiNumberedCommandSender;
class Knot;
template<class T> class LineRawData;

class THRunScriptCommand {
 public:
  THRunScriptCommand(MultiNumberedCommandSender* nc_extension);
  virtual ~THRunScriptCommand() {}

  typedef Future<MultiNumberedCommandSender::SharedResults>
      ResultsFuture;

  /// Send command_data (the first element of which should be a command name
  /// and the rest of which is parameters for that command) to the remote end
  /// of the connection. When the remote end indicates that it has started
  /// executing the given script fire the first future. When the command
  /// completes, fire the 2nd one.
  void SendRunScript(
      const LineRawData<Knot>& command_data,
      ResultsFuture command_start_future,
      ResultsFuture command_complete_future);

  /// Defined here so THRunScriptHandler can be sure to use the same strings.
  static const char* kCommandHeader;
  static const int kCommandHeaderLen;
  static const char* kCommandFooter;
  static const int kCommandFooterLen;
  static const char* kStartedToken;
  static const int kStartedTokenLen;
  static const char* kFinishedToken;
  static const int kFinishedTokenLen;

 private:
  void ResultsForCommand(
      MultiNumberedCommandSender::SharedResults results,
      ResultsFuture command_start_future,
      ResultsFuture command_complete_future);

  MultiNumberedCommandSender* nc_extension_;
};

#endif
