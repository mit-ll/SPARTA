//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        For handling numbered commands that can have multiple
//                     results.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Aug 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_MULTI_NUMBERED_COMMAND_SENDER_H_
#define CPP_TEST_HARNESS_COMMON_MULTI_NUMBERED_COMMAND_SENDER_H_

#include <functional>
#include <memory>
#include <thread>

#include "numbered-command-sender-base.h"
#include "common/line-raw-data.h"
#include "common/knot.h"

class EventMessageMonitor;
class ReadyMonitor;

/// Indicates the results of a command.
struct NumberedCommandResult {
  /// The id of the command that caused these results
  int command_id;
  /// The results sent to the test harness by the SUT.
  LineRawData<Knot> results_received;
};

/// An extension for handling numbered commands and results. Unlike the version
/// described in the test plan and used to communicate commands from the test
/// harness to the SUT, this protocol allows for multiple results for each
/// command. This is useful for having multiple test harness components
/// collaborate over the network. For example, harness 1 might ask harness 2 to
/// run a command. In response it gets one results saying the command has
/// started, another results saying the command is 1/2 done, and a final set of
/// results indicating the command is complete (at which point RemoveCallback()
/// should be called).
///
/// For the more standard numbered command protocol see
/// NumberedCommandSender.
class MultiNumberedCommandSender : public NumberedCommandSenderBase {
 public:
  MultiNumberedCommandSender(ReadyMonitor* ready_monitor,
                             EventMessageMonitor* event_monitor = nullptr);
  virtual ~MultiNumberedCommandSender();
  
  typedef std::shared_ptr<NumberedCommandResult> SharedResults;
  typedef std::function<void (int, int, Knot)> EventCallback;
  typedef std::function<void (SharedResults)> ResultCallback;
  typedef std::function<void (int)> SentCallback;
  /// Schedule the given data to be sent as a numbered command as soon as the SUT
  /// is in the ready state. The sent callback will be called when the command is
  /// sent. The result callback will be called each time we get a RESULTS message
  /// with the corresponding number. On return command_id will be the id number
  /// of the command that was sent. The event callback will be called each time
  /// we get an EVENTMSG message with the corresponding number.
  void SendCommand(Knot data, ResultCallback cb, int* command_id, 
                   SentCallback sb = nullptr, EventCallback eb = nullptr);

  /// Users should call this when the command is complete. This removes the
  /// callback so we no longer expect to receive results for command_id. Note
  /// that it is an error if this is destroyed and there are outstanding
  /// commands that have not had RemoveCallback called.
  void RemoveCallback(int command_id);

 protected:
  virtual void OnProtocolStartImpl(int command_id);
  virtual void LineReceivedImpl(Knot line);
  virtual void RawReceivedImpl(Knot data); 
  virtual void ResultsDone();

 private:
  /// Guards the two variables that come after it. SendCommand can be called
  /// from multiple threads and the OnProtocolStart, LineReceived, RawReceived,
  /// and RemoveCallback methods can all be called from threads other than the
  /// thread calling SendCommand (but OnProtocolStart, LineReceived, and
  /// RawReceived will always be called from the same thread as each other and
  /// in the correct order.)
  std::mutex data_tex_;
  std::map<int, ResultCallback > pending_callbacks_;

  /// Holds the results for a command until we get ENDRESULTS
  SharedResults cur_results_data_;
};
#endif
