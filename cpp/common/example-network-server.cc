//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Very simple example that shows how to write a network
//                     server with libevent.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 07 Sep 2012   omd            Original Version
//*****************************************************************

#include "event-loop.h"
#include "host-port.h"
#include "logging.h"
#include "network-connection.h"
#include "statics.h"

#include <arpa/inet.h>
#include <boost/function.hpp>

// Very simple executable that demonstrates how to write a very simple network
// server using libevent. This can also be used to debug the code using netcat.

// Gets called whenever new data arrives on the socket.
void DataReceived(Strand* s) {
  LOG(INFO) << "Received data: " << s->ToString();
  delete s;
}

// Gets called when a new client connects to the server.
void ConnectionMade(std::auto_ptr<NetworkConnection> connection) {
  LOG(INFO) << "Receved connection from: "
        << connection->GetHostPort().ToString();
  connection->RegisterDataCallback(&DataReceived);
}

int main(int argc, char** argv) {
  Initialize();
  EventLoop loop;
  HostPort hp = HostPort::AnyAddress(1234);
  loop.Start();
  loop.ListenForConnections(hp, &ConnectionMade);
  loop.WaitForExit();
}
