//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039 
// Description:        Unit test for SlaveHarnessNetworkStack 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   ni24039        Original Version
//*****************************************************************

#define BOOST_TEST_MODULE SlaveHarnessNetworkStackTest
#include "common/test-init.h"

#include <boost/thread.hpp>
#include <memory>

#include "slave-harness-network-stack.h"
#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/common/network-protocol-stack.h"
#include "test-harness/common/th-run-script-command.h"
#include "test-harness/common/th-run-script-handler.h"
#include "test-harness/common/script-manager.h"
#include "test-harness/common/test-script.h"
#include "common/network-server.h"
#include "common/network-client.h"

using namespace std;
typedef NumberedCommandSender::ResultsFuture ResultsFuture;
typedef NumberedCommandSender::SharedResults SharedResults;

const uint16_t kServerPort = 1245;

// Test class emulating a typical master harness network protocol stack.
class MasterNetworkProtocolStack : public NetworkProtocolStack {
  public:
   MasterNetworkProtocolStack(NetworkConnection* connection)
     : NetworkProtocolStack(connection),
       run_script_command(new THRunScriptCommand(GetNumberedCommandSender())) {}

   virtual ~MasterNetworkProtocolStack() {}

   // Sends command_data as a numbered command and returns a Resultsfuture that
   // can be waited on for the corresponding numbered results.
   ResultsFuture SendNumberedCommand(Knot command_data) {
     int to_discard;
     ResultsFuture future;
     GetNumberedCommandSender()->SendCommand(
         command_data,
         boost::bind(&MasterNetworkProtocolStack::ResultsReceived, 
                     this, _1, future), 
         &to_discard);
     return future;
   }

   unique_ptr<THRunScriptCommand> run_script_command;

  private:
   // Callback for calls to GetNumberedCommandSender()->SendCommand(). Fires the
   // future and removes the callback from the command sender.
   void ResultsReceived(SharedResults results, ResultsFuture future) {
     future.Fire(results);
     GetNumberedCommandSender()->RemoveCallback(results->command_id);
   }
};

// Test class emulating a typical master harness component.
class MasterHarness {
 public:
  MasterHarness() {
    // Start listening on a port and start the event loop. When we get a
    // connection we'll call ConnectionMade to set up a protocol stack for the
    // new connection.
    network_server.reset(new NetworkServer(
            HostPort::AnyAddress(kServerPort), &event_loop,
            boost::bind(&MasterHarness::ConnectionMade, this, _1, _2)));
    event_loop.Start();
  }

  unique_ptr<MasterNetworkProtocolStack> protocol_stack;
  EventLoop event_loop;
  unique_ptr<NetworkServer> network_server;

 private:
  // Called when the client connects. This will setup the protocol stack with
  // on top of the new connection.
  void ConnectionMade(size_t connection_id, NetworkConnection* connection) {
    // There should only be 1 active network connection.
    BOOST_CHECK(protocol_stack.get() == nullptr);
    protocol_stack.reset(new MasterNetworkProtocolStack(connection));
  }
};

// This is the script that's going to be called over the network. It does
// nothing but change the called boolean passed to its constructor from false to
// true after waiting a few milliseconds.
class NoteCalledScript : public TestScript {
 public:
  NoteCalledScript(bool* called) : called_(called) {
    CHECK(*called == false);
  }

  virtual ~NoteCalledScript() {}

  virtual void Run() {
    boost::this_thread::sleep(boost::posix_time::milliseconds(100));
    *called_ = true;
  }

 private:
  bool* called_;
};

// Factory to produce a NoteCalledScript.
TestScript* NoteCalledScriptFactory(bool* called) {
  return new NoteCalledScript(called);
}

BOOST_AUTO_TEST_CASE(SlaveHarnessNetworkStackWorks) {
  string harness_id = "harness1";
  size_t num_suts = 10;

  MasterHarness master_harness;
  EventLoop event_loop;

  // Set up the slave harness' script manager.
  ScriptManager script_manager;
  bool script_was_called = false;
  script_manager.AddScript("NoteCalledScript",
      boost::bind(&NoteCalledScriptFactory, &script_was_called));

  // Establish the slave harness' connection to the master harness.
  unique_ptr<NetworkClient> network_client(new NetworkClient(&event_loop));
  event_loop.Start();
  LOG(DEBUG) << "Connecting to server...";
  ConnectionStatus cs = 
     network_client->ConnectToServer(HostPort("127.0.0.1", kServerPort));
  LOG(DEBUG) << "Connected to server.";
  BOOST_CHECK_EQUAL(cs.success, true);
  std::shared_ptr<NetworkConnection> connection = cs.connection;

  // Initialize the slave harness' network stack.
  LOG(DEBUG) << "Setting up network stack...";
  SlaveHarnessNetworkStack slave_stack(
      harness_id, num_suts, connection, &script_manager);
  slave_stack.Start();
  LOG(DEBUG) << "Set up network stack.";

  // Wait until the master harness is ready to send commands to the slave
  // harness.
  LOG(DEBUG) << "Blocking until connection detected...";
  master_harness.network_server->BlockUntilNumConnections(1);
  LOG(DEBUG) << "Connection detected.";
  LOG(DEBUG) << "Waiting for ready...";
  master_harness.protocol_stack->GetReadyMonitor()->WaitUntilReady();
  LOG(DEBUG) << "Received ready.";

  // Request HARNESS_INFO from the slave harness.
  ResultsFuture future = master_harness.protocol_stack->SendNumberedCommand(
      Knot(new string("HARNESS_INFO\n")));

  // Verify that the harness information is correct.
  LOG(DEBUG) << "Waiting for harness info...";
  LineRawData<Knot> results = future.Value()->results_received;
  LOG(DEBUG) << "Received harness info...";
  BOOST_CHECK_EQUAL(results.Size(), 1);
  BOOST_CHECK(!results.IsRaw(0));
  BOOST_CHECK_EQUAL(results.Get(0).ToString(), 
                    harness_id + " " + itoa(num_suts)); 
  LOG(DEBUG) << "Waiting for ready...";
  master_harness.protocol_stack->GetReadyMonitor()->WaitUntilReady();
  LOG(DEBUG) << "Received ready.";

  // Request a NoteCalledScript to be run by the slave harness.
  LineRawData<Knot> script_command_data;
  script_command_data.AddLine(Knot(new string("NoteCalledScript")));
  THRunScriptCommand::ResultsFuture started_f, finished_f;
  master_harness.protocol_stack->run_script_command->SendRunScript(
      script_command_data, started_f, finished_f);

  // Verify that the slave harness correctly processed the RUNSCRIPT command.
  LOG(DEBUG) << "Waiting for the script to indicate it started";
  started_f.Wait();
  BOOST_REQUIRE_EQUAL(started_f.Value()->results_received.Size(), 1);
  BOOST_REQUIRE_EQUAL(started_f.Value()->results_received.Get(0), "STARTED");
  LOG(DEBUG) << "Waiting for the script to finish";
  finished_f.Wait();
  BOOST_REQUIRE_EQUAL(finished_f.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(finished_f.Value()->results_received.Get(0), "FINISHED");
  BOOST_CHECK_EQUAL(script_was_called, true);

  // Tidy up.
  LOG(DEBUG) << "Waiting for final READY...";
  master_harness.protocol_stack->GetReadyMonitor()->WaitUntilReady();
  LOG(DEBUG) << "Shutting down network server...";
  master_harness.network_server->StopListening();
  LOG(DEBUG) << "Shutting down connection...";
  connection->Shutdown();
  LOG(DEBUG) << "Waiting for slave harness event loop to finish...";
  event_loop.ExitLoopAndWait();
  LOG(DEBUG) << "Waiting for master harness event loop to finish...";
  master_harness.event_loop.ExitLoopAndWait();
}
