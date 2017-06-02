//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Client that makes a TCP connection using EventLoop.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 Sep 2012   omd            Original Version
// 29 Oct 2012   njh            Changed to class to make memory management more
//                              durable and API a bit more abstracted and
//                              convenient
//*****************************************************************


#ifndef CPP_COMMON_NETWORK_CLIENT_H_
#define CPP_COMMON_NETWORK_CLIENT_H_

#include <memory>

#include "future.h"
#include "host-port.h"
#include "network-connection.h"

class EventLoop;

/// struct that holds the connection status.
struct ConnectionStatus {
  /// Was the connection successful?
  bool success;
  /// If success == true this holds a pointer to the NetworkConnection object.
  std::shared_ptr<NetworkConnection> connection;
};

class NetworkClient {
   public:
      NetworkClient(EventLoop* event_loop) : 
        event_loop_(event_loop), initiated_(false) {}
      /// Using event_loop_, connect to the server with the given HostPort. It is
      /// an error to call this a second time before the previous connection
      /// is complete (i.e., this should always be followed by a call to
      /// WaitForConnection()).
      void InitiateServerConnection(HostPort hp);
      /// Returns a ConnectionStatus once the connection is complete or fails.
      /// This can be used to retrieve the ConnectionStatus multiple times for
      /// the same connection event.
      ConnectionStatus WaitForConnection();
      /// Convenience function that both initiates and waits for the connection
      /// to complete or fail. See the above comments for calling this a second
      /// time before allowing the previous connection to complete.
      ConnectionStatus ConnectToServer(HostPort hp) {
         InitiateServerConnection(hp);
         return WaitForConnection();
      }

  private:
      /// Called by libevent when a connection is made.
      static void ConnectionComplete(
         int file_descriptor, short event_type, void* ptr);
      EventLoop* event_loop_;
      /// Indicates whether the NetworkClient has already been initiated via a
      /// call to InitiateServerConnection();
      bool initiated_;
      /// The Future passed to ConnectionComplete via a WriteableEventData struct
      /// upon connection. This maintains the ConnectionStatus information for as
      /// long as this NetworkClient exists (or until a new connection is
      /// initiated).
      Future<ConnectionStatus> event_future_;
};

#endif
