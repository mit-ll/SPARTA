//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for PublishCommand.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#define BOOST_TEST_MODULE PublishCommandTest

#include <boost/assign/list_of.hpp>
#include <memory>
#include <sstream>

#include "publish-command.h"
#include "test-harness/common/numbered-command-fixture.h"
#include "test-harness/common/ready-monitor.h"
#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/test-init.h"
#include "common/test-util.h"
#include "common/util.h"

using namespace std;
using boost::assign::list_of;

class PublishCommandFixture : public NumberedCommandFixture {
 public:
  PublishCommandFixture();
  virtual ~PublishCommandFixture() {}

  unique_ptr<PublishCommand> publish_command;
};

PublishCommandFixture::PublishCommandFixture() {
  publish_command.reset(new PublishCommand(nc_extension));
}

BOOST_FIXTURE_TEST_CASE(PublishCommandWithLoggingWorks, PublishCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  sut_output_stream << "READY" << endl;

  LineRawData<Knot> publish_data;
  // This is the publication metadata.
  publish_data.AddLine(Knot(new string("John,McClane,123456789,1955-05-23")));
  // This is the publication payload.
  publish_data.AddLine(Knot(new string("Come out to the coast...")));
  publish_data.AddRaw(Knot(
        new string("We'll get together, have a few laughs...")));
  publish_data.AddLine(Knot(new string("Grab a few beers...")));

  NumberedCommandSender::ResultsFuture f =
      publish_command->Schedule(publish_data, &logger);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  VerifyIStreamContents(list_of(string("COMMAND 0"))("PUBLISH")
      ("METADATA")("John,McClane,123456789,1955-05-23")("PAYLOAD")
      ("Come out to the coast...")("RAW")("40") 
      ("We'll get together, have a few laughs...ENDRAW")
      ("Grab a few beers...")("ENDPAYLOAD")("ENDPUBLISH")("ENDCOMMAND"),
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
    list_of(string("Command: PUBLISH, command id: 0, ")
            + "metadata: John,McClane,123456789,1955-05-23, "
            + "payload hash: [0-9a-f]{32}, payload length: 83")
           ("Command 0 complete. Results: DONE$")("")("");
  // TODO(njhwang) fix this unit test to be compatible with Phase 2 logging
  // formats
  //VerifyTimeStampedInputLines(fake_log_file->str(), exp_lines);
}
