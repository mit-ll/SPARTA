//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Protocl stack for a test harness component that is acting
//                     as a slave for a master component. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA1_SLAVE_NETWORK_STACK_H_
#define CPP_TEST_HARNESS_TA1_SLAVE_NETWORK_STACK_H_

#include <memory>

#include "common/network-connection.h"
#include "common/line-raw-parser.h"

class ScriptManager;
class NumberedCommandReceiver;

/// Sets up the stack for the server test harness component that is listening to
/// the network for commands from the test harness component controlling the
/// client.
class SlaveNetworkStack {
 public:
  SlaveNetworkStack(std::shared_ptr<NetworkConnection> connection,
                    ScriptManager* script_manager);

  NumberedCommandReceiver* GetNumberedCommandReceiver() {
    return nc_receiver;
  }

 private:
  std::shared_ptr<NetworkConnection> connection_;
  std::auto_ptr<LineRawParser> lr_parser_;
  /// Freed by the ready handler which is freed by the parser.
  NumberedCommandReceiver* nc_receiver;
};


#endif
