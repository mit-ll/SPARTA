//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for MultiClientSUTProtocolStack.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#define BOOST_TEST_MODULE MultiClientSUTProtocolStackTest
#include <boost/assign/list_of.hpp>
#include <sstream>

#include "multi-client-sut-protocol-stack.h"
#include "slave-harness-network-stack.h"
#include "client-sut-protocol-stack.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/script-manager.h"
#include "test-harness/common/spawn-sut.h"
#include "common/network-connection.h"
#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/test-init.h"
#include "common/test-util.h"
#include "common/util.h"

using boost::assign::list_of;
using namespace std;

BOOST_AUTO_TEST_CASE(MultiClientSUTProtocolStackWorks) {
  const size_t num_suts = 5;
  EventLoop event_loop;
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
    // Make sure passing in separate args strings works
    BOOST_CHECK_EQUAL(args, "ARGS" + itoa(suts_spawned));
    suts_spawned++;
    return 0;
  };

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  // Spawn the notional SUTs and build all protocol stacks.
  std::shared_ptr<NetworkConnection> 
    dummy_conn(new NetworkConnection(0, &event_loop));
  ScriptManager dummy_sm;
  SlaveHarnessNetworkStack network_stack("dummy_harness_id", 1, 
    dummy_conn, &dummy_sm);
  vector<string> dummy_args(num_suts, "");
  for (size_t i = 0; i < num_suts; i++) {
    dummy_args[i] = "ARGS" + itoa(i);
  }
  MultiClientSUTProtocolStack multi_client_ps(
      pipe_fun, "", false, &event_loop, num_suts, 
      &network_stack, sut_monitors, dummy_args, &logger);

  event_loop.Start();

  // Make sure that we can command each SUT.
  for (size_t i = 0; i < num_suts; i++) {
    // Set up access to the notional SUT's stdin/out.
    FileHandleOStream sut_output_stream(sut_stdout_write_fds[i]);
    FileHandleIStream sut_input_stream(sut_stdin_read_fds[i]);
    ClientSUTProtocolStack* client_ps = multi_client_ps.GetProtocolStack(i); 

    // Simulate READY signals.
    sut_output_stream << "READY" << endl;
    client_ps->WaitUntilReady();

    // Perform command sequences. SUT output is simulated by writing to
    // sut_output_stream while test harness output is simulated by using
    // protocol_stack's API. SUT input is verified via VerifyIStreamContents.

    // TODO(njhwang) Test numbered commands later.

    client_ps->GetRootModeCommandSender()->SendCommand("SHUTDOWN");
    VerifyIStreamContents(list_of(string("SHUTDOWN")), &sut_input_stream);
    sut_monitors[i]->SetShutdownExpected(true);
    sut_output_stream << "DONE" << endl;
    // This final READY/wait sequence is done to ensure protocol_stack receives
    // all of the notional SUT's output before event_loop terminates and the log
    // files are closed.
    sut_output_stream << "READY" << endl;
  }
  // Test that WaitUntilAllReady() works.
  multi_client_ps.WaitUntilAllReady();

  event_loop.ExitLoopAndWait();

  for (auto item : sut_monitors) {
    delete item;
  }
}
