//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for HarnessInfoRequestHandler
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE HarnessInfoRequestHandlerTest

#include <boost/assign/list_of.hpp>
#include <string>
#include <vector>

#include "harness-info-request-handler.h"
#include "common/test-init.h"
#include "common/test-util.h"
#include "common/logging.h"
#include "common/util.h"

#include "baseline/common/numbered-command-receiver-fixture.h"
#include "baseline/common/extensible-ready-handler.h"

using boost::assign::list_of;
using namespace std;

BOOST_FIXTURE_TEST_CASE(HarnessInfoRequestHandlerWorks, 
                        NumberedCommandReceiverFixture) {
  FileHandleIStream from_handler(sut_stdout_read_fd);
  FileHandleOStream to_handler(sut_stdin_write_fd);
  string harness_id = "harness1";
  size_t num_suts = 10;

  auto hirh_factory = 
    [&] () { return HarnessInfoRequestHandlerFactory(&harness_id, &num_suts); };
  command_extension->AddHandler("HARNESS_INFO", hirh_factory);

  // This should block until the stream is written to.
  string line;
  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line.clear();

  to_handler << "COMMAND 0\n"
                "HARNESS_INFO\n"
                "ENDCOMMAND" << endl;

  VerifyIStreamContents(list_of(string("RESULTS 0"))
                               (harness_id + " " + itoa(num_suts))
                               ("ENDRESULTS")("READY"),
                        &from_handler);
}
