//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit test for ClearCacheHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Oct 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE ClearCacheHandlerTest
#include "common/test-init.h"

#include "clearcache-handler.h"

#include <string>

#include "baseline/common/extensible-ready-handler-fixture.h"
#include "common/util.h"


using namespace std;

// This is a super-simple handler so the test is also simple. Mainly we're
// making sure the data gets sent and there aren't any memory leaks.
BOOST_FIXTURE_TEST_CASE(ClearCacheWorks, ExtensibleReadyHandlerFixture) {
  FileHandleIStream from_handler(sut_stdout_read_fd);
  FileHandleOStream to_handler(sut_stdin_write_fd);

  string result;
  getline(from_handler, result);
  BOOST_CHECK_EQUAL(result, "READY");

  ready_handler->AddHandler(
      "CLEARCACHE",
      new ClearCacheHandler(event_loop.GetWriteQueue(sut_stdout_write_fd))); 

  to_handler << "CLEARCACHE\n";
  to_handler.flush();

  getline(from_handler, result);
  BOOST_CHECK_EQUAL(result, "DONE");

  getline(from_handler, result);
  BOOST_CHECK_EQUAL(result, "READY");
}
