//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for ExtensibleReadyHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 08 May 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE ExtensibleReadyHandlerTest
#include "common/test-init.h"

#include <boost/thread.hpp>
#include <string>
#include <sstream>

#include "common/util.h"
#include "extensible-ready-handler.h"
#include "extensible-ready-handler-fixture.h"

using std::string;
using std::endl;

// Define two very simple protocol extensions.

// This extension doesn't do any further parsing - when it's command is received
// it simply increments num_times_called_ and returns.
class DoCommandExtension : public ProtocolExtension {
 public:
  DoCommandExtension() : num_times_called_(0) {
  }

  virtual void OnProtocolStart(Knot start_line) {
    BOOST_CHECK_EQUAL(start_line, "DO");
    boost::lock_guard<boost::mutex>(this->num_times_called_tex_);
    ++num_times_called_;
    num_times_called_cond_.notify_all();
    Done();
  }

  int num_times_called() {
    boost::lock_guard<boost::mutex> l(num_times_called_tex_);
    return num_times_called_;
  }

  // num_times_called_ will be updated in the input handling thread so the main
  // test thread can't know when the input it's provided was processed without a
  // function like this. This blocks unitl num_times_called_ == n.
  void WaitForNumCalled(int n) {
    boost::unique_lock<boost::mutex> l(num_times_called_tex_);
    while (num_times_called_ < n) {
      num_times_called_cond_.wait(l);
    }
  }

 private:
  int num_times_called_; 
  boost::mutex num_times_called_tex_;
  boost::condition_variable num_times_called_cond_;
};

// This extension expects one more line of data which it saves in its
// line_received_ member.
class BufferLineExtension : public ProtocolExtension {
 public:
  BufferLineExtension() {}

  virtual void OnProtocolStart(Knot start_line) {
    BOOST_CHECK_EQUAL(start_line, "LINE");
    line_received_ = "";
  }

  virtual void LineReceived(Knot data) {
    {
      boost::lock_guard<boost::mutex> l(line_received_tex_);
      line_received_ = data.ToString();
      line_received_cond_.notify_all();
    }
    Done();
  }

  // Block until this has processed a line with the given value.
  void WaitForValue(const string& value) {
    boost::unique_lock<boost::mutex> l(line_received_tex_);
    while (line_received_ != value) {
      line_received_cond_.wait(l);
    }
  }

  const string& line_received() {
      boost::lock_guard<boost::mutex> l(line_received_tex_);
      return line_received_;
  }

 private:
  string line_received_;
  boost::mutex line_received_tex_;
  boost::condition_variable line_received_cond_;
};

// This extension tests that we are in fact triggering on the 1st word on the
// line. It will be registered with "NUMBER" and it expects to have
// OnProtocolStart called with "NUMBER 1", "NUMBER 2", etc. and will use
// BOOST_CHECK_EQUAL to ensure that is, in fact, what is received.
class NumberExtension : public ProtocolExtension {
 public:
  NumberExtension() : next_number_(1) {}
  virtual void OnProtocolStart(Knot start_line) {
    std::stringstream expected_line;
    expected_line << "NUMBER " << next_number_;
    ++next_number_;
    BOOST_CHECK_EQUAL(start_line, expected_line.str());
    Done();
  }

  int GetLastNumberReceived() const {
    return next_number_ - 1;
  }
 private:
  int next_number_;
};

// Create a ExtensibleReadyHandler using the DoCommandExtension and
// BufferLineExtension as extensions. Send it appropriate data and make sure it
// is processed as expected.
BOOST_FIXTURE_TEST_CASE(TestBasicFunctionality, ExtensibleReadyHandlerFixture) {
  FileHandleIStream from_handler(sut_stdout_read_fd);
  FileHandleOStream to_handler(sut_stdin_write_fd);

  DoCommandExtension* do_extension = new DoCommandExtension;
  BufferLineExtension* line_extension = new BufferLineExtension;
  ready_handler->AddHandler("DO", do_extension);
  ready_handler->AddHandler("LINE", line_extension);

  string line;

  // This should block until the stream is written to.
  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line = "";

  to_handler << "DO" << endl;
  do_extension->WaitForNumCalled(1);
  // Note that the CHECK_EQUAL is redundant. If this doesn't equal 1 the above
  // line will deadlock. Still, it seems like a test should have CHECK's...
  BOOST_CHECK_EQUAL(do_extension->num_times_called(), 1);

  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line = "";

  to_handler << "LINE" << endl;
  to_handler << "This should get buffered" << endl;
  line_extension->WaitForValue("This should get buffered");
  // As above, the CHECK_EQUAL is redundant as the test will deadlock if this is
  // false.
  BOOST_CHECK_EQUAL(line_extension->line_received(),
                    "This should get buffered");

  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line = "";
}

// Test that it's the *start* of the line that triggers the sub-protocol and
// that the full line that triggered is passed to the extension.
BOOST_FIXTURE_TEST_CASE(TestTokenIsLineStart, ExtensibleReadyHandlerFixture) {
  FileHandleIStream from_handler(sut_stdout_read_fd);
  FileHandleOStream to_handler(sut_stdin_write_fd);

  NumberExtension* number_extension = new NumberExtension;
  ready_handler->AddHandler("NUMBER", number_extension);

  // This should block until the stream is written to.
  string line;
  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line = "";

  to_handler << "NUMBER 1\n";
  to_handler.flush();

  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line = "";

  to_handler << "NUMBER 2\n";
  to_handler.flush();
  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line = "";

  BOOST_CHECK_EQUAL(number_extension->GetLastNumberReceived(), 2);
}

