//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        Protocol stack for a test harness component that is acting
//                     as a slave for a master component. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version for TA1
// 15 Nov 2012   ni24039        Tailored for TA3
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_SLAVE_NETWORK_STACK_H_
#define CPP_TEST_HARNESS_TA3_SLAVE_NETWORK_STACK_H_

#include <memory>

#include "common/network-connection.h"
#include "common/line-raw-parser.h"

class NumberedCommandReceiver;
class NetworkConnection;
class ScriptManager;

class SlaveHarnessNetworkStack {
 public:
  SlaveHarnessNetworkStack(std::string harness_id, size_t num_suts,
                           std::shared_ptr<NetworkConnection> connection,
                           ScriptManager* script_manager);

  /// Enables this network stack to process incoming data over the network
  /// connection. Incoming data will not be processed before this is called.
  void Start();

  /// Gets called when a client SUT emits a DISCONNECTION message.
  void SUTDisconnected(size_t sut_id);

  /// Shuts down the network connection.
  void Shutdown();

  NumberedCommandReceiver* GetNumberedCommandReceiver() {
    return nc_receiver_;
  }

  std::string GetHarnessId() {
    return harness_id_;
  }

 private:
  std::string harness_id_;
  size_t num_suts_;
  std::shared_ptr<NetworkConnection> connection_;
  std::unique_ptr<LineRawParser> lr_parser_;
  NumberedCommandReceiver* nc_receiver_;
};

#endif
