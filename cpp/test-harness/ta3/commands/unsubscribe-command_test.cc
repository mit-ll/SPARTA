//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for UnsubscribeCommand.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#define BOOST_TEST_MODULE UnsubscribeCommandTest

#include <boost/assign/list_of.hpp>
#include <memory>
#include <sstream>

#include "unsubscribe-command.h"
#include "test-harness/common/numbered-command-fixture.h"
#include "test-harness/common/ready-monitor.h"
#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/test-init.h"
#include "common/test-util.h"
#include "common/util.h"

using namespace std;
using boost::assign::list_of;

class UnsubscribeCommandFixture : public NumberedCommandFixture {
 public:
  UnsubscribeCommandFixture();
  virtual ~UnsubscribeCommandFixture() {}

  unique_ptr<UnsubscribeCommand> unsubscribe_command;
};

UnsubscribeCommandFixture::UnsubscribeCommandFixture() {
  unsubscribe_command.reset(new UnsubscribeCommand(nc_extension));
}

BOOST_FIXTURE_TEST_CASE(UnsubscribeCommandWithLoggingWorks, UnsubscribeCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  sut_output_stream << "READY" << endl;

  LineRawData<Knot> unsubscribe_data;
  // 70 here is the subscription ID.
  unsubscribe_data.AddLine(Knot(new string("70")));

  NumberedCommandSender::ResultsFuture f =
      unsubscribe_command->Schedule(unsubscribe_data, &logger);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  VerifyIStreamContents(list_of(string("COMMAND 0"))("UNSUBSCRIBE 70")
        ("ENDCOMMAND"), &sut_input_stream);

  BOOST_CHECK_EQUAL(f.HasFired(), false);

  sut_output_stream << "RESULTS 0\nDONE\nENDRESULTS" << endl;

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
    list_of("Command: UNSUBSCRIBE, command id: 0")
           ("Command 0 complete. Results: DONE$")("")("");
  // TODO(njhwang) fix this unit test to be compatible with Phase 2 logging
  // formats
  //VerifyTimeStampedInputLines(fake_log_file->str(), exp_lines);
}
