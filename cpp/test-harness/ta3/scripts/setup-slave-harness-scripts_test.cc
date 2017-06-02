//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for SetupSlaveHarnessScripts
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#define BOOST_TEST_MODULE SetupSlaveHarnessScriptsTest
#include "common/test-init.h"

#include <boost/assign/list_of.hpp>
#include <sstream>

#include "setup-slave-harness-scripts.h"
#include "test-harness/ta3/multi-client-sut-protocol-stack.h"
#include "test-harness/ta3/slave-harness-network-stack.h"
#include "test-harness/ta3/client-sut-protocol-stack.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/script-manager.h"
#include "common/network-connection.h"
#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/util.h"

using boost::assign::list_of;
using namespace std;

BOOST_AUTO_TEST_CASE(SetupSlaveHarnessScriptsWorks) {
  EventLoop event_loop;

  size_t num_suts = 5;
  int sut_stdin_read_fds[num_suts];
  int sut_stdout_write_fds[num_suts];
  int suts_spawned = 0;

  vector<SUTRunningMonitor*> sut_monitors;
  for (size_t i = 0; i < num_suts; i++) {
    sut_monitors.push_back(new SUTRunningMonitor());
  }

  // Set up the function that will set up the notional SUTs' pipes.
  auto pipe_fun = [&](int* sut_stdin, int* sut_stdout, string args) {
    SetupPipes(sut_stdout, &sut_stdout_write_fds[suts_spawned],
               &sut_stdin_read_fds[suts_spawned], sut_stdin);
    suts_spawned++;
    return 0;
  };

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  std::shared_ptr<NetworkConnection> 
    dummy_conn(new NetworkConnection(0, &event_loop));
  ScriptManager dummy_sm;
  SlaveHarnessNetworkStack network_stack("dummy_harness_id", 1, 
    dummy_conn, &dummy_sm);
  vector<string> dummy_args(1, "");
  MultiClientSUTProtocolStack protocol_stack(
      pipe_fun, "", false, &event_loop, num_suts, &network_stack, 
      sut_monitors, dummy_args, &logger);

  event_loop.Start();

  ScriptManager script_manager;

  SetupSlaveHarnessScripts(&protocol_stack, &logger, &script_manager,
      sut_monitors);

  std::vector<FileHandleOStream*> sut_ostreams;
  for (size_t i = 0; i < num_suts; i++) {
    // Set up access to the notional SUT's stdin/out.
    FileHandleOStream sut_output_stream(sut_stdout_write_fds[i]);
    sut_ostreams.push_back(&sut_output_stream);
    FileHandleIStream sut_input_stream(sut_stdin_read_fds[i]);
    ClientSUTProtocolStack* client_ps = protocol_stack.GetProtocolStack(i); 

    LOG(DEBUG) << "SUT sending READY...";
    sut_output_stream << "READY" << endl;
    client_ps->WaitUntilReady();
    sut_monitors[i]->SetShutdownExpected(true);
  }

  network_stack.Shutdown();
  for (auto item : sut_ostreams) {
    item->close();
  }
  event_loop.ExitLoopAndWait();

  for (auto item : sut_monitors) {
    delete item;
  }
}
