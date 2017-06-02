//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of EventLoop
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 27 Jun 2012   omd            Original Version
//*****************************************************************

#include "event-loop.h"

#include <boost/bind.hpp>
#include <event2/listener.h>
#include <fcntl.h>
#include <sys/uio.h>

#include "check.h"
#include "host-port.h"
#include "network-connection.h"
#include "statics.h"

using std::string;
using std::map;
using std::make_pair;
using std::vector;

EventLoop::~EventLoop() {
  read_event_loop_.ExitLoopAndWait();
  write_event_loop_.ExitLoopAndWait();

  // Free the network connection data.
  for (auto listen_it : listener_struct_map_) {
    evconnlistener_free(listen_it.second);
  }

  vector<NetworkConnectionData*>::iterator cd_it;
  for (cd_it = connection_data_.begin();
       cd_it != connection_data_.end(); ++cd_it) {
    delete *cd_it;
  }
}

void EventLoop::Start() {
  read_event_loop_.Start();
  write_event_loop_.Start();
}

void EventLoop::ListenForConnections(const HostPort& host_port,
                                     ConnectionMadeCallback cb) {
  struct sockaddr_in server_addr = host_port.ToSockAddr();

  // The number of outstanding connections that we haven't yet handled that
  // the OS will permit. This is probably greater than the max allowed by the
  // OS, but that's fine. It will just truncate the value to the max allowed.
  const int kMaxConnectionBacklog = 256;
  NetworkConnectionData* data = new NetworkConnectionData;
  data->loop = this;
  data->callback = cb;
  connection_data_.push_back(data);

  // Note that there is a flag to make the returned object thread safe. Since we
  // don't use it from multiple threads I don't think this is necessary. If it
  // is, it's probably better to pass the flag than it is to use a mutex.
  struct evconnlistener* conn_listener =
      evconnlistener_new_bind(
          read_event_loop_.GetEventBase(),
          &EventLoop::StaticNetworkConnectionMade,
          data, LEV_OPT_CLOSE_ON_FREE | LEV_OPT_REUSEABLE,
          kMaxConnectionBacklog, reinterpret_cast<sockaddr*>(&server_addr),
          sizeof(server_addr));
  // TODO(odain): Set an error callback via evconnlistener_set_error_cb

  listener_struct_map_.insert(make_pair(host_port, conn_listener));
}

void EventLoop::StopListening(const HostPort& host_port) {
  auto it = listener_struct_map_.find(host_port);
  CHECK(it != listener_struct_map_.end());
  struct evconnlistener* conn_listener = it->second;
  evconnlistener_disable(conn_listener);
}

void EventLoop::StaticNetworkConnectionMade(
    evconnlistener *listener, evutil_socket_t sock, struct sockaddr *addr,
    int len, void *ptr) {
  NetworkConnectionData* data = reinterpret_cast<NetworkConnectionData*>(ptr);
  data->loop->NetworkConnectionMade(sock, &data->callback);
}

void EventLoop::NetworkConnectionMade(int socket_fd,
                                      ConnectionMadeCallback* cb) {
  DCHECK(cb != NULL);
  std::auto_ptr<NetworkConnection> connection(
      new NetworkConnection(socket_fd, this));

  if (!cb->empty()) {
    (*cb)(connection);
  }
}

void EventLoop::ExitLoop() {
  read_event_loop_.ExitLoop();
  write_event_loop_.ExitLoop();
}

void EventLoop::WaitForExit() {
  read_event_loop_.WaitForExit();
  write_event_loop_.WaitForExit();
}
