//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A handler for the SHUTDOWN command. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_COMMON_SHUTDOWN_HANDLER_H_
#define CPP_BASELINE_COMMON_SHUTDOWN_HANDLER_H_

#include "baseline/common/extensible-ready-handler.h"

class NumberedCommandReceiver;
class EventLoop;

/// This is a root mode command used by both the TA1 client and server. When it
/// receives "SHUTDOWN" it waits for all pending commands to complete and then
/// calls exit() to shut down the binary.
class ShutdownHandler : public ProtocolExtension {
 public:
  /// Waits for all commands pending on reciever before calling exit.
  ShutdownHandler(NumberedCommandReceiver* receiver, EventLoop* event_loop)
      : receiver_(receiver), event_loop_(event_loop) {}
  virtual ~ShutdownHandler() {}

  virtual void OnProtocolStart(Knot start_line);
  virtual void LineReceived(Knot data);
  virtual void RawReceived(Knot data);

 private:
  NumberedCommandReceiver* receiver_;
  EventLoop* event_loop_;
};

#endif
