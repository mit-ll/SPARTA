//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of NetworkServer 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Sep 2012   omd            Original Version
//*****************************************************************

#include "network-server.h"

#include <boost/bind.hpp>

#include "event-loop.h"

using std::map;

typedef boost::lock_guard<boost::mutex> MutexGuard;

NetworkServer::NetworkServer(HostPort host_port, EventLoop* event_loop,
                             ConnectionCallback cb)
    : event_loop_(event_loop), host_port_(host_port), conn_callback_(cb) {
  CHECK(event_loop != NULL);
  event_loop_->ListenForConnections(
      host_port, boost::bind(&NetworkServer::ConnectionMade, this, _1));
}

NetworkServer::~NetworkServer() {
  StopListening();
  map<HostPort, NetworkConnection*>::iterator i;
  {
    MutexGuard l(data_tex_);
    for (i = connection_map_.begin(); i != connection_map_.end(); ++i) {
      delete i->second;
    }
  }
}

void NetworkServer::StopListening() const {
  event_loop_->StopListening(host_port_);
}

void NetworkServer::ConnectionMade(
    std::auto_ptr<NetworkConnection> connection) {
  DCHECK(connection.get() != NULL);
  NetworkConnection* conn_ptr = connection.release();
  size_t conn_id;
  {
    MutexGuard l(data_tex_);
    conn_id = all_connections_.size();
    all_connections_.push_back(conn_ptr);
    // Call the user's callback with this connection. See notes in header file
    // for precautions when designing connection callbacks.
    //
    // The callback is called here to guarantee that the callback completes
    // before the NetworkServer reports to any user that the connection has
    // completed (e.g., via BlockUntilNumConnections). Note that this means
    // deadlock will occur if the callback attempts to call any NetworkServer
    // methods that obtain the mutex.
    if (!conn_callback_.empty()) {
      conn_callback_(conn_id, conn_ptr);
    }
    DCHECK(connection_map_.find(conn_ptr->GetHostPort()) ==
           connection_map_.end());
    connection_map_.insert(
        std::make_pair(conn_ptr->GetHostPort(), conn_ptr));
    DCHECK(all_connections_.size() == connection_map_.size());
  }
  num_connections_changed_cond_.notify_all();
}

size_t NetworkServer::NumConnections() const {
  MutexGuard l(data_tex_);
  return all_connections_.size();
}

void NetworkServer::BlockUntilNumConnections(size_t desired_connections) const {
  boost::unique_lock<boost::mutex> l(data_tex_);
  while (all_connections_.size() < desired_connections) {
    num_connections_changed_cond_.wait(l);
  }
}

NetworkConnection* NetworkServer::GetConnectionById(size_t id) const {
  MutexGuard l(data_tex_);
  if (id >= all_connections_.size()) {
   return NULL;
  } else {
   return all_connections_[id];
  } 
}
