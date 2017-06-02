//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Base class for things that manage the sending of numbered
//                     commands and the receiving of the associated results. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_NUMBERED_COMMAND_SENDER_BASE_H_
#define CPP_TEST_HARNESS_COMMON_NUMBERED_COMMAND_SENDER_BASE_H_

#include <functional>

#include "common/protocol-extension-manager.h"
#include "common/knot.h"

class EventMessageMonitor;
class ReadyMonitor;

/// Base class from which all NumberedCommand sending things are derived. This
/// doesn't do a whole lot since the subclasses are fairly different. However, it
/// does handle a part of the protocol parsing and sending and the assignment of
/// unique command id's to all subclasses. Subclasses need only implement
/// OnProtocolStartImpl, LineReceivedImpl, RawReceivedImpl, and ResultsDone.
class NumberedCommandSenderBase : public ProtocolExtension {
 public:
  NumberedCommandSenderBase(ReadyMonitor* ready_monitor,
                            EventMessageMonitor* event_monitor = nullptr)
      : ready_monitor_(ready_monitor),
        event_monitor_(event_monitor) {}
  virtual ~NumberedCommandSenderBase() {}

  virtual void OnProtocolStart(Knot start_line);
  virtual void LineReceived(Knot line);
  virtual void RawReceived(Knot data) {
   RawReceivedImpl(data);
  } 

 protected:
  /// Atomically increments the command id counter and returns the next command
  /// number. All subclasses *must* use this to get command id's in order to
  /// ensure they remain unique.
  int GetNextCommandId();
  /// Callback function that takes a int, the command id. Will be called when the
  /// data is actually sent (as opposed to when it gets queued but is still
  /// waiting for the READY signal).
  typedef std::function<void (int, int, Knot)> EventCallback;
  typedef std::function<void (int)> SentCallback;
  /// Send the data, wrapped in a COMMAND/ENDCOMMAND pair and return the
  /// command_id assigned. Call SentCallback when the READY signal is received
  /// and the data is actually sent.
  int Send(Knot data, 
           SentCallback cb = nullptr, 
           EventCallback eb = nullptr);

  /// All subclasses must override the following methods

  /// This is called when a RESULTS line is received from the SUT. The command_id
  /// is the id number that came after RESULTS in the received data.
  virtual void OnProtocolStartImpl(int command_id) = 0;
  /// Called when a new line of data is received *unless* that line is
  /// 'ENDRESULTS' in which case ResultsDone is called.
  virtual void LineReceivedImpl(Knot line) = 0;
  /// Called when raw data is received.
  virtual void RawReceivedImpl(Knot data) = 0;
  /// Called when ENDRESULTS is received.
  virtual void ResultsDone() = 0;

  static const char kCommandHeader[];
  static const int kCommandHeaderLen;

  static const char kCommandEnd[];
  static const int kCommandEndLen;

  static const char kResultsHeader[];
  static const int kResultsHeaderLen;
  static const char kResultsEnd[];
  static const int kResultsEndLen;

 private:
  ReadyMonitor* ready_monitor_;
  EventMessageMonitor* event_monitor_;
};

#endif
