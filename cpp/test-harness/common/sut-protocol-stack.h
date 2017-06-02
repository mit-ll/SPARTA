//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Class that manages the stack of protocol parsers needed
//                     to control the client SUT from the test harness.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_SUT_PROTOCOL_STACK_H_
#define CPP_TEST_HARNESS_COMMON_SUT_PROTOCOL_STACK_H_

#include <ostream>
#include <memory>
#include <functional>

#include "common/line-raw-parser.h"
#include "common/read-event-loop.h"

class ProtocolExtensionManager;
class ReadyMonitor;
class EventLoop;

/// Construct one of these and then call StartSUTAndBuildStack. That method
/// spawns the SUT, connects to stdin and stdout, and then builds the protocol
/// stack (LineRawParser, ReadyMonitor, etc.) to allow communication with the
/// SUT.
class SUTProtocolStack {
 public:
  SUTProtocolStack() {}
  virtual ~SUTProtocolStack() {}
  
  /// event_loop is a pointer to the EventLoop object that should manage the
  /// connection with the SUT. This does *not* take ownership of the EventLoop.
  ///
  /// The SUT is "spawned" via pipe_fun. pipe_fun is a function that takes two
  /// pointers to file handles as parameters. Upon completion, pipe_fun should
  /// set the pointers to valid file handles, whether by spawning a process and
  /// piping the process' stdin/out to the file handles, or by creating
  /// standalone pipes to the file handles.
  ///
  /// If sut_stdout_log is not null all data read from the SUT will be logged to
  /// the given stream. Similarly for sut_stdin_log. Note that both of these will
  /// seriously impact performance.
  typedef std::function<int(int*, int*)> PipeSetupFunction;
  virtual void StartSUTAndBuildStack(
      EventLoop* event_loop, PipeSetupFunction pipe_fun, 
      std::ostream* sut_stdout_log, std::ostream* sut_stdin_log,
      ReadEventLoop::EOFCallback sut_terminated_cb);

  /// For debugging purposes we can ask that every byte of data sent to the test
  /// harness gets logged to the specified output stream.
  void LogAllOutput(std::ostream* output_stream);

  /// Blocks until the SUT sends a READY signal.
  void WaitUntilReady();

  /// Blocks until the SUT process dies.
  void WaitUntilSUTDies();

 protected:
  /// Adds test harness commands to the protocol stack.
  virtual void SetupCommands() = 0;

  ReadyMonitor* GetReadyMonitor() {
    return ready_monitor_;
  }

  ProtocolExtensionManager* GetProtocolManager() {
    return proto_manager_;
  }
 private:

  EventLoop* event_loop_;
  ReadyMonitor* ready_monitor_;
  ProtocolExtensionManager* proto_manager_;
  std::unique_ptr<LineRawParser> lr_parser_;
  /// The file descriptors for the SUT's stdout and stdin.
  int sut_stdin_;
  int sut_stdout_;
  /// The SUT's pid.
  int sut_pid_;
};

#endif
