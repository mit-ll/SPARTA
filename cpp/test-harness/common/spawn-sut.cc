//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************

#include "spawn-sut.h"

#include "sut-protocol-stack.h"
#include "common/logging.h"
#include "common/check.h"

using namespace std;

void SpawnSUT(
    function<int(int*, int*)> pipe_fun,
    const string& debug_directory, bool unbuffered,
    EventLoop* event_loop, std::ofstream* stdout_log,
    std::ofstream* stdin_log, SUTProtocolStack* protocol_stack,
    ReadEventLoop::EOFCallback sut_terminated_cb) {
  if (!debug_directory.empty()) {
    LOG(INFO) << "Logging all SUT communication to "
        << debug_directory
        << ". Note that this will adversely affect performance.";

    DCHECK(stdout_log != nullptr);
    DCHECK(stdin_log != nullptr);

    if (unbuffered) {
      LOG(INFO) << "SUT communications log will be unbuffered. Note that "
          << "this will adversely affect performance.";
      stdout_log->rdbuf()->pubsetbuf(0, 0);
      stdin_log->rdbuf()->pubsetbuf(0, 0);
    }

    // TODO(njhwang) it doesn't appear that the LOG(FATAL) occurs properly if
    // the directory doesn't exist if a SafeOFStream is passed in...
    string sut_stdout_log_path = debug_directory + "/sut_stdout";
    stdout_log->open(sut_stdout_log_path.c_str());
    string sut_stdin_log_path = debug_directory + "/sut_stdin";
    stdin_log->open(sut_stdin_log_path.c_str());


    protocol_stack->StartSUTAndBuildStack(
        event_loop, pipe_fun,
        stdout_log, stdin_log, sut_terminated_cb);
  } else {
    protocol_stack->StartSUTAndBuildStack(
        event_loop, pipe_fun,
        nullptr, nullptr, sut_terminated_cb);
  }
}
