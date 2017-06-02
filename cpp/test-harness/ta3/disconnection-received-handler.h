//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            ni24039
// Description:        For handling DISCONNECTION messages.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Dec 2012   ni24039        Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_DISCONNECTION_RECEIVED_HANDLER_H_
#define CPP_TEST_HARNESS_TA3_DISCONNECTION_RECEIVED_HANDLER_H_

#include "common/protocol-extension-manager.h"

class SlaveHarnessNetworkStack;
class GeneralLogger;
class Knot;

/// An extension for handling disconnection received messages. Disconnection received
/// messages will consist of a just DISCONNECTION token. The event is logged as a
/// warning.
class DisconnectionReceivedHandler : public ProtocolExtension {
 public:
  DisconnectionReceivedHandler(size_t sut_id, 
                               SlaveHarnessNetworkStack* network_stack,
                               GeneralLogger* logger) : 
    sut_id_(sut_id), network_stack_(network_stack), logger_(logger) {}
  virtual ~DisconnectionReceivedHandler() {}

  virtual void OnProtocolStart(Knot start_line);
  virtual void LineReceived(Knot line);
  virtual void RawReceived(Knot data); 

 private:
  size_t sut_id_;
  SlaveHarnessNetworkStack* network_stack_;
  GeneralLogger* logger_;
};

#endif
