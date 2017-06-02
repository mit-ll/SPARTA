// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for NumberedCommandSender 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 30 Aug 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE NumberedCommandSenderTest
#include "common/test-init.h"

#include "numbered-command-sender.h"

#include <cstring>
#include <memory>
#include <unistd.h>

#include "common/util.h"
#include "common/event-loop.h"
#include "common/string-algo.h"
#include "numbered-command-fixture.h"
#include "ready-monitor.h"

using namespace std;

BOOST_FIXTURE_TEST_CASE(CommandResponseWorks, NumberedCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  NumberedCommandSender::ResultsFuture f1 =
      nc_extension->SendCommand(new string("HELLO\n"));

  sut_output_stream << "READY\n";
  sut_output_stream.flush();

  // The call to SendCommand should result in the full "COMMAND
  // 0\nHELLO\nENDCOMMAND\n" begin sent. Make sure this is the case.
  string sut_received;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "COMMAND 0");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "HELLO");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "ENDCOMMAND");

  // Reply with results to this command. This should result in the future
  // getting fired with the value "and hello to you sir".
  sut_output_stream << "RESULTS 0\nand hello to you sir\nENDRESULTS\n";
  sut_output_stream.flush();

  f1.Wait();
  BOOST_CHECK_EQUAL(f1.Value()->command_id, 0);
  BOOST_CHECK_EQUAL(f1.Value()->results_received.Size(), 1);
  BOOST_CHECK(f1.Value()->results_received.IsRaw(0) == false);
  BOOST_CHECK_EQUAL(f1.Value()->results_received.Get(0),
                    "and hello to you sir");
}

// Send several commands and several responses but have the responses be in a
// different order. Make sure the correct futures get fired.
BOOST_FIXTURE_TEST_CASE(OutOfOrderResponsesWork, NumberedCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  sut_output_stream << "READY\n";
  sut_output_stream.flush();
  NumberedCommandSender::ResultsFuture f0 =
      nc_extension->SendCommand(new string("c0\n"));

  string sut_received;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "COMMAND 0");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "c0");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "ENDCOMMAND");

  sut_output_stream << "READY\n";
  sut_output_stream.flush();
  NumberedCommandSender::ResultsFuture f1 =
      nc_extension->SendCommand(new string("c1\n"));
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "COMMAND 1");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "c1");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "ENDCOMMAND");
  
  sut_output_stream << "READY\n";
  sut_output_stream.flush();
  NumberedCommandSender::ResultsFuture f2 =
      nc_extension->SendCommand(new string("c2\n"));
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "COMMAND 2");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "c2");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "ENDCOMMAND");

  sut_output_stream << "RESULTS 1\nHELLO!!\nENDRESULTS" << std::endl;
  f1.Wait();
  BOOST_CHECK_EQUAL(f1.Value()->command_id, 1);
  BOOST_REQUIRE_EQUAL(f1.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(f1.Value()->results_received.IsRaw(0), false);
  BOOST_CHECK_EQUAL(f1.Value()->results_received.Get(0), "HELLO!!");

  sut_output_stream
      << "RESULTS 0\nr0\nRAW\n3\nabcENDRAW\nENDRESULTS" << std::endl;
  f0.Wait();
  BOOST_CHECK_EQUAL(f0.Value()->command_id, 0);
  BOOST_REQUIRE_EQUAL(f0.Value()->results_received.Size(), 2);
  BOOST_CHECK_EQUAL(f0.Value()->results_received.IsRaw(0), false);
  BOOST_CHECK_EQUAL(f0.Value()->results_received.Get(0), "r0");
  BOOST_CHECK_EQUAL(f0.Value()->results_received.IsRaw(1), true);
  BOOST_CHECK_EQUAL(f0.Value()->results_received.Get(1), "abc");

  sut_output_stream << "RESULTS 2\nRAW\n2\nzzENDRAW\nENDRESULTS" << std::endl;
  f2.Wait(); 
  BOOST_CHECK_EQUAL(f2.Value()->command_id, 2);
  BOOST_REQUIRE_EQUAL(f2.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(f2.Value()->results_received.IsRaw(0), true);
  BOOST_CHECK_EQUAL(f2.Value()->results_received.Get(0), "zz");
}
