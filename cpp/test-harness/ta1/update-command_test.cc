//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for UpdateCommand.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************************
#include "update-command.h"

#define BOOST_TEST_MODULE UpdateCommandTest
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

class UpdateCommandFixture : public NumberedCommandFixture {
 public:
  UpdateCommandFixture();
  virtual ~UpdateCommandFixture() {}

  auto_ptr<UpdateCommand> update_command;
};

UpdateCommandFixture::UpdateCommandFixture() {
  update_command.reset(new UpdateCommand(nc_extension));
}

BOOST_FIXTURE_TEST_CASE(UpdateCommandWithLoggingWorks, UpdateCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  sut_output_stream << "READY\n";
  sut_output_stream.flush();

  LineRawData<Knot> update_data;
  // 7 here is the row id to update.
  update_data.AddLine(Knot(new string("7")));
  update_data.AddLine(Knot(new string("first_name")));
  update_data.AddLine(Knot(new string("Susan")));
  update_data.AddLine(Knot(new string("fingerprint")));
  update_data.AddRaw(Knot(new string("really raw data\n")));
  update_data.AddLine(Knot(new string("notes")));
  update_data.AddRaw(Knot(new string("kinda raw data\n")));
  update_data.AddLine(Knot(new string("last_name")));
  update_data.AddLine(Knot(new string("Boyle")));
  update_data.AddLine(Knot(new string("dob")));
  update_data.AddLine(Knot(new string("19610401")));

  NumberedCommandSender::ResultsFuture f =
      update_command->Schedule(update_data, &logger);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  string line;
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "COMMAND 0");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "UPDATE 7");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "first_name");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "Susan");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "fingerprint");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "RAW");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "16");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "really raw data");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDRAW");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "notes");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "RAW");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "15");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "kinda raw data");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDRAW");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "last_name");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "Boyle");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "dob");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "19610401");
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "ENDUPDATE");
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
    list_of("Command: UPDATE, command id: 0, row: 7$")
           ("Command 0 complete. Results: DONE$")("")("");
  // TODO(njhwang) update this to be compliant with Phase 2 logging format
  //VerifyTimeStampedInputLines(fake_log_file->str(), exp_lines);
}
