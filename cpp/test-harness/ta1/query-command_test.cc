//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for QueryCommand.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************

#include "query-command.h"

#define BOOST_TEST_MODULE QueryCommandTest
#include "common/test-init.h"
#include "common/test-util.h"

#include <boost/assign/list_of.hpp>
#include <boost/regex.hpp>
#include <boost/thread.hpp>
#include <memory>
#include <sstream>

#include "common/event-loop.h"
#include "common/general-logger.h"
#include "common/knot.h"
#include "common/string-algo.h"
#include "common/util.h"
#include "test-harness/common/agg-numbered-command-fixture.h"
#include "test-harness/common/ready-monitor.h"

using namespace std;

using boost::regex_match;
using boost::regex;
using boost::assign::list_of;

class QueryCommandFixture : public AggNumberedCommandFixture {
 public:
  QueryCommandFixture();
  virtual ~QueryCommandFixture() {}

  auto_ptr<QueryCommand> query_command;
};

QueryCommandFixture::QueryCommandFixture() {
  query_command.reset(new QueryCommand(nc_sender));
}

BOOST_FIXTURE_TEST_CASE(QueryCommandWithLoggingWorks, QueryCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  ostringstream* fake_log_file = new ostringstream;
  OstreamElapsedTimeLogger logger(fake_log_file); 

  sut_output_stream << "READY\n";
  sut_output_stream.flush();

  Knot query(new string("SELECT * FROM table WHERE age BETWEEN 18 AND 24\n"));
  
  Future<Knot> f = query_command->Schedule(0, 0, query, &logger);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  string line;
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "COMMAND 0");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "SELECT * FROM table WHERE age BETWEEN 18 AND 24");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDCOMMAND");

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  // 118 is the row id, the next line is "data"
  sut_output_stream << "RESULTS 0\nROW\n118\nHi there\nENDROW\nENDRESULTS\n";
  sut_output_stream.flush();

  f.Wait();

  // The last "line" should be empty. Since there's a final newline Split puts
  // an additional entry in the vector.
  // The line before that should be empty too. We log exactly what we got and
  // DONE includes a final newline which gets logged in addition to a final
  // newline. I don't think we want to strip off the final newlines as the
  // results could contain binary data.
  // The order of the 1st two log messages isn't defined and depends on how
  // things get scheduled.
  // This is a bit wasteful to Split here and Split again in VerifyInputLines,
  // and possibly do an unnecessary regex_match...but this is pretty
  // readable/maintainable as is.
  vector<string> log_lines = Split(fake_log_file->str(), '\n');
  vector<string> exp_lines = 
    list_of(string("^\\[\\d+\\.\\d+\\] ID \\?-0 queued"))
            (string("^\\[\\d+\\.\\d+\\] ID 0-0 QID 0: ") +
              "\\[\\[SELECT [^\\]]+\\]\\]")
            ("^\\[\\d+\\.\\d+\\] ID 0-0 sent")
            ("^\\[\\d+\\.\\d+\\] ID 0-0 results:")
            ("118 [0-9a-f]{32}")("")("");
  VerifyInputLines(fake_log_file->str(), exp_lines);
}

// Almost the same as the above, but we verify that we log when the command was
// *sent* by delaying the time at which we send READY and making sure the
// difference between the timestamps on the lines indicating the message was
// queued and the message was sent are at least as large as the delay.
BOOST_FIXTURE_TEST_CASE(LogWhenCommandSentWorks, QueryCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 


  Knot query(new string("SELECT * FROM table WHERE age BETWEEN 18 AND 24\n"));
  
  Future<Knot> f = query_command->Schedule(0, 0, query, &logger);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  // 200k us == 0.2 seconds
  const int kDelayMicros = 200000;
  boost::this_thread::sleep(boost::posix_time::microseconds(kDelayMicros));

  sut_output_stream << "READY\n";
  sut_output_stream.flush();

  string line;
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "COMMAND 0");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "SELECT * FROM table WHERE age BETWEEN 18 AND 24");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDCOMMAND");

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  // 118 is the row id, the next line is "data"
  sut_output_stream << "RESULTS 0\nROW\n118\nHi there\nENDROW\nENDRESULTS\n";
  sut_output_stream.flush();

  f.Wait();

  vector<string> exp_lines = 
    list_of(string("^\\[\\d+\\.\\d+\\] ID \\?-0 queued"))
            (string("^\\[\\d+\\.\\d+\\] ID 0-0 QID 0: ") +
              "\\[\\[SELECT [^\\]]+\\]\\]")
            ("^\\[\\d+\\.\\d+\\] ID 0-0 sent")
            ("^\\[\\d+\\.\\d+\\] ID 0-0 results:")
            ("118 [0-9a-f]{32}")("")("");
  VerifyInputLines(fake_log_file->str(), exp_lines);

  // Again, this is a bit wasteful to Split here again and repeat the regex
  // checks, but this is fairly readable/maintainable as is.
  vector<string> log_lines = Split(fake_log_file->str(), '\n');
  regex expected_queued("\\[(\\d+\\.\\d+)\\] ID \\?-0 queued");
  regex expected_sent("\\[(\\d+\\.\\d+)\\] ID 0-0 sent");
  boost::smatch queued_match, sent_match;
  regex_match(log_lines[0], queued_match, expected_queued);
  regex_match(log_lines[2], sent_match, expected_sent);

  double queued_ts, sent_ts;
  queued_ts = atof(queued_match.str(1).c_str());
  sent_ts = atof(sent_match.str(1).c_str());
  BOOST_CHECK_GT(queued_ts, 0);
  BOOST_CHECK_GT(sent_ts, 0);

  const int kNumMicrosPerSecond = 1000000;
  BOOST_CHECK_GE(sent_ts - queued_ts,
                 double(kDelayMicros) / double(kNumMicrosPerSecond));
}
