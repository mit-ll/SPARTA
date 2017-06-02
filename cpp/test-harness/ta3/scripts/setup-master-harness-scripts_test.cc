//*****************************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Unit tests for SetupMasterHarnessScripts
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************************

#define BOOST_TEST_MODULE SetupMasterHarnessScriptsTest
#include "common/test-init.h"

#include <sstream>
#include <fstream>
#include <vector>

#include "setup-master-harness-scripts.h"
#include "test-harness/ta3/master-harness-network-listener.h"
#include "test-harness/ta3/slave-harness-network-stack.h"
#include "test-harness/ta3/server-sut-protocol-stack.h"
#include "test-harness/common/sut-running-monitor.h"
#include "test-harness/common/scripts-from-file.h"
#include "test-harness/common/script-manager.h"
#include "test-harness/common/spawn-sut.h"
#include "test-harness/common/log-file-generator.h"
#include "common/general-logger.h"
#include "common/network-client.h"
#include "common/event-loop.h"
#include "common/util.h"

const uint16_t kServerPort = 1237;
const size_t num_slaves = 5;

using namespace std;

BOOST_AUTO_TEST_CASE(SetupMasterHarnessScriptsWorks) {
  EventLoop master_event_loop;
  SUTRunningMonitor server_sut_monitor;

  ServerSUTProtocolStack protocol_stack;
  int server_stdin_read_fd;
  int server_stdout_write_fd;

  // Set up the function that will set up the notional server SUT's pipes.
  auto pipe_fun = [&](int* sut_stdin, int* sut_stdout) {
    SetupPipes(sut_stdout, &server_stdout_write_fd,
               &server_stdin_read_fd, sut_stdin);
    return 0;
  };

  // Spawn the notional server SUT and build its protocol stack.
  SpawnSUT(pipe_fun, "", false, &master_event_loop, nullptr, nullptr, 
           &protocol_stack,
           std::bind(&SUTRunningMonitor::SUTShutdown, &server_sut_monitor));

  master_event_loop.Start();

  // Start the master listener.
  MasterHarnessNetworkListener master_listener;
  master_listener.StartServer(&master_event_loop, 
                              HostPort::AnyAddress(kServerPort));

  // Set up a bunch of SlaveHarnessNetworkStacks. 
  vector<SlaveHarnessNetworkStack*> slave_stacks;
  vector<ScriptManager*> script_managers;
  vector<NetworkClient*> network_clients;
  vector<EventLoop*> event_loops;
  vector<size_t> perm_num_suts;
  vector<string> perm_harness_ids;
  //vector<SUTRunningMonitor*> client_sut_monitors;
  for (size_t i = 1; i <= num_slaves; i++) {
    EventLoop* slave_event_loop(new EventLoop());
    event_loops.push_back(slave_event_loop);
    //SUTRunningMonitor* client_sut_monitor(new SUTRunningMonitor());
    //client_sut_monitors.push_back(client_sut_monitor);
    slave_event_loop->Start();
    NetworkClient* network_client(new NetworkClient(slave_event_loop));
    network_clients.push_back(network_client);
    LOG(DEBUG) << "Connecting to slave " << i;
    ConnectionStatus cs = 
       network_client->ConnectToServer(HostPort("127.0.0.1", kServerPort));
    BOOST_CHECK_EQUAL(cs.success, true);
    LOG(DEBUG) << "Connected to slave " << i;
    ScriptManager* script_manager(new ScriptManager());
    script_managers.push_back(script_manager);
    string harness_id = "sh" + itoa(i);
    size_t num_suts = i;
    perm_harness_ids.push_back(harness_id);
    perm_num_suts.push_back(num_suts);
    slave_stacks.push_back(new SlaveHarnessNetworkStack(harness_id, 
                                 num_suts, cs.connection, script_manager));
  }

  LOG(DEBUG) << "Waiting for master to recognize " << num_slaves << " slaves...";
  master_listener.BlockUntilNumConnections(num_slaves);
  LOG(DEBUG) << "Master recognized " << num_slaves << " slaves.";

  ScriptsFromFile scripts_from_file;
  ostringstream* fake_log_file = new ostringstream;
  OstreamRawTimeLogger logger(fake_log_file); 

  LOG(DEBUG) << "Setting up master harness scripts...";
  FirstTokenRawTimeLogFileGenerator log_generator("/tmp/", true);
  SetupMasterHarnessScripts(&protocol_stack, &master_listener,
      &scripts_from_file, &server_sut_monitor, &log_generator, 15);
  LOG(DEBUG) << "Set up master harness scripts.";

  for (auto item : slave_stacks) {
    item->Shutdown();
  }

  int slave_count = 0;
  for (auto item : event_loops) {
    LOG(DEBUG) << "Exiting slave event loop #" << slave_count << "...";
    item->ExitLoopAndWait();
    LOG(DEBUG) << "Exited slave event loop #" << slave_count << ".";
    slave_count++;
    delete item;
  }

  for (auto item : slave_stacks) {
    delete item;
  }
  for (auto item : script_managers) {
    delete item;
  }
  for (auto item : network_clients) {
    delete item;
  }

  LOG(DEBUG) << "Exiting master event loop...";
  master_listener.ShutdownServer();
  FileHandleOStream server_output_stream(server_stdout_write_fd);
  server_output_stream.close();
  FileHandleIStream server_input_stream(server_stdin_read_fd);
  server_input_stream.close();
  server_sut_monitor.SetShutdownExpected(true);
  master_event_loop.ExitLoopAndWait();
  LOG(DEBUG) << "Exited master event loop.";
}

