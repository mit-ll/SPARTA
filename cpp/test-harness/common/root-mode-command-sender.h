//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        For handling root mode commands.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_ROOT_MODE_COMMAND_SENDER_H_
#define CPP_TEST_HARNESS_COMMON_ROOT_MODE_COMMAND_SENDER_H_

#include <functional>
#include <string>
#include <memory>
#include <thread>

#include "common/future.h"
#include "common/knot.h"
#include "common/line-raw-data.h"
#include "common/protocol-extension-manager.h"

class ReadyMonitor;

/// An extension for handling root mode commands and results. Root mode commands
/// will either have no results expected or only expect a single "DONE" message,
/// and this sender contains enough information to handle incoming tokens as
/// required for each root mode command. This removes the need to create separate
/// 'senders' for each root mode command.
class RootModeCommandSender : public ProtocolExtension {
 public:
  RootModeCommandSender(ReadyMonitor* ready_monitor);
  virtual ~RootModeCommandSender() {}

  /// The type of data each future should return.
  typedef std::shared_ptr<LineRawData<Knot> > SharedRootModeResults;
  /// The type of future this sender returns.
  typedef Future<SharedRootModeResults> RootModeResultsFuture;
  /// The type of callback used to act upon received results.
  typedef std::function<void (SharedRootModeResults)> RootModeResultsCallback;
 
  /// Schedule the given command as soon as the SUT is in the ready state.
  /// pending_callback_ will be called if a DONE message is received. 
  RootModeResultsFuture SendCommand(std::string command_name);

  /// This sender only processes incoming tokens in this method, as root mode
  /// commands should receive at most a single line of results. This method will
  /// handle each type of root mode command as required, and will either look for
  /// a "DONE" message or immediately complete if no "DONE" message is required.
  virtual void OnProtocolStart(Knot start_line);
  /// This method should never be reached when processing root mode commands.
  virtual void LineReceived(Knot line);
  /// This method should never be reached when processing root mode commands.
  virtual void RawReceived(Knot data); 

 private:
  /// Ready monitor for this sender.
  ReadyMonitor* ready_monitor_;
  /// Future to be fired when results are received.
  RootModeResultsFuture future_;
  /// Used to synchronize access between SendCommand and OnProtocolStart. There
  /// is a race condition that appears if a recipient detects and responds to a
  /// root command via OnProtocolStart before SendCommand can return a valid
  /// future. This mutex ensures that does not happen.
  std::mutex data_tex_;
};

#endif
