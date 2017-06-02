//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of InputMessageHandler 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Sep 2012  yang            Original Version
//*****************************************************************

#include "input-message-handler.h"
#include "common/check.h"
#include "common/string-algo.h"

using namespace std;

InputMessageHandler::InputMessageHandler(ostream* log)
    : MessageHandler(log) {
}

void InputMessageHandler::Send(std::istream* input_stream) {
  CHECK(client_stdin() != nullptr && client_stdout() != nullptr)
      << "InputMessageHandler has uninitialized client streams";
  CHECK(server_stdin() != nullptr && server_stdout() != nullptr)
      << "InputMessageHandler has uninitialized server streams";
  string line;
 
  client_stdin()->Write("PDATA");
  while (input_stream->good()) {
    getline(*input_stream, line);
    if (line != "") {
      client_stdin()->Write(line);
    }
  }
  CHECK(input_stream->eof() == true);
  client_stdin()->Write("ENDPDATA");

  // Sent unencrypted data to the SUT client. Starting timer for encryption.
  // SUT Client <-- Test Harness
  timer().Start();

  // We expect an EDATA message from the client.
  client_stdout()->Read(&line);
  CHECK(line == "EDATA") 
      << " Received unexpected input message header from client: " << line;
  server_stdin()->Write("EDATA");

  // Received first byte of encrypted input. Stopping timer.
  double encrypt_time = timer().Elapsed();
  // Starting timer for network transmission of encrypted input.
  // Test Harness --> SUT Server
  timer().Start();

  unsigned int data_size = 0;
  // This will either be a byte count or "ENDEDATA"
  client_stdout()->Read(&line);
  while (line != "ENDEDATA") {
    // Write out byte count to server followed by a line break
    server_stdin()->Write(line);
    unsigned int size = SafeAtoi(line);
    data_size += size;
    char encrypted_input[size];
    client_stdout()->Read(encrypted_input, size);
    // Write out data to server *WITHOUT* line break
    server_stdin()->Write(encrypted_input, size);
    // Consume the rest of line. This will either be another byte count or
    // "ENDEDATA"
    client_stdout()->Read(&line);
  }
  CHECK(line == "ENDEDATA") 
      << "Received unexpected input message footer from client: " << line;
  server_stdin()->Write("ENDEDATA");
  double network_time = timer().Elapsed();
  *log() << "ENCRYPT: " << encrypt_time << endl;
  *log() << "INPUTTRANSMIT: " << network_time << endl;
  *log() << "INPUTSIZE: " << data_size << endl;

  // Now the server has the entire encrypted input. Starting timer for
  // evaluation.
  timer().Start();

  // We expect an EDATA message from the server
  server_stdout()->Read(&line);
  CHECK(line == "EDATA") 
      << "Received unexpected input message header from server: " << line;
  client_stdin()->Write("EDATA");

  double eval_time = timer().Elapsed();
  // Receiving encrypted output. Starting transmission timer.
  // Test Harness <-- SUT Server
  timer().Start();
  
  data_size = 0;
  server_stdout()->Read(&line);
  while (line != "ENDEDATA") {
    client_stdin()->Write(line);
    unsigned int size = SafeAtoi(line);
    data_size += size;
    char encrypted_output[size];
    server_stdout()->Read(encrypted_output, size);
    client_stdin()->Write(encrypted_output, size);
    server_stdout()->Read(&line);
  }
  CHECK(line == "ENDEDATA") 
      << "Received unexpected input message footer from server: " << line;
  client_stdin()->Write("ENDEDATA");

  // Finished transmitting encrypted data to client.
  // SUT Client <-- Test Harness <-- SUT Server
  network_time = timer().Elapsed();

  *log() << "EVAL: " << eval_time << endl;
  *log() << "OUTPUTTRANSMIT: " << network_time << endl;
  *log() << "OUTPUTSIZE: " << data_size << endl;
  
  // Starting evaluation timer. 
  timer().Start();

  // We expect a PDATA message from the client.
  client_stdout()->Read(&line);
  CHECK(line == "PDATA") << "Unexpected input message header: " << line;
  double decrypt_time = timer().Elapsed();
  client_stdout()->Read(&line);
  *log() << "DECRYPTED RESULT: " << line << endl;
  client_stdout()->Read(&line);
  CHECK(line == "ENDPDATA") << "Unexpected input message footer " << line;
  *log() << "DECRYPT: " << decrypt_time << endl;
}

