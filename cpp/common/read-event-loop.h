//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        An EventLoop for read events. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Oct 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_READ_EVENT_LOOP_H_
#define CPP_COMMON_READ_EVENT_LOOP_H_

#include "event-loop-base.h"

#include <functional>

#include "buffer-pool.h"
#include "knot.h"

class Event;

/// As noted in event-loop.h we wish to have separete event loops for reading and
/// writing. This is the class that handles all reads.
class ReadEventLoop : public EventLoopBase {
 public:
  ReadEventLoop();
  virtual ~ReadEventLoop();
  /// Function signature for functions called when data is available. The called
  /// function must take ownership of the passed knot object and make sure it
  /// gets freed.
  typedef boost::function<void (Strand* data)> DataCallback;
  /// This causes cb to get called with any new data that arrives on
  /// file_descriptor. cb is responsible for freeing the knot* that gets passed
  /// to it.
  ///
  /// TODO(odain) Currently it is *not* safe to call this from multiple threads
  /// (though it is safe to call this after calling Start()). This matches our
  /// current use case so it's not clear if that should be "fixed" or not.
  void RegisterFileDataCallback(int file_descriptor, DataCallback cb);

  typedef std::function<void ()> EOFCallback;
  /// Calls cb when an EOF is seen on the given file. For processes this means
  /// the process has exited (or the pipe was otherwise broken) and for network
  /// sockets this means the network connection went away. Note that this is not
  /// thread safe and there is a race if this is called at the same time an EOF
  /// is encountered. This is so rare in our use cases that this is generally not
  /// a concern.
  void RegisterEOFCallback(int file_descriptor, EOFCallback cb);

  void RemoveEOFCallbacks(int file_descriptor);

  /// Same as the above, but also adds a log file. All data read from the file
  /// descriptor will be written to log_file. Note that this will be a
  /// potentially slow blocking call so this should only be done for debugging.
  void RegisterFileDataCallback(int file_descriptor, DataCallback cb,
                                std::ostream* log_file);

  /// This is the inverse of the above: It asks to not longer be called when
  /// data arrives on the file descriptor.
  void RemoveFileDataCallback(int file_descriptor);

 private:
  friend class Event;

  /// This is called by libevent so we have not flexability in it's argument
  /// list. For us, the void* will be boost::bind wrapped version of
  /// ReadDataAndCallback (bound to the relevant instance of ReadEventLoop). That
  /// function will do all the actual reading.
  static void CallReadCallback(int file_descriptor, short event_type,
                               void* callback);

  /// Called (via CallReadCallback) when a file_descriptor becomes readable. This
  /// will read all available data from file_descriptor and call cb, the user's
  /// callback function, with the result. If log_file != NULL all the read data
  /// will be sent to the log file as well.
  void ReadDataAndCallback(int file_descriptor, DataCallback cb,
                           std::ostream* log_file);

  /// We need to maintain all the pending events so we can later free them.
  /// Otherwise we'd have a memory leak. Note that WriteQueue's manage their own
  /// event's so they are not included in this map. This maps from file
  /// descriptor to the event for that file descriptor. Since we currently only
  /// manage read events here there should be no more than 1 event per file
  /// descriptor so this is fine.
  std::map<int, event*> events_;

  /// Map from file descriptor to a callback that should be called when end of
  /// file is observed for that file.
  std::map<int, std::list<EOFCallback> > eof_callbacks_;

  typedef boost::function<void (int)> ReadCallback;
  /// We need to maintain a copy of all the callback functions as we need to pass
  /// the *address* of a callback function to callbacks called by libevent
  /// (ReadDataAndCallback for example). So we store a copy of each callback
  /// function here. Note that making copies of boost::function objects is
  /// generally inexpensive.
  std::vector<ReadCallback*> callback_functions_;

  /// proctects callback_functions_ and events_.
  boost::mutex data_tex_;

  /// We read data from the file descriptor using readv. We use a buffer pool to
  /// manage a shared memory pool so that we can re-use buffers instead of using
  /// the free-store as that would be slower.
  BufferPool buffer_pool_;
};


#endif
