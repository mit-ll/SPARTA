//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for NumberedCommandReceiver 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 May 2012   omd            Original Version
//*****************************************************************

#include "numbered-command-receiver.h"

#define BOOST_TEST_MODULE NumberedCommandReceiverTest
#include "common/test-init.h"

#include <boost/thread.hpp>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "extensible-ready-handler.h"
#include "numbered-command-receiver-fixture.h"
#include "common/logging.h"
#include "common/util.h"

using std::string;
using std::vector;

// Spawns a thread, waits a bit, then calls WriteResults with two lines, the
// first line in the command_data passed to Execute and the line "DONE".
class DelayedDone : public NumberedCommandHandler {
 public:
  virtual ~DelayedDone() {}
  virtual void Execute(LineRawData<Knot>* command_data) {
    // Schedule Go() on a new thread.
    boost::thread runner_thread(
        boost::bind(&DelayedDone::Go, this, command_data));
  }

  void Go(LineRawData<Knot>* command_data) {
    // Sleep for a bit and then call ResultReady.
    boost::this_thread::sleep(boost::posix_time::milliseconds(100));
    LineRawData<Knot> output_data;
    output_data.AddLine(command_data->Get(0));
    output_data.AddLine(Knot(new string("DONE")));
    WriteResults(output_data);
    delete command_data;
    Done();
  }
};

NumberedCommandHandler* ConstructDelayedDone() {
  return new DelayedDone;
};

const int kBigResultsSize = 100 << 20;
// Writes a HUGE results sets to make sure that works.
class BigResults : public NumberedCommandHandler {
 public:
  virtual ~BigResults() {}
  virtual void Execute(LineRawData<Knot>* command_data) {
    boost::thread runner_thread(boost::bind(&BigResults::Go, this));
    delete command_data;
  }

  void Go() {
    LineRawData<Knot> results;
    Knot long_line;
    // A huge string of 'a' characters.
    string* long_line_str = new string(kBigResultsSize, 'a');
    results.AddLine(Knot(long_line_str));
    WriteResults(results);
    Done();
  }
};

NumberedCommandHandler* ConstructBigResults() {
  return new BigResults;
}

BOOST_FIXTURE_TEST_CASE(NumberedCommandWorks, NumberedCommandReceiverFixture) {
  FileHandleIStream from_handler(sut_stdout_read_fd);
  FileHandleOStream to_handler(sut_stdin_write_fd);

  command_extension->AddHandler("DD", ConstructDelayedDone);

  // This should block until the stream is written to.
  string line;
  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line.clear();

  // Inputs that should cause DelayedDone to be invoked twice.
  to_handler << "COMMAND 1\n"
                 "DD foo\n"
                 "ENDCOMMAND\n"
                 "COMMAND 2\n"
                 "DD bar\n"
                 "ENDCOMMAND\n";
  to_handler.flush();

  // Read lines from the pipe until we see 2 more READY signals and results for
  // the two command above.
  vector<string> results;
  int num_ready = 0;
  int num_results = 0;
  while (num_results < 2 && num_results < 2) {
    getline(from_handler, line);
    if (line == "READY") {
      ++num_ready;
    } else if (line == "ENDRESULTS") {
      ++num_results;
    }

    results.push_back(line);
    line.clear();
  }

  // This shouldn't have to wait since the above waited for the commands to not
  // only finish, but the results to arrive at the end of the pipe.
  command_extension->WaitForAllCommands();

  // Now we should have received 2 READY signals, one after each command we
  // sent. Normally both would happen at once since the results of the commands
  // are delayed. However, there is no guarantee of that as both threads could
  // have been delayed until the sleep expired at which point the command might
  // complete before the READY token was produced. Thus, to be robust, we only
  // check that we got 2 ready signals. However, if any of them came after a set
  // of results we write a warning as we don't expect this to happen often.
  int num_ready_found = 0;
  for (size_t i = 0; i < results.size(); ++i) {
    if (results[i] == "READY") {
      ++num_ready_found;
      if (i > 1) {
        LOG(WARNING) << "Found READY after results. Unexpected.";
      }
    }
  }
  BOOST_CHECK_EQUAL(num_ready_found, 2);


  // We should also get results for command 1 and command 2. Since these ran in
  // different threads there is no ordering guarantee. However, for any one set
  // of results we know what the next few lines should be.
  int num_results_found = 0;
  for (size_t i = 0; i < results.size(); ++i) {
    if (results[i] == "RESULTS 1") {
      num_results_found += 1;
      BOOST_REQUIRE_LT(i + 2, results.size());
      BOOST_CHECK_EQUAL(results[i + 1], "DD foo");
      BOOST_CHECK_EQUAL(results[i + 2], "DONE");
    }
    if (results[i] == "RESULTS 2") {
      num_results_found += 1;
      BOOST_REQUIRE_LT(i + 2, results.size());
      BOOST_CHECK_EQUAL(results[i + 1], "DD bar");
      BOOST_CHECK_EQUAL(results[i + 2], "DONE");
    }
  }
  BOOST_CHECK_EQUAL(num_results_found, 2);
}

// Really big results are sent through a slightly different output path since
// they are too big to be queued for output. This test ensures that these
// commands work.
BOOST_FIXTURE_TEST_CASE(BigResultsWork, NumberedCommandReceiverFixture) {
  FileHandleIStream from_handler(sut_stdout_read_fd);
  FileHandleOStream to_handler(sut_stdin_write_fd);

  command_extension->AddHandler("BIG", &ConstructBigResults);

  string line;
  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "READY");
  line.clear();

  to_handler << "COMMAND 107\nBIG\nENDCOMMAND\n";
  to_handler.flush();

  // Ignore the READY line if that gets sent first.
  do {
    getline(from_handler, line);
  } while (line == "READY");
  BOOST_CHECK_EQUAL(line, "RESULTS 107");
  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, string(kBigResultsSize, 'a'));
  getline(from_handler, line);
  BOOST_CHECK_EQUAL(line, "ENDRESULTS");
}
