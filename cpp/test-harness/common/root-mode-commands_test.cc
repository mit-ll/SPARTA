//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for root mode commands.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Sep 2012   ni24039        Original Version
//*****************************************************************

#include "root-mode-commands.h"

#define BOOST_TEST_MODULE RootModeCommandsTest
#include "common/test-init.h"
#include "common/test-util.h"

#include <boost/assign/list_of.hpp>
#include <memory>
#include <sstream>

#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/util.h"
#include "test-harness/common/root-mode-command-fixture.h"
#include "test-harness/common/ready-monitor.h"

using namespace std;
using boost::assign::list_of;

class AllRootCommandsFixture : public RootModeCommandFixture {
 public:
  AllRootCommandsFixture();
  virtual ~AllRootCommandsFixture() {}

  auto_ptr<ClearcacheCommand> clearcache_command;
  auto_ptr<ShutdownCommand> shutdown_command;
};

AllRootCommandsFixture::AllRootCommandsFixture() {
  clearcache_command.reset(new ClearcacheCommand(rm_extension));
  shutdown_command.reset(new ShutdownCommand(rm_extension));
}

BOOST_FIXTURE_TEST_CASE(AllCommandsWithLoggingWorks, AllRootCommandsFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  ostringstream* fake_log_file = new ostringstream;
  OstreamElapsedTimeLogger logger(fake_log_file); 
  sut_output_stream << "READY\n";
  sut_output_stream.flush();

  RootModeCommandSender::RootModeResultsFuture f =
      clearcache_command->Schedule(&logger);
  BOOST_CHECK_EQUAL(f.HasFired(), false);

  string line;
  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "CLEARCACHE");
  BOOST_CHECK_EQUAL(f.HasFired(), false);

  sut_output_stream << "DONE\n";
  sut_output_stream << "READY\n";
  sut_output_stream.flush();

  BOOST_REQUIRE_EQUAL(f.Value()->Size(), 1);
  BOOST_CHECK_EQUAL(f.Value()->IsRaw(0), false);
  BOOST_CHECK_EQUAL(f.Value()->Get(0), "DONE");

  shutdown_command->Schedule(&logger);

  getline(sut_input_stream, line);
  BOOST_CHECK_EQUAL(line, "SHUTDOWN");

  // The last "line" should be empty. Since there's a final newline Split puts
  // an additional entry in the vector.
  // The line two lines before that should be empty too. We log exactly what we
  // got and DONE includes a final newline which gets logged in addition to a
  // final newline. I don't think we want to strip off the final newlines as the
  // results could contain binary data.
  vector<string> exp_lines = 
    list_of("Root command CLEARCACHE sent")
           ("Root command CLEARCACHE complete. Results: DONE")
           ("")("Root command SHUTDOWN sent")("");
  VerifyTimeStampedInputLines(fake_log_file->str(), exp_lines);
}
