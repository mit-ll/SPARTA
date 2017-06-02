//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of NetworkConnection 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 Sep 2012   omd            Original Version
//*****************************************************************

#include "network-connection.h"

#include <sys/socket.h>

#include "logging.h"
#include "host-port.h"

NetworkConnection::NetworkConnection(int file_descriptor, EventLoop* event_loop)
    : file_descriptor_(file_descriptor), event_loop_(event_loop),
      write_queue_(NULL) {
  event_loop->RegisterEOFCallback(
      file_descriptor, std::bind(&NetworkConnection::SocketAtEOF, this));
}

WriteQueue* NetworkConnection::GetWriteQueue() {
  if (write_queue_ == NULL) {
    write_queue_ = event_loop_->GetWriteQueue(file_descriptor_);
  }
  return write_queue_;
}

HostPort NetworkConnection::GetHostPort() const {
  sockaddr_in addr;
  socklen_t addr_len = sizeof(addr);
  getpeername(
      file_descriptor_, reinterpret_cast<sockaddr*>(&addr), &addr_len);
  return HostPort(addr);
}

void NetworkConnection::SocketAtEOF() const {
  LOG(INFO) << "Received EOF on network connection. Closing socket.";
  close(file_descriptor_);
}
