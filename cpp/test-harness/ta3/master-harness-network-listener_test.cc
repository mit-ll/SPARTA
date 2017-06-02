//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039 
// Description:        Unit test for MasterHarnessNetworkListener
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#define BOOST_TEST_MODULE MasterHarnessNetworkListenerTest
#include "common/test-init.h"

#include <memory>
#include <vector>

#include "master-harness-network-listener.h"
#include "slave-harness-network-stack.h"
#include "test-harness/common/script-manager.h"
#include "common/network-client.h"

const uint16_t kServerPort = 1236;
const size_t num_slaves = 5;

using namespace std;

BOOST_AUTO_TEST_CASE(MasterHarnessNetworkListenerWorks) {
  EventLoop master_event_loop;
  master_event_loop.Start();

  MasterHarnessNetworkListener master_listener;
  master_listener.StartServer(&master_event_loop, HostPort::AnyAddress(kServerPort));

  vector<SlaveHarnessNetworkStack*> slave_stacks;
  vector<ScriptManager*> script_managers;
  vector<NetworkClient*> network_clients;
  vector<EventLoop*> event_loops;
  vector<size_t> perm_num_suts;
  vector<string> perm_harness_ids;
  for (size_t i = 1; i <= num_slaves; i++) {
    EventLoop* slave_event_loop(new EventLoop());
    event_loops.push_back(slave_event_loop);
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
    SlaveHarnessNetworkStack* slave_stack = 
      new SlaveHarnessNetworkStack(harness_id, num_suts, 
                                   cs.connection, script_manager);
    slave_stack->Start();
    slave_stacks.push_back(slave_stack);
  }

  LOG(DEBUG) << "Waiting for master to recognize " << num_slaves << " slaves...";
  master_listener.BlockUntilNumConnections(num_slaves);
  LOG(DEBUG) << "Updating network map...";
  master_listener.UpdateNetworkMap();

  for (size_t i = 0; i < num_slaves; i++) {
    string harness_id = perm_harness_ids[i];
    auto sut_ids = master_listener.GetClientSUTIDs(harness_id);
    for (auto sut_id : *sut_ids) {
      BOOST_CHECK_EQUAL(master_listener.GetSlaveHarnessID(sut_id), harness_id);
      BOOST_CHECK_EQUAL(master_listener.GetProtocolStack(sut_id), 
                        master_listener.GetProtocolStack(harness_id));
      BOOST_CHECK_EQUAL(
          master_listener.GetProtocolStack(sut_id)->GetSlaveHarnessInfo(), 
          harness_id + " " + itoa(i + 1));
    }
  }

  master_listener.ShutdownServer();

  for (auto item : slave_stacks) {
    item->Shutdown();
    delete item;
  }
  for (auto item : script_managers) {
    delete item;
  }
  for (auto item : network_clients) {
    delete item;
  }
  for (auto item : event_loops) {
    delete item;
  }
}
