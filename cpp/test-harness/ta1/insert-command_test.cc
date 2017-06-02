//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for InsertCommand
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 14 Sep 2012   omd            Original Version
//*****************************************************************

#include "insert-command.h"

#define BOOST_TEST_MODULE InsertCommandTest
#include "common/test-init.h"
#include "common/test-util.h"

#include <boost/assign/list_of.hpp>
#include <sstream>
#include <memory>

#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/util.h"
#include "test-harness/common/numbered-command-fixture.h"
#include "test-harness/common/ready-monitor.h"

using namespace std;
using boost::assign::list_of;

class InsertCommandFixture : public NumberedCommandFixture {
 public:
  InsertCommandFixture();
  virtual ~InsertCommandFixture() {}

  auto_ptr<InsertCommand> insert_command;
};

InsertCommandFixture::InsertCommandFixture() {
  insert_command.reset(new InsertCommand(nc_extension));
}

BOOST_FIXTURE_TEST_CASE(InsertCommandWithLoggingWorks, InsertCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  ostringstream* fake_log_file = new ostringstream;
  OstreamElapsedTimeLogger logger(fake_log_file); 

  sut_output_stream << "READY\n";
  sut_output_stream.flush();

  LineRawData<Knot> insert_data;
  // 118 here is the row id to insert.
  insert_data.AddLine(Knot(new string("118")));
  insert_data.AddLine(Knot(new string("data 1")));
  
  NumberedCommandSender::ResultsFuture f =
      insert_command->Schedule(insert_data, &logger);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  string line;
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "COMMAND 0");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "INSERT");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "118");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "data 1");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDINSERT");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDCOMMAND");

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  sut_output_stream << "RESULTS 0\nDONE\nENDRESULTS\n";
  sut_output_stream.flush();

  BOOST_CHECK_EQUAL(f.Value()->command_id, 0);
  BOOST_REQUIRE_EQUAL(f.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(f.Value()->results_received.IsRaw(0), false);
  BOOST_CHECK_EQUAL(f.Value()->results_received.Get(0), "DONE");

  // The last "line" should be empty. Since there's a final newline Split puts
  // an additional entry in the vector.
  // The line before that should be empty too. We log exactly what we got and
  // DONE includes a final newline which gets logged in addition to a final
  // newline. I don't think we want to strip off the final newlines as the
  // results could contain binary data.
  vector<string> exp_lines = 
    list_of("Command: INSERT, command id: 0, row: 118$")
           ("Command 0 complete. Results: DONE$")("")("");
  // TODO(njhwang) update this to be compliant with Phase 2 logging format
  //VerifyTimeStampedInputLines(fake_log_file->str(), exp_lines);
}
