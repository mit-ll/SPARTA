//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of CircuitMessageHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012  yang            Original Version
//*****************************************************************

#include "circuit-message-handler.h"
#include "common/check.h"

using namespace std;

CircuitMessageHandler::CircuitMessageHandler(ostream* log) 
    : MessageHandler(log) {
}

void CircuitMessageHandler::Send(istream* circuit_stream) {
  CHECK(server_stdin() != nullptr && server_stdout() != nullptr)
      << "CircuitMessageHandler attempting to send over uninitialized streams";

  // Sending circuit description to server. Starting network transmission timer.
  // Test Harness --> SUT Server
  timer().Start();

  server_stdin()->Write("CIRCUIT");
  string line;
  while (circuit_stream->good()) {
    getline(*circuit_stream, line);
    if (line != "") {
      server_stdin()->Write(line);
    }
  }
  CHECK(circuit_stream->eof() == true);
  server_stdin()->Write("ENDCIRCUIT");
  double network_time = timer().Elapsed();

  // Starting timer for circuit ingestion.
  timer().Start();

  
  server_stdout()->Read(&line);
  CHECK(line == "CIRCUIT") << "Expected CIRCUIT header but got " << line;
  server_stdout()->Read(&line);

  CHECK(line == "CIRCUIT READY") << "Expected CIRCUIT READY but got " << line;
  server_stdout()->Read(&line);
  CHECK(line == "ENDCIRCUIT") << "Expected ENDCIRCUIT but got " << line;
  
  // Received circuit ready message from server. Stopping ingestion timer.
  // Test Harness <-- SUT Server
  double ingestion_time = timer().Elapsed();

  *log() << "INGESTION: " << ingestion_time << endl;
  *log() << "CIRCUITTRANSMIT: " << network_time << endl;

}

