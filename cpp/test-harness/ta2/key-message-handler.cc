//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of KeyMessageHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012  yang            Original Version
//*****************************************************************

#include "key-message-handler.h"
#include "common/check.h"

using namespace std;

KeyMessageHandler::KeyMessageHandler(ostream* log) : MessageHandler(log) {
}

void KeyMessageHandler::Send(istream* is) {
  CHECK(client_stdin() != nullptr && client_stdout() != nullptr)
      << "KeyMessageHandler has uninitialized client streams.";
  CHECK(server_stdin() != nullptr && server_stdout() != nullptr)
      << "KeyMessageHandler has uninitialized server streams.";
  client_stdin()->Write("KEY");
  string line;
  while (is->good()) {
    getline(*is, line);
    if (line != "") {
      client_stdin()->Write(line);
    }
  }
  CHECK(is->eof() == true);
  client_stdin()->Write("ENDKEY");

  // Finished transmitting security parameters. Starting timer to measure key
  // generation.
  // SUT Client <-- Test Harness
  timer().Start();
  
  client_stdout()->Read(&line);
  CHECK(line == "KEY") << "Unexpected key message header: " << line;

  // Received first bytes of public key. Stopping timer.
  // SUT Client --> Test Harness
  double keygen_time = timer().Elapsed();

  // Starting timer to measure key network transmission time.
  // SUT Client --> Test Harness --> SUT Server
  timer().Start();

  unsigned int data_size = 0;
  server_stdin()->Write("KEY");
  while(line != "ENDKEY") {;
    client_stdout()->Read(&line);
    data_size += line.length();
    server_stdin()->Write(line);
  }
  CHECK(line == "ENDKEY") << "Unexpected key message footer: " << line;
  double network_time = timer().Elapsed();
  *log() << "KEYGEN: " << keygen_time << endl;
  *log() << "KEYTRANSMIT: " << network_time << endl;
  *log() << "KEYSIZE: " << data_size << endl;
}

