//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit test for the unsubscribe script
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#include "unsubscribe-script.h"

#define BOOST_TEST_MODULE UnsubscribeScriptTest
#include "common/test-init.h"
#include "common/test-util.h"

#include <boost/assign/list_of.hpp>
#include <boost/thread.hpp>
#include <boost/bind.hpp>
#include <iostream>

#include "unsubscribe-script.h"
#include "test-harness/ta3/multi-client-sut-protocol-stack.h"
#include "test-harness/ta3/slave-harness-network-stack.h"
#include "test-harness/ta3/commands/unsubscribe-command.h"
#include "test-harness/ta3/client-sut-protocol-stack.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/script-manager.h"
#include "common/network-connection.h"
#include "common/general-logger.h"
#include "common/event-loop.h"
#include "common/util.h"

using namespace std;
using boost::assign::list_of;

BOOST_AUTO_TEST_CASE(UnsubscribeScriptWorks) {
  EventLoop event_loop;

  size_t num_suts = 5;
  int sut_stdin_read_fds[num_suts];
  int sut_stdout_write_fds[num_suts];
  int suts_spawned = 0;

  vector<SUTRunningMonitor*> sut_monitors;
  for (size_t i = 0; i < num_suts; i++) {
    sut_monitors.push_back(new SUTRunningMonitor());
  }

  // Set up the function that will set up the notional SUTs' pipes.
  auto pipe_fun = [&](int* sut_stdin, int* sut_stdout, string args) {
    SetupPipes(sut_stdout, &sut_stdout_write_fds[suts_spawned],
               &sut_stdin_read_fds[suts_spawned], sut_stdin);
    suts_spawned++;
    return 0;
  };

  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  std::shared_ptr<NetworkConnection> 
    dummy_conn(new NetworkConnection(0, &event_loop));
  ScriptManager dummy_sm;
  SlaveHarnessNetworkStack network_stack("dummy_harness_id", 1, 
    dummy_conn, &dummy_sm);
  vector<string> dummy_args(1, "");
  MultiClientSUTProtocolStack protocol_stack(
      pipe_fun, "", false, &event_loop, num_suts, 
      &network_stack, sut_monitors, dummy_args, &logger);

  event_loop.Start();

  vector<FileHandleOStream*> sut_output_streams;
  vector<FileHandleIStream*> sut_input_streams;
  for (size_t i = 0; i < num_suts; i++) {
    // Set up access to the notional SUT's stdin/out.
    sut_output_streams.push_back(new FileHandleOStream(sut_stdout_write_fds[i]));
    sut_input_streams.push_back(new FileHandleIStream(sut_stdin_read_fds[i]));
    ClientSUTProtocolStack* client_ps = protocol_stack.GetProtocolStack(i); 

    LOG(DEBUG) << "SUT sending READY...";
    *sut_output_streams[i] << "READY" << endl;
    client_ps->WaitUntilReady();
  }

  LineRawData<Knot> subscription_data;
  subscription_data.AddLine(Knot(new string("0 0")));
  subscription_data.AddLine(Knot(new string("1 10")));

  UnsubscribeScript script(subscription_data, &protocol_stack, &logger);
  boost::thread script_thread(
      boost::bind(&UnsubscribeScript::Run, &script));

  boost::this_thread::sleep(boost::posix_time::milliseconds(100));

  VerifyIStreamContents(list_of(string("COMMAND 0"))("UNSUBSCRIBE 0")
    ("ENDCOMMAND"), sut_input_streams[0]);
  *sut_output_streams[0] << "READY" << endl;
  boost::this_thread::sleep(boost::posix_time::milliseconds(100));
  BOOST_CHECK_EQUAL(sut_input_streams[0]->rdbuf()->in_avail(), 0);
  *sut_output_streams[0] << "RESULTS 0\n"
      "DONE\n"
      "ENDRESULTS" << endl;

  VerifyIStreamContents(list_of(string("COMMAND 1"))("UNSUBSCRIBE 10")
    ("ENDCOMMAND"), sut_input_streams[1]);
  *sut_output_streams[1] << "READY" << endl;
  boost::this_thread::sleep(boost::posix_time::milliseconds(100));
  BOOST_CHECK_EQUAL(sut_input_streams[1]->rdbuf()->in_avail(), 0);
  *sut_output_streams[1] << "RESULTS 1\n"
      "DONE\n"
      "ENDRESULTS" << endl;

  script_thread.join();
  network_stack.Shutdown();  
  for (auto item : sut_monitors) {
    item->SetShutdownExpected(true);
  }
  for (auto item : sut_output_streams) {
    item->close();
  }
  event_loop.ExitLoopAndWait();

  for (auto item : sut_monitors) {
    delete item;
  }
  for (auto item : sut_output_streams) {
    delete item;
  }
  for (auto item : sut_input_streams) {
    delete item;
  }
}
