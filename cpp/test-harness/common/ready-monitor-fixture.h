//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit test fixture.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_COMMON_READY_MONITOR_FIXTURE_H_
#define CPP_TEST_HARNESS_COMMON_READY_MONITOR_FIXTURE_H_

#include <memory>

#include "common/check.h"
#include "common/event-loop.h"
#include "common/line-raw-parser.h"

class ReadyMonitor;
class ProtocolExtensionManager;

/// Each command, and protocol handler has unit tests. These generally set up the
/// same set of pipes, parsers, ready monitors, etc. This file defines a
/// ReadyMonitorFixture class that sets up the EventLoop, LineRawParser,
/// ReadyMonitor and pipes used for testing.
///
/// Unit tests for numbered commands, inidividual commands, etc. will require
/// this same functionality, plus some other components. They would thus create a
/// subclass of this (or another subclass) and add additional protocol layers.
class ReadyMonitorFixture {
 public:
  ReadyMonitorFixture();
  virtual ~ReadyMonitorFixture() {
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
  ReadyMonitor* ready_monitor;
  int sut_stdout_write_fd;
  int sut_stdin_read_fd;

};

#endif
