//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A unit test fixture for things that use
//                     ExtensibleReadyHandler. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_COMMON_EXTENSIBLE_READY_HANDLER_FIXTURE_H_
#define CPP_BASELINE_COMMON_EXTENSIBLE_READY_HANDLER_FIXTURE_H_

#include "extensible-ready-handler.h"

#include "common/line-raw-parser.h"
#include "common/event-loop.h"

/// See the comments on cpp/test-harness/common/ready-monitor-fixture.h
class ExtensibleReadyHandlerFixture {
 public:
  ExtensibleReadyHandlerFixture();
  virtual ~ExtensibleReadyHandlerFixture() {
    event_loop.ExitLoopAndWait();
  }

  /// Sets up a pipe. On return read_fd is a file descriptor the we can read from
  /// a write_fd is one we can write to.
  void SetupPipe(int* read_fd, int* write_fd) {
    int pipe_descriptors[2];
    int ret = pipe(pipe_descriptors);
    CHECK(ret == 0);

    /// The constants 0 and 1 here are as per the pipe() call.
    *read_fd = pipe_descriptors[0];
    *write_fd = pipe_descriptors[1];
  }

  /// Memebers are public since this is for unit tests.
  EventLoop event_loop;
  std::auto_ptr<LineRawParser> lr_parser;
  /// The LineRawParser owns this so we don't need to free it.
  ExtensibleReadyHandler* ready_handler;
  int sut_stdout_read_fd;
  int sut_stdin_write_fd;
 protected:
  int sut_stdout_write_fd;
  int sut_stdin_read_fd;
};


#endif
