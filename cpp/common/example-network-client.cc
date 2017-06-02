//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Sample script that demonstrates how to write a network
//                     client with EventLoop.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 Sep 2012   omd            Original Version
//*****************************************************************

#include "event-loop.h"
#include "host-port.h"
#include "logging.h"
#include "network-client.h"
#include "statics.h"

#include <arpa/inet.h>
#include <boost/function.hpp>
#include <string>
#include <memory>

// Very simple executable that demonstrates how to write a very simple network
// client using libevent. This can also be used to debug the code using netcat.

// Gets called whenever new data arrives on the socket.
void DataReceived(Strand* s) {
  LOG(INFO) << "Received data: " << s->ToString();
  delete s;
}

int main(int argc, char** argv) {
  Initialize();
  EventLoop loop;
  NetworkClient client(&loop);
  HostPort hp = HostPort("127.0.0.1", 1234);
  loop.Start();
  client.InitiateServerConnection(hp);
  LOG(INFO) << "Waiting on connection....";
  ConnectionStatus cs = client.WaitForConnection();
  if (cs.success) {
    LOG(INFO) << "Connection Succeeded";
  } else {
    LOG(FATAL) << "Connection failed.";
  }

  std::shared_ptr<NetworkConnection> connection = cs.connection;

  connection->RegisterDataCallback(&DataReceived);

  connection->GetWriteQueue()->WriteWithBlock(
      new Knot(new std::string("I made a network client!\n")));
  loop.WaitForExit();
}
