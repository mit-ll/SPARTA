//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of MultiClientSUTProtocolStack 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   njh            Original Version
//*****************************************************************

#include <fstream>

#include "multi-client-sut-protocol-stack.h"
#include "slave-harness-network-stack.h"
#include "client-sut-protocol-stack.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/spawn-sut.h"
#include "common/safe-file-stream.h"
#include "common/general-logger.h"
#include "common/string-algo.h"
#include "common/logging.h"
#include "common/types.h"
#include "common/check.h"

using namespace std;

MultiClientSUTProtocolStack::MultiClientSUTProtocolStack(
    function<int(int*, int*, std::string)> spawn_fun,
    const std::string& debug_directory, bool unbuffered,
    EventLoop* event_loop, size_t num_suts, 
    SlaveHarnessNetworkStack* network_stack, 
    std::vector<SUTRunningMonitor*> sut_monitors, 
    std::vector<std::string> sut_argsv, GeneralLogger* logger) {

  if (sut_argsv.size() != 1) {
    DCHECK(sut_argsv.size() == num_suts);
  }
  string sut_args = sut_argsv[0];
  MutexGuard l(data_tex_);
  for (size_t i = 0; i < num_suts; i++) {
    auto protocol_stack = new ClientSUTProtocolStack(i, network_stack, logger);
    SafeOFStream* sut_stdout_log = nullptr;
    SafeOFStream* sut_stdin_log = nullptr;

    LOG(INFO) << "Spawning SUT #" << i;
    if (sut_argsv.size() != 1) {
      sut_args = sut_argsv[i];
    } 
    auto pipe_fun = [&](int* sut_stdin, int* sut_stdout) {
      return spawn_fun(sut_stdin, sut_stdout, sut_args);
    };
    if (!debug_directory.empty()) {
      sut_stdout_log = new SafeOFStream();
      sut_stdin_log = new SafeOFStream();
      sut_stdin_logs_.push_back(sut_stdin_log);
      sut_stdout_logs_.push_back(sut_stdout_log);
      SpawnSUT(pipe_fun, 
               debug_directory + "/" + 
                 network_stack->GetHarnessId() + "-" + itoa(i), 
               unbuffered,
               event_loop, sut_stdout_log, sut_stdin_log, 
               protocol_stack, 
               std::bind(&SUTRunningMonitor::SUTShutdown, sut_monitors[i]));
    } else {
      SpawnSUT(pipe_fun, "", unbuffered,
               event_loop, sut_stdout_log, sut_stdin_log, protocol_stack,
               std::bind(&SUTRunningMonitor::SUTShutdown, sut_monitors[i]));
    }

    LOG(INFO) << "Spawned SUT #" << i;
    sut_pstacks_.push_back(protocol_stack);
  }
}

MultiClientSUTProtocolStack::~MultiClientSUTProtocolStack() {
  for (auto item : sut_pstacks_) {
    delete item;
  }
  for (auto item : sut_stdin_logs_) {
    delete item;
  }
  for (auto item : sut_stdout_logs_) {
    delete item;
  }
}

void MultiClientSUTProtocolStack::WaitUntilAllReady() {
  for (auto pstack : sut_pstacks_) {
    pstack->WaitUntilReady();
  }
}

void MultiClientSUTProtocolStack::WaitUntilAllSUTsDie() {
  for (auto pstack : sut_pstacks_) {
    pstack->WaitUntilSUTDies();
  }
}

ClientSUTProtocolStack* 
    MultiClientSUTProtocolStack::GetProtocolStack(size_t sut_id) {
  std::lock_guard<std::mutex> l(data_tex_);
  DCHECK(sut_id >= 0);
  DCHECK(sut_id < sut_pstacks_.size()) << "Could not find the specified SUT "
    << "with ID " << sut_id;
  return sut_pstacks_[sut_id];
}

size_t MultiClientSUTProtocolStack::GetNumClientSUTs() {
  std::lock_guard<std::mutex> l(data_tex_);
  return sut_pstacks_.size(); 
}
