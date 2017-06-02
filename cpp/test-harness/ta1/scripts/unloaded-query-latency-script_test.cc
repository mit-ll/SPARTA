//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit test for the unloaded query latency test script. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012   omd            Original Version
//*****************************************************************

#include "unloaded-query-latency-script.h"

#define BOOST_TEST_MODULE UnloadedQueryTest
#include "common/test-init.h"

#include <boost/bind.hpp>
#include <boost/thread.hpp>
#include <iostream>

#include "common/util.h"
#include "common/general-logger.h"
#include "test-harness/common/agg-numbered-command-fixture.h"
#include "test-harness/common/delay-generators.h"
#include "test-harness/ta1/query-command.h"

using namespace std;

class UQLTestFixture : public AggNumberedCommandFixture {
 public:
  UQLTestFixture();

  virtual ~UQLTestFixture() {}

  QueryCommand query_command;
};

UQLTestFixture::UQLTestFixture()
    : query_command(nc_sender) {
}

// TODO(odain) njhwang: I saw this fail at least once with this message:
// [FATAL] Check 'map_it != agg_map_.end()' failed in
// cpp/test-harness/common/agg-numbered-command-sender.cc on line 49
BOOST_FIXTURE_TEST_CASE(UnloadedQueryTestWorks, UQLTestFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  sut_output_stream << "READY" << endl;

  ostringstream* fake_log_file = new ostringstream;
  OstreamElapsedTimeLogger logger(fake_log_file); 

  istringstream queries_file(
      "SELECT * from foo where bar\n"
      "SELECT id from foo where fizzle\n");

  UnloadedQueryLatencyScript script(&queries_file, 1, &ZeroDelay, 
                                    &query_command, &logger);
  boost::thread script_thread(
      boost::bind(&UnloadedQueryLatencyScript::Run, &script));

  string line;
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "COMMAND 0");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "SELECT * from foo where bar");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDCOMMAND");

  // There shouldn't be another command, no matter how long I wait, until I send
  // results for the first one. Even if I send a READY.
  sut_output_stream << "READY" << endl;
  boost::this_thread::sleep(boost::posix_time::milliseconds(100));
  BOOST_CHECK_EQUAL(sut_input_stream.rdbuf()->in_avail(), 0);

  sut_output_stream << "RESULTS 0\n"
      "ROW\n"
      "fizzle\n"
      "ENDROW\n"
      "ENDRESULTS" << endl;

  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "COMMAND 1");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "SELECT id from foo where fizzle");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDCOMMAND");


  sut_output_stream << "RESULTS 1\n"
      "ROW\n"
      "fizzle\n"
      "ENDROW\n"
      "ENDRESULTS" << endl;

  script_thread.join();
}
