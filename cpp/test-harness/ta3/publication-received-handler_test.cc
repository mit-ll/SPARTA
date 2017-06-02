//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit test for PublicationReceivedHandler.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE PublicatonReceivedHandlerTest

#include <boost/assign/list_of.hpp>

#include "publication-received-handler.h"
#include "event-message-fixture.h"
#include "common/string-algo.h"
#include "common/test-init.h"
#include "common/test-util.h"
#include "common/check.h"
#include "common/util.h"

using namespace std;
using boost::assign::list_of;

BOOST_FIXTURE_TEST_CASE(PublicationReceivedHandlerWorks, EventMessageFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  sut_output_stream << "PUBLICATION\nPAYLOAD\n" <<
                       "RAW\n4\nblahENDRAW\nENDPAYLOAD\nENDPUBLICATION\n" <<
                       "PUBLICATION\nPAYLOAD\n" <<
                       "blah\nENDPAYLOAD\nENDPUBLICATION" << endl;

  // Wait a bit to make sure the message is processed.
  boost::this_thread::sleep(boost::posix_time::seconds(2));
  vector<string> exp_lines = 
    list_of("Publication received on SUT [0-9]+. Payload hash: [0-9a-f]{32}")
           ("Publication received on SUT [0-9]+. Payload hash: [0-9a-f]{32}")("");
  VerifyTimeStampedInputLines(fake_log_file->str(), exp_lines);

  boost::this_thread::sleep(boost::posix_time::seconds(2));
  pubrecv_handler->CheckTimeout(2);
}
