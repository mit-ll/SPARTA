//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for EventMessageMonitor
//*****************************************************************

#define BOOST_TEST_MODULE EventMessageMonitorTest
#include "common/test-init.h"

#include <iostream>

#include "event-message-monitor-fixture.h"
#include "event-message-monitor.h"
#include "common/util.h"
#include "common/knot.h"

using namespace std;

BOOST_FIXTURE_TEST_CASE(BasicEventMonitorWorks, EventMessageMonitorFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  std::ostringstream log_output_stream;

  std::mutex log_tex;
  typedef std::function<void (int, int, Knot)> EventCallback;
  EventCallback event_cb = [&log_output_stream, &log_tex](int cmd_id, 
                              int event_id, 
                              Knot data) {
    MutexGuard g(log_tex);
    log_output_stream << "Received event " << event_id << " for command " <<
                          cmd_id << " with extra data [" << data << "]" << endl;
  };

  em_monitor->RegisterCallback(0, event_cb);
  em_monitor->RegisterCallback(1, event_cb);

  LOG(DEBUG) << "Sending EVENTMSGs...";
  sut_output_stream << "EVENTMSG" << endl;
  sut_output_stream << "0 2" << endl;
  sut_output_stream << "EVENTMSG" << endl;
  sut_output_stream << "1 5 some event info" << endl;
  sut_output_stream << "EVENTMSG" << endl;
  sut_output_stream << "0 1" << endl;

  // To prevent race conditions, we wait until the ostringstream has received
  // all of its characters
  while (log_output_stream.str().length() < 116) {}
  BOOST_CHECK_EQUAL(log_output_stream.str(),
      "Received event 2 for command 0 with extra data []\n"
      "Received event 5 for command 1 with extra data [some event info]\n"
      "Received event 1 for command 0 with extra data []\n");
}
