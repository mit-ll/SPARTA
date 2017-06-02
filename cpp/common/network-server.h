//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class that listens on a tcp port and keeps track of the
//                     clients that are connected to it.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_NETWORK_SERVER_H_
#define CPP_COMMON_NETWORK_SERVER_H_

#include <boost/function.hpp>
#include <boost/thread.hpp>
#include <memory>

#include "host-port.h"
#include "network-connection.h"

class EventLoop;

/// The EventLoop class has a ListenForConnections class that allows you to set
/// up a server. However, it doesn't make it easy to maintain all the existing
/// connections to a server, find the connection to a given server, etc. This
/// class does that work.
class NetworkServer {
 public:
  /// Signature for the callback that gets called when a new connection is made.
  /// The NetworkServer owns the connection object that is passed. The size_t
  /// argument indicates what the assigned connection ID is for the passed in
  /// connection object.
  typedef boost::function<void (size_t, NetworkConnection*)> ConnectionCallback;
  /// Listen on HostPort using event_loop to manage the connections.
  /// connection is made call ConnectionCallback. If a callback is not desired
  /// you can pass ConnectionCallback() (the equivalent of a NULL function
  /// pointer).
  ///
  /// Note that the connection is NOT considered complete until the callback
  /// completes. Also note that the callback should NOT call any public
  /// NetworkServer methods, as this will result in deadlock.  
  NetworkServer(HostPort host_port, EventLoop* event_loop,
                ConnectionCallback cb);
  virtual ~NetworkServer();

  /// Stop listening for connections.
  void StopListening() const;

  /// Return the number of clients currently connected.
  size_t NumConnections() const;

  /// Blocks until NumConnections() >= desired_connections
  void BlockUntilNumConnections(size_t desired_connections) const;

  /// Get a connection by number. Connections are numbered starting from 0 in the
  /// order in which the clients connected. The returned pointer is owned by this
  /// object.
  /// 
  /// Note that disconnections are not currently tracked, as the active
  /// NetworkConnections are owned by this object and there currently is not a
  /// callback to this object when a NetworkConnection disappears. Connection IDs
  /// are therefore stable for the lifetime of this object.
  NetworkConnection* GetConnectionById(size_t id) const;

 private:
  /// Called by EventLoop when there's a new network connection
  void ConnectionMade(std::auto_ptr<NetworkConnection> connection);

  EventLoop* event_loop_;
  HostPort host_port_;
  ConnectionCallback conn_callback_;
  std::map<HostPort, NetworkConnection*> connection_map_;
  /// Contains a copy of the NetworkConnections from connection_map_. Allows us
  /// to quickly return a copy of all connections to the user.
  std::vector<NetworkConnection*> all_connections_;
  mutable boost::mutex data_tex_;
  /// This condition variable indicates that the number of connections to this
  /// server has changed.
  mutable boost::condition_variable num_connections_changed_cond_;
};


#endif
