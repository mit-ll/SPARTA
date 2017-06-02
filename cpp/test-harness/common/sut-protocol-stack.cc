//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of SUTProtocolStack 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************

#include "sut-protocol-stack.h"

#include <sys/wait.h>

#include "ready-monitor.h"
#include "common/protocol-extension-manager.h"
#include "common/util.h"

using std::string;

void SUTProtocolStack::StartSUTAndBuildStack(
    EventLoop* event_loop, PipeSetupFunction pipe_fun, 
    std::ostream* sut_stdout_log, std::ostream* sut_stdin_log, 
    ReadEventLoop::EOFCallback sut_terminated_cb) {
  event_loop_ = event_loop;

  sut_pid_ = pipe_fun(&sut_stdin_, &sut_stdout_);

  if (sut_stdin_log != NULL) {
    LogAllOutput(sut_stdin_log);
  }

  // This ends up being owned by the LineRawParser
  proto_manager_ = new ProtocolExtensionManager;
  // This ends up being owned by proto_mananger
  ready_monitor_ = new ReadyMonitor(
      event_loop->GetWriteQueue(sut_stdin_));
  proto_manager_->AddHandler("READY", ready_monitor_);

  lr_parser_.reset(new LineRawParser(proto_manager_));

  if (sut_terminated_cb) {
    event_loop->RegisterEOFCallback(sut_stdout_, sut_terminated_cb);
  }

  event_loop->RegisterFileDataCallback(
      sut_stdout_,
      boost::bind(&LineRawParser::DataReceived, lr_parser_.get(), _1),
      sut_stdout_log);

  SetupCommands();
}

void SUTProtocolStack::WaitUntilReady() {
  CHECK(ready_monitor_ != nullptr);
  ready_monitor_->WaitUntilReady();
}

void SUTProtocolStack::WaitUntilSUTDies() {
  int status = 0;
  waitpid(sut_pid_, &status, 0 );
  CHECK(status == 0) << "SUT terminated with non-zero status: " << status;
}

void SUTProtocolStack::LogAllOutput(std::ostream* output_stream) {
  event_loop_->GetWriteQueue(sut_stdin_)->SetDebugLoggingStream(output_stream);
}
