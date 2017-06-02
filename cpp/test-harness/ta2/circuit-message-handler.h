//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Sends a circuit description to the SUT server 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA2_CIRCUIT_MESSAGE_HANDLER_H_
#define CPP_TEST_HARNESS_TA2_CIRCUIT_MESSAGE_HANDLER_H_

#include "message-handler.h"

// CircuitMessageHandler implements the communication protocol for passing the
// circuit description and public key to the SUT server.
class CircuitMessageHandler : public MessageHandler {
 public:

  CircuitMessageHandler(std::ostream* log);

  // This method implements the actual communication protocol. It takes as input
  // an input stream which contains the circuit description. The circuit
  // description should follow the syntax outlined in the test plan. The method
  // will read in the circuit and send the message
  //
  // CIRCUIT
  // <circuit description>
  // ENDCIRCUIT
  // KEY
  // <public key>
  // ENDKEY
  //
  // and wait for a CIRCUIT READY message from the server.
  virtual void Send(std::istream* circuit_stream);
};

#endif
