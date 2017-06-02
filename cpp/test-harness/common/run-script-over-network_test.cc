//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Test of THRunScriptCommand and THRunScriptHandler. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 20 Sep 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE RunScriptOverNetworkTest
#include "common/test-init.h"

#include <boost/thread.hpp>
#include <memory>

#include "common/network-server.h"
#include "common/network-client.h"
#include "multi-numbered-command-sender.h"
#include "ready-monitor.h"
#include "script-manager.h"
#include "test-script.h"
#include "th-run-script-command.h"
#include "th-run-script-handler.h"
#include "network-protocol-stack.h"

using namespace std;

// This test sets up two full EventLoops with an actual (and thus slightly
// fragile) network connection between two simulated test harness components.
// The "master" then asks the other harness component to run a TestScript and we
// make sure it all worked.

const uint16_t kServerPort = 1235;

class RunScriptNetworkSender : public NetworkProtocolStack {
 public:
  RunScriptNetworkSender(NetworkConnection* connection)
      : NetworkProtocolStack(connection),
        run_script_command(new THRunScriptCommand(
                GetNumberedCommandSender())) {
  }

  virtual ~RunScriptNetworkSender() {}

  auto_ptr<THRunScriptCommand> run_script_command;

};

// The protocol stack for the master.
//
// TODO(odain) Much of this will likely appear here and in at least one
// executable. Consider some refactoring to get better re-use when the time
// comes.
class MasterStack {
 public:
  MasterStack();

  auto_ptr<RunScriptNetworkSender> protocol_stack;
  EventLoop event_loop;
  auto_ptr<NetworkServer> network_server;
 private:
  // Called when the client connects. This will setup the protocol stack with
  // on top of the new connection.
  void ConnectionMade(size_t connection_id, NetworkConnection* connection);
};

MasterStack::MasterStack() {
  // Start listening on a port and start the event loop. When we get a
  // connection we'll call ConnectionMade to set up a protocol stack for the new
  // connection.
  network_server.reset(new NetworkServer(
          HostPort::AnyAddress(kServerPort), &event_loop,
          boost::bind(&MasterStack::ConnectionMade, this, _1, _2)));
  event_loop.Start();
}

void MasterStack::ConnectionMade(size_t connection_id, 
                                 NetworkConnection* connection) {
  // There should only be 1 active network connection.
  BOOST_CHECK(protocol_stack.get() == NULL);
  protocol_stack.reset(new RunScriptNetworkSender(connection));
}

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

// Factory to produce one of these scripts.
TestScript* NoteCalledScriptFactory(bool* called) {
  return new NoteCalledScript(called);
}

// Another script that gets called over the network. Unlike NoteCalledScript,
// this one takes an argument and copies it to the string pointer provided to
// its constructor.]
class CopyArgumentScript : public TestScript {
 public:
  CopyArgumentScript(const LineRawData<Knot>& arguments, string* result)
      : result_(result) {
    // Should be just the argument
    CHECK(arguments.Size() == 1);
    pending_result_ = arguments.Get(0).ToString();
  }

  virtual void Run() {
    boost::this_thread::sleep(boost::posix_time::milliseconds(100));
    *result_ = pending_result_;
  }

 private:
  // We assume a single argument in the arguments LineRawData and we copy it
  // here only putting in the string pointer when the script is complete.
  string pending_result_;
  string* result_;
};

TestScript* CopyArgumentScriptFactory(const LineRawData<Knot>& args,
                                      string* result_location) {
  return new CopyArgumentScript(args, result_location);
}

// Similar to the above, but sets up a stack for the client side of the
// connection.
class ClientStack {
 public:
  ClientStack();
  // Connect to the server and set up the stack.
  void Connect();

  auto_ptr<NetworkClient> network_client; 
  EventLoop event_loop;
  std::auto_ptr<LineRawParser> lr_parser;
  // The LineRawParser owns this so we don't need to free it.
  ExtensibleReadyHandler* ready_handler;
  // The ExtensibleReadyHandler owns this so we don't need to free it.
  NumberedCommandReceiver* nc_receiver;
  ScriptManager script_manager;
  shared_ptr<NetworkConnection> connection;
};

ClientStack::ClientStack() {
  network_client.reset(new NetworkClient(&event_loop));
  event_loop.Start();
}
void ClientStack::Connect() {
  ConnectionStatus cs = 
     network_client->ConnectToServer(HostPort("127.0.0.1", kServerPort));
  BOOST_CHECK_EQUAL(cs.success, true);
  connection = cs.connection;

  ready_handler = new ExtensibleReadyHandler(connection->GetWriteQueue());
  nc_receiver = new NumberedCommandReceiver(connection->GetWriteQueue());
  ready_handler->AddHandler("COMMAND", nc_receiver);
  nc_receiver->AddHandler(
      "RUNSCRIPT", boost::bind(&ConstructTHRunScriptHandler, &script_manager));

  lr_parser.reset(new LineRawParser(ready_handler));
  connection->RegisterDataCallback(
      boost::bind(&LineRawParser::DataReceived, lr_parser.get(), _1));
}

// Tests than I can call a script over the network, have it run, and have it
// return results.
BOOST_AUTO_TEST_CASE(NetworkingWorks) {
  MasterStack master_stack;
  ClientStack client_stack;

  bool script_was_called = false;
  client_stack.script_manager.AddScript(
      "NoteCalledScript",
      boost::bind(&NoteCalledScriptFactory, &script_was_called));

  client_stack.Connect();
  master_stack.network_server->BlockUntilNumConnections(1);
  LineRawData<Knot> script_command_data;
  script_command_data.AddLine(Knot(new string("NoteCalledScript")));

  THRunScriptCommand::ResultsFuture started_f, finished_f;
  master_stack.protocol_stack->run_script_command->SendRunScript(
      script_command_data, started_f, finished_f);

  LOG(DEBUG) << "Waiting for the script to indicate it started";
  started_f.Wait();

  BOOST_REQUIRE_EQUAL(started_f.Value()->results_received.Size(), 1);
  BOOST_REQUIRE_EQUAL(started_f.Value()->results_received.Get(0), "STARTED");

  LOG(DEBUG) << "Waiting for the script to finish";
  finished_f.Wait();

  BOOST_REQUIRE_EQUAL(finished_f.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(finished_f.Value()->results_received.Get(0), "FINISHED");

  BOOST_CHECK_EQUAL(script_was_called, true);

  client_stack.connection->Shutdown();
  master_stack.network_server->StopListening();
  master_stack.event_loop.ExitLoopAndWait();
  client_stack.event_loop.ExitLoopAndWait();
}

// Same as the above, but passes an argument to the script that gets called.
BOOST_AUTO_TEST_CASE(ScriptsWithArgumentsWork) {
  MasterStack master_stack;
  ClientStack client_stack;

  string script_result;
  client_stack.script_manager.AddArgumentScript(
      "CopyArgumentScript",
      boost::bind(&CopyArgumentScriptFactory, _1, &script_result));

  client_stack.Connect();
  master_stack.network_server->BlockUntilNumConnections(1);

  LineRawData<Knot> script_command_data;
  script_command_data.AddLine(Knot(new string("CopyArgumentScript")));
  script_command_data.AddLine(Knot(new string("This is the argument")));

  THRunScriptCommand::ResultsFuture started_f, finished_f;
  master_stack.protocol_stack->run_script_command->SendRunScript(
      script_command_data, started_f, finished_f);

  LOG(DEBUG) << "Waiting for the script to indicate it started";
  started_f.Wait();

  BOOST_REQUIRE_EQUAL(started_f.Value()->results_received.Size(), 1);
  BOOST_REQUIRE_EQUAL(started_f.Value()->results_received.Get(0), "STARTED");

  LOG(DEBUG) << "Waiting for the script to finish";
  finished_f.Wait();

  BOOST_REQUIRE_EQUAL(finished_f.Value()->results_received.Size(), 1);
  BOOST_CHECK_EQUAL(finished_f.Value()->results_received.Get(0), "FINISHED");

  BOOST_CHECK_EQUAL(script_result, "This is the argument");

  client_stack.connection->Shutdown();
  master_stack.network_server->StopListening();
  master_stack.event_loop.ExitLoopAndWait();
  client_stack.event_loop.ExitLoopAndWait();
}
