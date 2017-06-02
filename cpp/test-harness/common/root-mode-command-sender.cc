//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Implementation of RootModeCommandSender.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************

#include "root-mode-command-sender.h"

#include <sstream>

#include "ready-monitor.h"

using namespace std;

const char kDone[] = "DONE";
const int kDoneLen = strlen(kDone);

RootModeCommandSender::RootModeCommandSender(
    ReadyMonitor* ready_monitor)
    : ready_monitor_(ready_monitor) {
}

RootModeCommandSender::RootModeResultsFuture 
    RootModeCommandSender::SendCommand(string command_name) {
  std::ostringstream command_line;
  command_line << command_name << "\n";
  Knot* command_knot = new Knot(new string(command_line.str()));
   
  MutexGuard l(data_tex_);
  ready_monitor_->ScheduleSend(command_knot);
  RootModeResultsFuture results_future;
  future_ = results_future;
  return results_future;
}

void RootModeCommandSender::OnProtocolStart(Knot line) {
  MutexGuard l(data_tex_);
  if (line.Equal(kDone, kDoneLen)) {
    SharedRootModeResults cur_results_data;
    cur_results_data.reset(new LineRawData<Knot>);
    cur_results_data->AddLine(line);
    future_.Fire(cur_results_data);
    Done();
  } else {
    LOG(FATAL) << "Expected a DONE token as a result. Received " << line;
  }
}

void RootModeCommandSender::LineReceived(Knot line) {
  LOG(FATAL) << "Root mode commands should process at most a single line of "
      << "results. Received " << line;
}

void RootModeCommandSender::RawReceived(Knot data) {
  LOG(FATAL) << "Root mode commands should process at most a single line of "
      << "results. Received " << data;
}
