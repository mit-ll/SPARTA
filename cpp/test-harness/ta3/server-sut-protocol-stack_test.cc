//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for ServerSUTProtocolStack.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#define BOOST_TEST_MODULE ServerSUTProtocolStackTest
#include <boost/assign/list_of.hpp>

#include "server-sut-protocol-stack.h"
#include "test-harness/common/root-mode-command-sender.h"
#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/common/spawn-sut.h"
#include "common/event-loop.h"
#include "common/test-init.h"
#include "common/test-util.h"
#include "common/util.h"

using boost::assign::list_of;
using namespace std;

BOOST_AUTO_TEST_CASE(ServerSUTProtocolStackWorks) {
  EventLoop event_loop;
  ServerSUTProtocolStack protocol_stack;
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

  LOG(DEBUG) << "TH sending PUBLISH...";
  protocol_stack.WaitUntilReady();
  LineRawData<Knot> publish_data;
  // This is the publication metadata.
  publish_data.AddLine(Knot(new string("John,McClane,123456789,1955-05-23")));
  // This is the publication payload.
  publish_data.AddRaw(Knot(new string(
    "Come out to the coast, we'll get together, have a few laughs...")));
  NumberedCommandSender::ResultsFuture sub_f = 
    protocol_stack.GetPublishCommand()->Schedule(publish_data);
  VerifyIStreamContents(list_of(string("COMMAND 0"))("PUBLISH")
      ("METADATA")("John,McClane,123456789,1955-05-23")("PAYLOAD")
      ("RAW")("63") 
      ("Come out to the coast, we'll get together, have a few laughs...ENDRAW")
      ("ENDPAYLOAD")("ENDPUBLISH")("ENDCOMMAND"),
      &sut_input_stream);

  LOG(DEBUG) << "SUT sending RESULTS...";
  sut_output_stream << "RESULTS 0\nDONE\nENDRESULTS\nREADY" << endl;
  BOOST_CHECK_EQUAL(sub_f.Value()->command_id, 0);
  BOOST_REQUIRE_EQUAL(sub_f.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(sub_f.Value()->results_received.IsRaw(0), false);
  BOOST_CHECK_EQUAL(sub_f.Value()->results_received.Get(0), "DONE");

  LOG(DEBUG) << "TH sending SHUTDOWN...";
  protocol_stack.WaitUntilReady();
  protocol_stack.GetRootModeCommandSender()->SendCommand("SHUTDOWN");
  VerifyIStreamContents(list_of(string("SHUTDOWN")), &sut_input_stream);
  sut_output_stream << "DONE" << endl;
  // This final READY/wait sequence is done to ensure protocol_stack receives
  // all of the notional SUT's output before event_loop terminates.
  sut_output_stream << "READY" << endl;
  sut_output_stream.close();
  protocol_stack.WaitUntilReady();
  event_loop.ExitLoopAndWait();
}

