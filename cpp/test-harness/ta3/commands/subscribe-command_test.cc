//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for SubscribeCommand.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#define BOOST_TEST_MODULE SubscribeCommandTest

#include <boost/assign/list_of.hpp>
#include <memory>
#include <sstream>

#include "subscribe-command.h"
#include "test-harness/common/numbered-command-fixture.h"
#include "test-harness/common/ready-monitor.h"
#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/test-init.h"
#include "common/test-util.h"
#include "common/util.h"

using namespace std;
using boost::assign::list_of;

class SubscribeCommandFixture : public NumberedCommandFixture {
 public:
  SubscribeCommandFixture();
  virtual ~SubscribeCommandFixture() {}

  unique_ptr<SubscribeCommand> subscribe_command;
};

SubscribeCommandFixture::SubscribeCommandFixture() {
  subscribe_command.reset(new SubscribeCommand(nc_extension));
}

BOOST_FIXTURE_TEST_CASE(SubscribeCommandWithLoggingWorks, SubscribeCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  sut_output_stream << "READY" << endl;

  LineRawData<Knot> subscribe_data;
  // 70 here is the subscription ID.
  subscribe_data.AddLine(Knot(new string("70")));
  // This is the subscription filter to apply.
  subscribe_data.AddLine(Knot(new string(
          "fname = 'John' AND lname = 'McClane'")));

  NumberedCommandSender::ResultsFuture f =
      subscribe_command->Schedule(subscribe_data, &logger);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  VerifyIStreamContents(list_of(string("COMMAND 0"))("SUBSCRIBE 70")
        ("fname = 'John' AND lname = 'McClane'")("ENDCOMMAND"), 
        &sut_input_stream);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  sut_output_stream << "RESULTS 0\nDONE\nENDRESULTS\nREADY" << endl;

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
    list_of("Command: SUBSCRIBE, command id: 0$")
           ("Command 0 complete. Results: DONE$")("")("");
  // TODO(njhwang) fix this unit test to be compatible with Phase 2 logging
  // formats
  //VerifyTimeStampedInputLines(fake_log_file->str(), exp_lines);
}
