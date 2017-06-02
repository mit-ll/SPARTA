//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for ReadyMonitor. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 19 Jul 2012   omd            Original Version
//*****************************************************************

#include "ready-monitor.h"

#define BOOST_TEST_MODULE ReadyMonitorTest

#include <boost/thread.hpp>
#include <memory>
#include <unistd.h>

#include "common/test-init.h"
#include "common/util.h"
#include "ready-monitor-fixture.h"


using namespace std;

// Check the simplest case: that our sending commands only after we've received
// a READY signal works.
BOOST_FIXTURE_TEST_CASE(OrderedNonBlockingWorks, ReadyMonitorFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  BOOST_CHECK_EQUAL(ready_monitor->IsReady(), false);
  sut_output_stream << "READY" << endl;
  ready_monitor->WaitUntilReady();
  BOOST_CHECK_EQUAL(ready_monitor->IsReady(), true);

  // We should now be able to send data to the SUT without blocking.
  ready_monitor->BlockUntilReadyAndSend(new Knot(new string("Line 1\n")));
  string sut_received;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "Line 1");
}

BOOST_FIXTURE_TEST_CASE(ScheduledWritesWork, ReadyMonitorFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);
  
  // queue up 3 writes
  ready_monitor->ScheduleSend(new Knot(new string("Line 1\n")));
  ready_monitor->ScheduleSend(new Knot(new string("Line 2\n")));
  ready_monitor->ScheduleSend(new Knot(new string("Line 3\n")));

  // If we look there should be no data in the stream. Until the SUT sends
  // "READY" nothing should be sent.
  char read_buf[2];
  BOOST_CHECK_EQUAL(sut_input_stream.readsome(read_buf, 2), 0);
  // So we send READY. At that point exactly one message should come through.
  sut_output_stream << "READY" << endl;
  string sut_received;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "Line 1");
  // But that's it. There shouldn't be any more data until we send another
  // READY.
  BOOST_CHECK_EQUAL(sut_input_stream.readsome(read_buf, 2), 0);


  sut_output_stream << "READY" << endl;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "Line 2");
  BOOST_CHECK_EQUAL(sut_input_stream.readsome(read_buf, 2), 0);

  sut_output_stream << "READY" << endl;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "Line 3");
}

BOOST_FIXTURE_TEST_CASE(CallbacksWork, ReadyMonitorFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  // Queue up some writes and associate a callback that will set a boolean to
  // true with each callback.
  bool w1 = false;
  ready_monitor->ScheduleSend(
      new Knot(new string("Line 1\n")),
      [&w1](){BOOST_CHECK_EQUAL(w1, false); w1 = true;});

  bool w2 = false;
  ready_monitor->ScheduleSend(
      new Knot(new string("Line 2\n")),
      [&w2](){BOOST_CHECK_EQUAL(w2, false); w2 = true;});

  bool w3 = false;
  ready_monitor->ScheduleSend(
      new Knot(new string("Line 3\n")),
      [&w3](){BOOST_CHECK_EQUAL(w3, false); w3 = true;});

  sut_output_stream << "READY" << endl;
  string sut_received;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "Line 1");
  BOOST_CHECK_EQUAL(w1, true);
  BOOST_CHECK_EQUAL(w2, false);
  BOOST_CHECK_EQUAL(w3, false);

  sut_output_stream << "READY" << endl;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "Line 2");
  BOOST_CHECK_EQUAL(w1, true);
  BOOST_CHECK_EQUAL(w2, true);
  BOOST_CHECK_EQUAL(w3, false);

  sut_output_stream << "READY" << endl;
  getline(sut_input_stream, sut_received);
  BOOST_CHECK_EQUAL(sut_received, "Line 3");
  BOOST_CHECK_EQUAL(w1, true);
  BOOST_CHECK_EQUAL(w2, true);
  BOOST_CHECK_EQUAL(w3, true);
}


// This method will be called in a separate thread. It emulates the SUT and
// sends data to the SUT's stdout. It will send num_ready READY signals to the
// sut_stdout stream, waiting time_to_sleep between each one. This lets us 
void ReadySender(int num_ready, boost::posix_time::time_duration time_to_sleep,
                 FileHandleOStream* sut_stdout) {
  for (int i = 0; i < num_ready; ++i) {
    boost::this_thread::sleep(time_to_sleep);
    (*sut_stdout) << "READY" << endl;
  }
}

// This is called in yet another thread. It emulates the SUT reading from it's
// stdin. It will just buffer up all the data it receives on sut_stdin and put
// it in the received_data vector. The thread exits after receiving num_expected
// lines on it's stdin.
void SUTReader(int num_expected, FileHandleIStream* sut_stdin,
               vector<string>* received_data) {
  for (int i = 0; i < num_expected; ++i) {
    string line;
    getline(*sut_stdin, line);
    received_data->push_back(line);
  } 
}

BOOST_FIXTURE_TEST_CASE(BlockingWritesWork, ReadyMonitorFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  const int kNumReadyWritePairs = 10;
  const boost::posix_time::time_duration kDelayBeforeReady =
      boost::posix_time::milliseconds(100);
  vector<string> received_by_sut;

  boost::thread reading_thread(
      boost::bind(&SUTReader, kNumReadyWritePairs, &sut_input_stream,
                  &received_by_sut));

  boost::thread ready_sending_thread(
      boost::bind(&ReadySender, kNumReadyWritePairs, kDelayBeforeReady,
                  &sut_output_stream));

  for (int i = 0; i < kNumReadyWritePairs; ++i) {
    ostringstream to_send;
    to_send << "Line " << i << "\n";
    ready_monitor->BlockUntilReadyAndSend(new Knot(new string(to_send.str())));
  }

  reading_thread.join();
  BOOST_REQUIRE_EQUAL(received_by_sut.size(), kNumReadyWritePairs);

  for (int i = 0; i < kNumReadyWritePairs; ++i) {
    ostringstream expected;
    expected << "Line " << i;
    BOOST_CHECK_EQUAL(received_by_sut[i], expected.str());
  }
  ready_sending_thread.join();
}
