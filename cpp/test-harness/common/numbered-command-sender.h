//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        For handling numbered commands. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Aug 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_NUMBERED_COMMAND_SENDER_H_
#define CPP_TEST_HARNESS_COMMON_NUMBERED_COMMAND_SENDER_H_

#include <memory>
#include <functional>

#include "multi-numbered-command-sender.h"
#include "common/future.h"

class EventMessageMonitor;
class ReadyMonitor;

/// The standard numbered command/numbered results protocol as described in the
/// test plan.
class NumberedCommandSender : public MultiNumberedCommandSender {
 public:
  NumberedCommandSender(ReadyMonitor* ready_monitor,
                        EventMessageMonitor* event_monitor = nullptr);
  virtual ~NumberedCommandSender() {}
  
  typedef std::shared_ptr<NumberedCommandResult> SharedResults;
  typedef std::function<void (int, int, Knot)> EventCallback;
  typedef std::function<void (int)> SentCallback;
  /// The type of future this returns.
  typedef Future<SharedResults> ResultsFuture;
  /// Schedule the given data to be sent as a numbered command as soon as the
  /// SUT is in the ready state. The returned future will fire when the SUT
  /// sends a corresponding RESULTS message.
  ResultsFuture SendCommand(Knot data);

  /// Same as the above but also fills in command_id with the id of the command
  /// number that was sent and allows for the definition of a callback function
  /// to be called when the command is sent.
  ResultsFuture SendCommand(Knot data, 
                            int* command_id, 
                            SentCallback sb = nullptr,
                            EventCallback eb = nullptr);

 private:
  void ResultsAvailable(SharedResults results,
                        ResultsFuture future);
};
#endif
