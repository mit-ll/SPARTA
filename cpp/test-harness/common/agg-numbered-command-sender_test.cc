//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for AggNumberedCommandSender 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Nov 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE AggNumberedCommandSenderTest
#include "common/test-init.h"

#include <iostream>

#include "common/aggregating-future.h"
#include "common/types.h"
#include "common/util.h"
#include "agg-numbered-command-fixture-with-event-monitor.h"
#include "agg-numbered-command-fixture.h"
#include "agg-numbered-command-sender.h"
#include "ready-monitor-fixture.h"

using namespace std;

// Aggregator that returns the total number of characters it's observed.
class CharCountAggregator : public FutureAggregator<int, Knot> {
 public:
  CharCountAggregator() : count_(0) {}
  virtual ~CharCountAggregator() {}

  virtual void AddPartialResult(const Knot& data) {
    count_ += data.Size();
  }

 protected:
  virtual int Finalize() {
    return count_;
  }

 private:
  int count_;
};

// TODO(odain) This needs more tests. Specifically add some where multiple
// commands are executed concurrently and they return results out of order.
BOOST_FIXTURE_TEST_CASE(BasicAggregationWorks, AggNumberedCommandFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);

  std::unique_ptr<CharCountAggregator> cc_agg(new CharCountAggregator);
  Future<int> f = cc_agg->GetFuture();

  sut_output_stream << "READY" << endl;

  int command_id;
  nc_sender->SendCommand(
      Knot(new string("This is my command\n")), std::move(cc_agg), &command_id);

  string sut_received_line;
  getline(sut_input_stream, sut_received_line);
  BOOST_CHECK_EQUAL(sut_received_line, "COMMAND 0");
  getline(sut_input_stream, sut_received_line);
  BOOST_CHECK_EQUAL(sut_received_line, "This is my command");
  getline(sut_input_stream, sut_received_line);
  BOOST_CHECK_EQUAL(sut_received_line, "ENDCOMMAND");

  sut_output_stream << "RESULTS " << command_id
      << "\nHi there\nRAW\n2\nabENDRAW\nENDRESULTS" << endl;
  sut_output_stream << "READY" << endl;

  f.Wait();

  // "Hi there" is 8 characters plus the 2 we sent as raw data is 10 total
  // bytes.
  BOOST_CHECK_EQUAL(f.Value(), 10);
}

BOOST_FIXTURE_TEST_CASE(EventHandlingWorks, 
                        AggNumberedCommandWithEventMonitorFixture) {
  FileHandleOStream sut_output_stream(sut_stdout_write_fd);
  FileHandleIStream sut_input_stream(sut_stdin_read_fd);
  std::ostringstream log_output_stream;

  std::unique_ptr<CharCountAggregator> cc_agg(new CharCountAggregator);
  Future<int> f = cc_agg->GetFuture();

  sut_output_stream << "READY" << endl;

  int command_id;
  std::mutex log_tex;

  typedef std::function<void (int)> SentCallback;
  typedef std::function<void (int, int, Knot)> EventCallback;
  SentCallback sent_cb = [&log_output_stream, &log_tex](int cmd_id) {
    MutexGuard g(log_tex);
    log_output_stream << "Sent command " << cmd_id << endl;
  };
  EventCallback event_cb = [&log_output_stream, &log_tex](int cmd_id, 
                                                          int event_id, 
                                                          Knot data) {
    MutexGuard g(log_tex);
    log_output_stream << "Received event " << event_id << " for command "
                      << cmd_id << " with extra data [" << data << "]" << endl;
  };

  nc_sender->SendCommand(
      Knot(new string("This is my command\n")), std::move(cc_agg), &command_id,
      sent_cb, event_cb);

  string sut_received_line;
  getline(sut_input_stream, sut_received_line);
  BOOST_CHECK_EQUAL(sut_received_line, "COMMAND 0");
  getline(sut_input_stream, sut_received_line);
  BOOST_CHECK_EQUAL(sut_received_line, "This is my command");
  getline(sut_input_stream, sut_received_line);
  BOOST_CHECK_EQUAL(sut_received_line, "ENDCOMMAND");

  sut_output_stream << "RESULTS " << command_id
      << "\nSo \nRAW\n2\nahENDRAW" << endl;
  sut_output_stream << "EVENTMSG\n0 5" << endl;
  sut_output_stream << "What's up doc" << endl;
  sut_output_stream << "EVENTMSG\n0 3 Wascally Wabbit" << endl;
  sut_output_stream << "EVENTMSG\n0 2" << endl;
  sut_output_stream << "That's all folks\nENDRESULTS" << endl;
  sut_output_stream << "READY" << endl;

  f.Wait();

  BOOST_CHECK_EQUAL(f.Value(), 34);
  BOOST_CHECK_EQUAL(log_output_stream.str(),
      "Sent command 0\n"
      "Received event 5 for command 0 with extra data []\n"
      "Received event 3 for command 0 with extra data [Wascally Wabbit]\n"
      "Received event 2 for command 0 with extra data []\n");
}
