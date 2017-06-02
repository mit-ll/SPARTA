//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Executes a key-exchange round with the SUT 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA2_KEY_MESSAGE_HANDLER_H_
#define CPP_TEST_HARNESS_TA2_KEY_MESSAGE_HANDLER_H_

#include "message-handler.h"

// The KeyMessageHandler implements the communication protocol for key exchange
// with the SUT client.
class KeyMessageHandler : public MessageHandler {
 public:

  // Constructor takes as input the result log stream.
  KeyMessageHandler(std::ostream* log);

  // This method implements the actual communication protocol. It takes as input
  // the security parameter and wait for the expected response. The method
  // transmits the public key from the client to the server.
  virtual void Send(std::istream* is);

};
#endif
