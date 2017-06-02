//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        A class for executing an input round with the SUT  
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA2_INPUT_MESSAGE_HANDLER_H_
#define CPP_TEST_HARNESS_TA2_INPUT_MESSAGE_HANDLER_H_

#include "message-handler.h"

// InputMessageHandler implements the communication protocol with the SUT client
// and server for encryption, homomorphic evaluation, and decryption of inputs.
class InputMessageHandler : public MessageHandler {
 public:
 
  InputMessageHandler(std::ostream* log);
 
  // This method implements the actual communication protocol.
  //
  // The method will send the client a PDATA message containing the plain-text 
  // input and wait for an EDATA response containing the encrypted input. Once
  // received, it will forward the encrypted input to the server in an EDATA
  // message and wait for an encrypted result. Finally, it will forward the 
  // encrypted result to the client and wait for a decrypted result.
  //
  // If in any part of this communication, an unexpected message is encountered,
  // the function will abort. Otherwise, it will block until all three rounds
  // are completed.
  virtual void Send(std::istream* input_stream);
};

#endif
