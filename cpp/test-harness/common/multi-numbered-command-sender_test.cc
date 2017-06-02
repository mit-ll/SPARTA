//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for MultiNumberedCommandSender 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 Sep 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE NumberedCommandSenderTest
#include "common/test-init.h"

#include "multi-numbered-command-sender.h"

#include <thread>
#include <vector>

#include "common/util.h"
#include "common/types.h"
#include "multi-numbered-command-fixture.h"

using namespace std;

void AccumulateResults(
    MultiNumberedCommandSender::SharedResults results,
    vector<MultiNumberedCommandSender::SharedResults>* results_received,
    std::mutex* tex, std::condition_variable* changed_cond) {
  MutexGuard l(*tex); 
  results_received->push_back(results);
  changed_cond->notify_all();
}

BOOST_FIXTURE_TEST_CASE(CommandResponseWorks, MultiNumberedCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  sut_output_stream << "READY\n";
  sut_output_stream.flush();

  vector<MultiNumberedCommandSender::SharedResults> results_received;

  int command_id;
  std::mutex data_tex;
  std::condition_variable data_changed_cond;
  nc_extension->SendCommand(
      new string("HELLO\n"),
      std::bind(&AccumulateResults, std::placeholders::_1, &results_received,
                &data_tex, &data_changed_cond),
      &command_id);

  BOOST_CHECK_EQUAL(command_id, 0);

  // The call to SendCommand should result in the full "COMMAND
  // 0\nHELLO\nENDCOMMAND\n" begin sent. Make sure this is the case.
  string sut_received;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "COMMAND 0");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "HELLO");
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "ENDCOMMAND");

  // Reply with multiple sets of results.
  sut_output_stream << "RESULTS 0\npart 1\nENDRESULTS\n";
  sut_output_stream.flush();

  sut_output_stream << "RESULTS 0\npart 2\nENDRESULTS\n";
  sut_output_stream.flush();

  sut_output_stream << "RESULTS 0\npart 3\nENDRESULTS\n";
  sut_output_stream.flush();

  // Wait for the results.
  {
    UniqueMutexGuard g(data_tex);
    while (results_received.size() < 3) {
      data_changed_cond.wait(g);
    }
  }

  BOOST_REQUIRE_EQUAL(results_received.size(), 3);

  BOOST_CHECK_EQUAL(results_received[0]->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(results_received[0]->results_received.Get(0), "part 1");

  BOOST_CHECK_EQUAL(results_received[1]->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(results_received[1]->results_received.Get(0), "part 2");

  BOOST_CHECK_EQUAL(results_received[2]->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(results_received[2]->results_received.Get(0), "part 3");

  nc_extension->RemoveCallback(0);
}
