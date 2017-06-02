//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of network client methods. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 Sep 2012   omd            Original Version
//*****************************************************************

#include "network-client.h"
#include "event-loop.h"

#include <arpa/inet.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <event2/event.h>

// In event_new we get to pass an arbitrary pointer that will be passed to the
// ConnectionComplete callback. This is the data we'll pass via that pointer.
// This is essentially just a container for pointers to mutable data that the 
// callback needs to manipulate from a static context. 
struct WriteableEventData {
  // We need to pass the event object itself to the callback so it can be freed.
  // This is the event object.
  event* event_struct;
  // The EventLoop object handling this connection.
  EventLoop* event_loop;
  // This points to the future returned to the caller of WaitForConnection or
  // ConnectToServer. We need to fire this future once the connection is
  // complete.
  Future<ConnectionStatus> event_future;
};

// Called by libevent when the socket becomes writeable.
void NetworkClient::ConnectionComplete(
    int file_descriptor, short event_type, void* ptr) {
  CHECK(event_type == EV_WRITE);
  WriteableEventData* ed = reinterpret_cast<WriteableEventData*>(ptr);
  // Remove the event that was registered, as we do not want it to be
  // persistent.
  event_free(ed->event_struct);

  // Make the getsockopt system call to find out if the connection succeeded or
  // not. The getsockopt system call sets connection_status to one of the values
  // connect() would usually set in errno.
  //
  // TODO(odain): If connection_status != 0 add some meaningful error messages
  // to pass via the Future.
  int connection_status;
  socklen_t connection_status_len = sizeof(connection_status);
  getsockopt(file_descriptor, SOL_SOCKET, SO_ERROR, &connection_status,
             &connection_status_len);
  // getsockopt can modify the length argument to indicate the size of the
  // returned result but for SO_ERROR it should never do that.
  DCHECK(connection_status_len == sizeof(connection_status));

  ConnectionStatus cs;
  if (connection_status != 0) {
    cs.success = false;
  } else {
    cs.success = true;
    cs.connection.reset(new NetworkConnection(file_descriptor, ed->event_loop));
  }

  ed->event_future.Fire(cs);
  delete ed;
}

void NetworkClient::InitiateServerConnection(HostPort hp) {
  if (initiated_) {
    CHECK(!event_future_.HasFired()) <<
      "Error. Client connection being re-initiated before current " <<
       "connection has completed."; 
  }
  sockaddr_in addr = hp.ToSockAddr();
  int socket_fd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);
  int result = connect(socket_fd, reinterpret_cast<sockaddr*>(&addr),
                       sizeof(addr));
  // We expect a "error" return status as this is a non-blocking socket. As such
  // we expect to get back the error code. We'll know this socket is ready only
  // when the file descriptor becomes writeable.
  CHECK(result == -1);
  CHECK(errno == EINPROGRESS) << "Error. Connection failed with error: "
      << errno;

  WriteableEventData* ed = new WriteableEventData;

  // Note: this is not a persistent event. We want to know the 1st time the
  // descriptor becomes writeable as that indicates a network connection. After
  // that, it's up to the user of the NetworkConnection object to register
  // write/read callbacks.
  event* writeable_event =
      event_new(event_loop_->GetWriteLoop()->GetEventBase(), socket_fd, 
                EV_WRITE, &ConnectionComplete, ed);
  ed->event_struct = writeable_event;
  ed->event_loop = event_loop_;

  event_future_ = ed->event_future;

  // Event must be registered after ed has been initiated, lest the 
  // event triggers before ed is ready.
  event_loop_->GetWriteLoop()->RegisterEvent(writeable_event);
  initiated_ = true;
}

ConnectionStatus NetworkClient::WaitForConnection() {
  CHECK(initiated_) << "Error. Cannot wait for a connection " <<
    "that hasn't been initiated.";
  event_future_.Wait();
  return event_future_.Value();
}
