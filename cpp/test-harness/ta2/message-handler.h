//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Base class for message handlers 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 Nov 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA2_MESSAGE_HANDLER_H_
#define CPP_TEST_HARNESS_TA2_MESSAGE_HANDLER_H_

#include <iostream>
#include "stream-util.h"
#include "common/check.h"
#include "common/timer.h"

// MessageHandler is the base class for KeyMessageHandler,
// CircuitMessageHandler, and InputMessageHandler. It contains the pointers to
// the stdin and stdout pipes to the SUT client and server. It also holds the
// pointer to the result log and the timer.
//
// At initialization, the pointer to the result log is passed to the
// constructor, but the TestHarnessXStream pointers are null. After TestScript
// spawns the SUT server and client and establishes the TestHarnessXStream
// objects, it will set them. You should *not* call Send() before setting the
// TestHarnessXStreams.
//
// Subclasses need to implement the Send() method, which takes an input stream
// containing the data to be sent to either the SUT client or server.
class MessageHandler {
 public:
  // Constructor takes as input a ostream pointer to the result log. Performance
  // and output data will be recorded to this log.
  MessageHandler(std::ostream* log) 
      : client_stdin_(nullptr), client_stdout_(nullptr),
      server_stdin_(nullptr), server_stdout_(nullptr), log_(log), timer_() {
    CHECK(log != nullptr) << "Initializing MessageHandler with null log";
  }

  // Send must implement the specific protocol for either key-exchange, circuit
  // ingestion, or evaluation. Subclasses are responsible for writing the the
  // result log and keeping track of timing information using the timer provided
  // in this class.
  virtual void Send(std::istream* s) = 0;

  // The TestHarnessXStreams are not available at the time of construction of
  // the MessageHandlers. The necessary setters must be called prior to calling 
  // Send().
  inline void set_client_stdin(TestHarnessOStream* client_stdin) {
    client_stdin_ = client_stdin;
  }

  inline void set_client_stdout(TestHarnessIStream* client_stdout) {
    client_stdout_ = client_stdout;
  }

  inline void set_server_stdin(TestHarnessOStream* server_stdin) {
    server_stdin_ = server_stdin;
  }

  inline void set_server_stdout(TestHarnessIStream* server_stdout) {
    server_stdout_ = server_stdout;
  }

  inline TestHarnessOStream* client_stdin() {
    return client_stdin_;
  }

  inline TestHarnessIStream* client_stdout() {
    return client_stdout_;
  }

  inline TestHarnessOStream* server_stdin() {
    return server_stdin_;
  }

  inline TestHarnessIStream* server_stdout() {
    return server_stdout_;
  }

  inline Timer& timer() {
    return timer_;
  }

  inline std::ostream* log() {
    return log_;
  }

 private:
  TestHarnessOStream* client_stdin_;
  TestHarnessIStream* client_stdout_;
  TestHarnessOStream* server_stdin_;
  TestHarnessIStream* server_stdout_;
  std::ostream* log_;
  Timer timer_;

};
#endif
