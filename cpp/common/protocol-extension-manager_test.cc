//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for ProtocolExtensionManager 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 08 May 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE ProtocolExtensionManagerTest

#include <boost/thread.hpp>
#include <string>
#include <sstream>
#include <unistd.h>

#include "line-raw-parser.h"
#include "protocol-extension-manager.h"
#include "statics.h"
#include "test-init.h"
#include "types.h"

using std::string;
using std::ostream;
using std::istream;
using std::endl;

// Define a few simple protocol extensions.

// This extension doesn't do any further parsing - when it's command is received
// it simply increments num_times_called_ and returns.
class DoCommandExtension : public ProtocolExtension {
 public:
  DoCommandExtension() : num_times_called_(0) {
  }

  virtual void OnProtocolStart(Knot start_line) {
    BOOST_CHECK_EQUAL(start_line, "DO");
    ++num_times_called_;
    Done();
  }

  int num_times_called() {
    return num_times_called_;
  }

 private:
  int num_times_called_; 
};

// This extension expects to be triggered by "LINE" and then recieve one line of
// data and one chunk of RAW data.
class BufferExtension : public ProtocolExtension {
 public:
  BufferExtension() : got_line_(false) {}

  virtual void OnProtocolStart(Knot start_line) {
    BOOST_CHECK_EQUAL(start_line, "LINE");
  }

  virtual void LineReceived(Knot data) {
    BOOST_CHECK_EQUAL(got_line_, false);
    line_received_ = data;
    got_line_  = true;
  }

  virtual void RawReceived(Knot data) {
    BOOST_CHECK_EQUAL(got_line_, true);
    raw_received_ = data;
    Done();
  }

  Knot line_received_;
  Knot raw_received_;

 private:
  bool got_line_;
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

Strand* GetStrand(const char* data) {
  return new StringStrand(new string(data));
}

// Create a ProtocolExtensionManager using the DoCommandExtension and
// BufferLineExtension as extensions. Send it appropriate data and make sure it
// is processed as expected.
BOOST_AUTO_TEST_CASE(TestBasicFunctionality) {
  ProtocolExtensionManager* manager = new ProtocolExtensionManager;
  DoCommandExtension* do_extension = new DoCommandExtension;
  BufferExtension* buffer_extension = new BufferExtension;
  manager->AddHandler("DO", do_extension);
  manager->AddHandler("LINE", buffer_extension);

  LineRawParser parser(manager);


  parser.DataReceived(GetStrand("DO\n"));
  BOOST_CHECK_EQUAL(do_extension->num_times_called(), 1);

  parser.DataReceived(GetStrand("LINE\n"));
  parser.DataReceived(GetStrand("This should get buffered\n"));
  parser.DataReceived(GetStrand("RAW\n3\nabcENDRAW\n"));
  // As above, the CHECK_EQUAL is redundant as the test will deadlock if this is
  // false.
  BOOST_CHECK_EQUAL(buffer_extension->line_received_,
                    "This should get buffered");
  BOOST_CHECK_EQUAL(buffer_extension->raw_received_, "abc");

  parser.DataReceived(GetStrand("DO\n"));
  BOOST_CHECK_EQUAL(do_extension->num_times_called(), 2);
  parser.DataReceived(GetStrand("DO\n"));
  BOOST_CHECK_EQUAL(do_extension->num_times_called(), 3);
}

// Test that it's the *start* of the line that triggers the sub-protocol and
// that the full line that triggered is passed to the extension.
BOOST_AUTO_TEST_CASE(TestTokenIsLineStart) {
  ProtocolExtensionManager* manager = new ProtocolExtensionManager;
  NumberExtension* number_extension = new NumberExtension;
  manager->AddHandler("NUMBER", number_extension);

  LineRawParser parser(manager);

  parser.DataReceived(GetStrand("NUMBER 1\n"));
  parser.DataReceived(GetStrand("NUMBER 2\n"));

  BOOST_CHECK_EQUAL(number_extension->GetLastNumberReceived(), 2);
}

