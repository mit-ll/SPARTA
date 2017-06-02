//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        An object that encapsulates a network connection. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_NETWORK_CONNECTION_H_
#define CPP_COMMON_NETWORK_CONNECTION_H_

#include "event-loop.h"

class Strand;

/// Represents a network connection managed by EventLoop. Note that initially
/// there is no callback registered to handle new data. Users must call
/// RegisterDataCallback in order to receive data from the socket.
///
/// Note that this is compatible with LineRawParser, ProtocolExtensionManager,
/// etc. so that the full suite of LineRawData protocols can easily be used to
/// communicate over both pipes and network connections.
class NetworkConnection {
 public:
  NetworkConnection(int file_descriptor, EventLoop* event_loop);
  virtual ~NetworkConnection() {}

  void RegisterDataCallback(EventLoop::DataCallback cb) {
    event_loop_->RegisterFileDataCallback(file_descriptor_, cb);
  }

  /// Close the connection
  void Shutdown() const {
    LOG(DEBUG) << "Removing EOF callback for connection";
    event_loop_->RemoveEOFCallbacks(file_descriptor_);
    shutdown(file_descriptor_, SHUT_WR);
  }

  WriteQueue* GetWriteQueue();

  HostPort GetHostPort() const;

  int GetFileDescriptor() const {
    return file_descriptor_;
  }

 private:
  /// Called when the socket hits EOF
  void SocketAtEOF() const;
  int file_descriptor_;
  EventLoop* event_loop_;
  WriteQueue* write_queue_;
};

#endif
