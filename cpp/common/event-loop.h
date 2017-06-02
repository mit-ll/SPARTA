//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        A async-io/timer event loop.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 27 Jun 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_COMMON_EVENT_LOOP_H_
#define CPP_COMMON_EVENT_LOOP_H_

#include <vector>

#include "knot.h"
#include "read-event-loop.h"
#include "write-event-loop.h"

/// An event loop that allows the user to wait for data on one or more file
/// descriptors. The main use case is for the SPAR test harness. That harness may
/// have to efficiently receive data from multiple places. For example, the TA3
/// server test harness component must receive command results from the
/// performer's stdout, it must also receive TCP socket data from all 100 test
/// harness components controlling all 100 clients. Spawning 101 threads and
/// having them all do blocking I/O would be very inefficient. A much better
/// solution is to use a single thread that waits for new data to be available on
/// any of the the file descriptors (threads or sockets). When new data is
/// available, the callback associated with that file descriptor is called with
/// the new data.
///
/// This actually uses two threads. One for all read operations and one for all
/// writes. This reduces the deadlock issues that might result when a read
/// callback wants to write some data in response as the writes can continue to
/// make progress while the read thread is blocked.
///
/// Waiting efficiently on multiple file descriptors is very plotform dependent
/// and somewhat tricky. Windows has one way of doing it, select works on all
/// versions of Linux and BSD but isn't very efficient. Since kernel 2.6 epoll is
/// the recommended way to do it on Linux but that only works on newer kernels
/// and doesn't work with other flavors of *nix, etc. As a result I've decided to
/// use libevent which provides a wrapper around all these methods and uses
/// whatever is the most efficient for the current platform. libevent is pure C
/// and provides a rather ugly interface so this code wraps libevent presenting
/// an easy to use interface.
///
/// Similarly, reading efficiently from a pipe with available data is suprisingly
/// tricky (see bug #617) and the are additional concerns about efficently moving
/// the data from thread to thread and method to method without too many copies.
/// Putting this in a single class lets us experiment with different methods (to
/// some degree) without affecting other code.
///
/// To use this calss create an EventLoop instance, call Register*Callback for
/// the type of callback you wish to have handled (currently this only handles
/// data in files or file-like objects such as pipes but I'll soon add methods
/// for sockets). The EventLoop then wathes the file and calls the supplied
/// callback with any new data. For example, to print any data received on stdin
/// a program could do the following:
///
/// // No need for a class here but this shows how you can use boost::bind to
/// // call methods on an object
/// class Example {
///   void SetupWatching() {
///     EventLoop loop;
///     // stdin == file descriptor 0
///     loop.RegisteFileDataCallback(0, boost::bind(&Example::Print, this));
///     loop.Start();
///    }
///
///    void Print(Knot data) {
///      cout << "Received: << *data << endl;
///      delete data;
///    }
/// };
///
/// The WriteQueue class handles writing to a file handle. You get a write queue
/// by calling GetWriteQueue() on the EventLoop. Multiple calls to GetWriteQueue
/// for the same file handle will return the same object so that multiple threads
/// can write to the same file and have ordering guaranteed. To write to the
/// handle you call Write(). If possible, Write() will send the data to the file
/// (or pipe) immediately. If that's not possible the data will be queued, an
/// event will be registered with EventLoop, and the data will be written as soon
/// as possible. If the file isn't writable and the queue of items to be written
/// gets too large (currently a fixed kMaxPendingBytes) Write() will return false
/// indicating that the data wasn't written OR queued. The caller must then
/// decide if they want to re-send, abandon the write, etc.

////////////////////////////////////////////////////////////////////////////////
// EventLoop
////////////////////////////////////////////////////////////////////////////////

struct evconnlistener;
class HostPort;
class NetworkConnection;
class NetworkClient;
struct ConnectionStatus;

/// The EventLoop class. See the comments at the top of this file for details.
class EventLoop {
 public:
  EventLoop() {}
  virtual ~EventLoop();
  /// This causes cb to get called with any new data that arrives on
  /// file_descriptor. cb is responsible for freeing the knot* that gets passed
  /// to it.
  ///
  /// TODO(odain) Currently it is *not* safe to call this from multiple threads
  /// (though it is safe to call this after calling Start()). This matches our
  /// current use case so it's not clear if that should be "fixed" or not.
  typedef ReadEventLoop::DataCallback DataCallback;
  void RegisterFileDataCallback(int file_descriptor, DataCallback cb) {
    read_event_loop_.RegisterFileDataCallback(file_descriptor, cb);
  }

  /// Registers a function to be called when the file reaches EOF. If the file is
  /// a pipe to a process this generally indictes that the process has exited. If
  /// the file_descriptor is a network socket this means the network connection
  /// has been disconnected.
  typedef ReadEventLoop::EOFCallback EOFCallback;
  void RegisterEOFCallback(int file_descriptor, EOFCallback cb) {
    read_event_loop_.RegisterEOFCallback(file_descriptor, cb);
  }

  void RemoveEOFCallbacks(int file_descriptor) {
    read_event_loop_.RemoveEOFCallbacks(file_descriptor);
  }

  /// Same as the above, but also adds a log file. All data read from the file
  /// descriptor will be written to log_file. Note that this will be a
  /// potentially slow blocking call so this should only be done for debugging.
  void RegisterFileDataCallback(
      int file_descriptor, DataCallback cb, std::ostream* log_file) {
    read_event_loop_.RegisterFileDataCallback(file_descriptor, cb, log_file);
  }

  /// This is the inverse of the above: It asks to not longer be called when
  /// data arrives on the file descriptor.
  void RemoveFileDataCallback(int file_descriptor) {
    read_event_loop_.RemoveFileDataCallback(file_descriptor);
  }

  /// Returns a WriteQueue for the given file handles. In order to ensure that
  /// multiple writes from different threads don't get interleaved all writes
  /// should be made through this object. Multiple calls to this method with the
  /// same file descriptor will return the same WriteQueue. Caching the
  /// WriteQueue is recommended as this function requires us to look up the queue
  /// for a given file handle which can be expensive. The EventLoop maintains
  /// ownership of all WriteQueue's and will free them in it's destructor.
  WriteQueue* GetWriteQueue(int file_descriptor) {
    return write_event_loop_.GetWriteQueue(file_descriptor);
  }

  /// Start the event loops in seprate threads and return immediately.
  void Start();

  /// Tells the event loop to exit as soon as possible. Note that is is OK to
  /// call this more than once (though subsequent calls will have no effect).
  void ExitLoop();

  /// This blocks until the event loop is done. This should only be called after
  /// ExitLoop has been called.
  void WaitForExit();

  /// Convenience method that calls ExitLoop() and then WaitForExit().
  void ExitLoopAndWait() {
    ExitLoop();
    WaitForExit();
  }

  /// Function that takes the host/port and the socket file descriptor for the
  /// new connection.
  typedef boost::function<void (std::auto_ptr<NetworkConnection>) >
      ConnectionMadeCallback;

  void ListenForConnections(const HostPort& host_port,
                            ConnectionMadeCallback cb);
  /// Stop listening for connections of host_port.
  void StopListening(const HostPort& host_port);

 private:
  /// Some accessors for the network client stuff
  friend class NetworkClient;

  WriteEventLoop* GetWriteLoop() {
    return &write_event_loop_;
  }

  ReadEventLoop* GetReadLoop() {
    return &read_event_loop_;
  }

  /// See below.
  struct NetworkConnectionData {
    EventLoop* loop;
    ConnectionMadeCallback callback;
  };
  /// Callback when connections are made. This has to be static and have this
  /// signature in order to work properly with libevent. ptr will be set to a
  /// NetworkConnectionData instance (which this should then free). This will
  /// call NetworkConnectionMade on the loop object in that struct. This allows
  /// us to call a non-member function from libevent (as libevent can't call
  /// members) and have that jump back into a member function cleanly.
  static void StaticNetworkConnectionMade(
    evconnlistener *listener, evutil_socket_t sock, struct sockaddr *addr,
    int len, void *ptr);

  /// The above just calls this method.
  void NetworkConnectionMade(int socket_fd, ConnectionMadeCallback* cb);

  /// We need to maintain all the pending events so we can later free them.
  /// Otherwise we'd have a memory leak. We also need to be able to enable and
  /// disable on a HostPort basis so we keep a map from HostPort to the listener
  /// struct.
  std::map<HostPort, evconnlistener*> listener_struct_map_;

  /// And we maintain all the server info to be freed later.
  std::vector<NetworkConnectionData*> connection_data_;

  /// The read and write event loops that do all the heavy lifting.
  WriteEventLoop write_event_loop_;
  ReadEventLoop read_event_loop_;
};

#endif
