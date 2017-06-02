//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for ClientSUTProtocolStack.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#define BOOST_TEST_MODULE ClientSUTProtocolStackTest
#include <boost/assign/list_of.hpp>
#include <sstream>
#include <memory>

#include "slave-harness-network-stack.h"
#include "client-sut-protocol-stack.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/numbered-command-sender.h"
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

BOOST_AUTO_TEST_CASE(ClientSUTProtocolStackWorks) {
  EventLoop event_loop;
  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 
  std::shared_ptr<NetworkConnection> 
    dummy_conn(new NetworkConnection(0, &event_loop));
  ScriptManager dummy_sm;
  SlaveHarnessNetworkStack network_stack("dummy_harness_id", 1, 
    dummy_conn, &dummy_sm);
  ClientSUTProtocolStack protocol_stack(0, &network_stack, &logger);
  int sut_stdin_read_fd;
  int sut_stdout_write_fd;

  // Set up the function that will set up the notional SUT's pipes.
  auto pipe_fun = [&](int* sut_stdin, int* sut_stdout) {
    SetupPipes(sut_stdout, &sut_stdout_write_fd,
               &sut_stdin_read_fd, sut_stdin);
    return 0;
  };

  // Spawn the notional SUT and build its protocol stack.
  SpawnSUT(pipe_fun, "", false, &event_loop, nullptr, nullptr, 
      &protocol_stack, nullptr);

  event_loop.Start();

  // Set up access to the notional SUT's stdin/out.
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  // Perform command sequence. SUT output is simulated by writing to
  // sut_output_stream while test harness output is simulated by using
  // protocol_stack's API. SUT input is verified via VerifyIStreamContents. 
  LOG(DEBUG) << "SUT sending READY...";
  sut_output_stream << "READY" << endl;

  LOG(DEBUG) << "TH sending SUBSCRIBE...";
  protocol_stack.WaitUntilReady();
  LineRawData<Knot> subscribe_data;
  // 70 here is the subscription ID.
  subscribe_data.AddLine(Knot(new string("70")));
  // This is the subscription filter to apply.
  subscribe_data.AddLine(Knot(new string(
          "fname = 'John' AND lname = 'McClane'")));
  NumberedCommandSender::ResultsFuture sub_f = 
    protocol_stack.GetSubscribeCommand()->Schedule(subscribe_data);
  VerifyIStreamContents(list_of(string("COMMAND 0"))("SUBSCRIBE 70")
                                ("fname = 'John' AND lname = 'McClane'")
                                ("ENDCOMMAND"), &sut_input_stream);

  LOG(DEBUG) << "SUT sending RESULTS...";
  sut_output_stream << "RESULTS 0\nDONE\nENDRESULTS\nREADY" << endl;
  BOOST_CHECK_EQUAL(sub_f.Value()->command_id, 0);
  BOOST_REQUIRE_EQUAL(sub_f.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(sub_f.Value()->results_received.IsRaw(0), false);
  BOOST_CHECK_EQUAL(sub_f.Value()->results_received.Get(0), "DONE");

  LOG(DEBUG) << "TH sending UNSUBSCRIBE...";
  protocol_stack.WaitUntilReady();
  LineRawData<Knot> unsubscribe_data;
  // 70 here is the subscription ID.
  unsubscribe_data.AddLine(Knot(new string("70")));
  NumberedCommandSender::ResultsFuture unsub_f = 
    protocol_stack.GetUnsubscribeCommand()->Schedule(unsubscribe_data);
  VerifyIStreamContents(list_of(string("COMMAND 1"))("UNSUBSCRIBE 70")
                                ("ENDCOMMAND"), &sut_input_stream);

  LOG(DEBUG) << "SUT sending RESULTS...";
  sut_output_stream << "RESULTS 1\nDONE\nENDRESULTS\nREADY" << endl;
  BOOST_CHECK_EQUAL(unsub_f.Value()->command_id, 1);
  BOOST_REQUIRE_EQUAL(unsub_f.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(unsub_f.Value()->results_received.IsRaw(0), false);
  BOOST_CHECK_EQUAL(unsub_f.Value()->results_received.Get(0), "DONE");

  LOG(DEBUG) << "TH sending SHUTDOWN...";
  protocol_stack.WaitUntilReady();
  protocol_stack.GetRootModeCommandSender()->SendCommand("SHUTDOWN");
  VerifyIStreamContents(list_of(string("SHUTDOWN")), &sut_input_stream);
  sut_output_stream << "DONE" << endl;
  // This final READY/wait sequence is done to ensure protocol_stack receives
  // all of the notional SUT's output before event_loop terminates.
  sut_output_stream << "READY" << endl;
  LOG(DEBUG) << "Waiting for final READY...";
  protocol_stack.WaitUntilReady();
  LOG(DEBUG) << "Shutting down connection...";
  dummy_conn->Shutdown();
  sut_output_stream.close();
  LOG(DEBUG) << "Exiting event loop...";
  event_loop.ExitLoopAndWait();
}

