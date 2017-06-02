//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Sets up a protocol stack for the test harness component
//                     that acts as the "master" 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_MASTER_HARNESS_NETWORK_LISTENER_H_
#define CPP_TEST_HARNESS_TA3_MASTER_HARNESS_NETWORK_LISTENER_H_

#include "test-harness/common/network-protocol-stack.h"
#include "test-harness/common/numbered-command-sender.h"
#include "test-harness/common/th-run-script-command.h"
#include "common/network-server.h"

class EventLoop;
class ProtocolExtensionManager;
class ReadyMonitor;
class THRunScriptCommand;
class NetworkServer;

/// The set of commands the master harness components needs to support in order
/// to command slave harnesses over our network connection.
class MasterHarnessProtocolStack : public NetworkProtocolStack {
  public:
   MasterHarnessProtocolStack(NetworkConnection* connection);
   virtual ~MasterHarnessProtocolStack() {}

   THRunScriptCommand* GetRunScriptCommand() {
     return run_script_command_.get();
   }

   /// Retrieves harness information from a remotely connected harness component.
   std::string GetSlaveHarnessInfo();

  private:
   /// Callback that is called when a remotely connected harness component sends
   /// a response to a harness info request.
   void SlaveHarnessInfoReceived(
       NumberedCommandSender::SharedResults results,
       NumberedCommandSender::ResultsFuture future);

   std::unique_ptr<THRunScriptCommand> run_script_command_;
};

/// One test harness component is the "master". It initiates all tests scripts
/// either by starting them itself or by asking other test harness components to
/// do things. In order to do that it has to communicate over the network with
/// the other components. This sets up a server that listens on a port for
/// connections for other network components. When a connection is established
/// this builds a protocol stack with a set of command handlers "at the top" that
/// can send commands to other test harness components.
class MasterHarnessNetworkListener {
 public:
  MasterHarnessNetworkListener();

  virtual ~MasterHarnessNetworkListener() {
    for (auto item : protocol_stacks_) {
      delete item;
    }
    for (auto item : harness_sut_map_) {
      delete item.second;
    }
  }

  /// Opens the server connection on theh given HostPort and listens for client
  /// connections.
  void StartServer(EventLoop* event_loop, HostPort listen_addr_port);
  void ShutdownServer();

  /// Blocks until the given number of test harness components have connected.
  void BlockUntilNumConnections(size_t num_conn);

  /// Returns the total number of client SUTs that can be communicated with by
  /// this listener.
  size_t GetNumClientSUTs();

  /// Returns the total number of client SUTs that can be communicated with by
  /// this listener.
  size_t GetNumSlaveHarnesses();

  /// Retrieves slave harness info from all remote connections and updates all
  /// data structures that maintain protocol stack information for each slave
  /// harness and client SUT. This should be called after
  /// BlockUntilNumConnections to guarantee that a sufficient number of slaves
  /// have connected to the master. Note that this will completely refresh all
  /// data structures that maintain harness/SUT ID mappings, so callers should
  /// not expect any previous mappings to be intact after a new call to
  /// UpdateNetworkMap.
  void UpdateNetworkMap();

  typedef MasterHarnessProtocolStack* MHPSPtr;
  /// Retrieves the protocol stack for a given slave harness ID.
  MHPSPtr GetProtocolStack(std::string harness_id);
  /// Retrieves the protocol stack for a given client SUT ID.
  MHPSPtr GetProtocolStack(size_t sut_id);
  /// Retrieves the slave harness ID for a given client SUT ID.
  std::string GetSlaveHarnessID(size_t sut_id);
  /// Retrieves all client SUT IDs for a given slave harness ID.
  std::vector<size_t>* GetClientSUTIDs(std::string harness_id);
  /// Retrieves all slave harness IDs in a vector.
  std::vector<std::string>* GetAllSlaveHarnessIDs();

 private:
  /// Called when a client connects to this server.
  /// TODO(njhwang) remove conn_id from NetworkServer API; no longer needed
  void ConnectionMade(size_t conn_id, NetworkConnection* conn);

  EventLoop* event_loop_;
  std::unique_ptr<NetworkServer> network_server_;
  /// Protects the data structures below.
  boost::mutex data_tex_;
  std::vector<MHPSPtr> protocol_stacks_;
  std::vector<std::string> harness_ids_;
  std::map<size_t, MHPSPtr> sut_ps_map_;
  std::map<std::string, MHPSPtr> harness_ps_map_;
  std::map<size_t, std::string> sut_harness_map_; 
  std::map<std::string, std::vector<size_t>*> harness_sut_map_;
};

#endif
