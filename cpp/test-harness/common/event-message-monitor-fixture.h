//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit test fixture.
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_EVENT_MESSAGE_MONITOR_FIXTURE_H_
#define CPP_TEST_HARNESS_COMMON_EVENT_MESSAGE_MONITOR_FIXTURE_H_

#include <iostream>
#include <memory>

#include "common/line-raw-parser.h"
#include "common/event-loop.h"
#include "common/check.h"
#include "common/types.h"

class ProtocolExtensionManager;
class EventMessageMonitor;

class EventMessageMonitorFixture {
 public:
  EventMessageMonitorFixture();
  virtual ~EventMessageMonitorFixture() {
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
  ProtocolExtensionManager* manager;
  /// The ProtocolExtensionManager has ownership of this so we don't need to free
  /// it.
  EventMessageMonitor* em_monitor;
  int sut_stdout_write_fd;
  int sut_stdin_read_fd;
};

#endif
