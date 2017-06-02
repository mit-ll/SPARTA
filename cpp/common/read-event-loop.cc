//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of ReadEventLoop 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Oct 2012   omd            Original Version
//*****************************************************************

#include "read-event-loop.h"

#include "bpbuffer-strand.h"
#include "check.h"

// We call read over and over filling up buffers of this size until no more
// buffers are available.
const int kReadBufferSize = (1 << 10); // 1k

ReadEventLoop::ReadEventLoop() : buffer_pool_(kReadBufferSize) {
}

ReadEventLoop::~ReadEventLoop() {
  boost::lock_guard<boost::mutex> l(data_tex_);

  // Free all the event objects.
  std::map<int, event*>::iterator i;
  for (i = events_.begin(); i != events_.end(); ++i) {
    if (i->second != NULL) {
      event_free(i->second);
    }
  }

  // And the callback objects.
  std::vector<ReadCallback*>::iterator rcb_it;
  for (rcb_it = callback_functions_.begin();
       rcb_it != callback_functions_.end(); ++rcb_it) {
    delete *rcb_it;
  }
}


void ReadEventLoop::RegisterFileDataCallback(
    int file_descriptor, DataCallback cb, std::ostream* log_file) {
  // We can't put a ReadCallback directly in the vector as we need an *address*
  // to pass to CallReadCallback and the addresses of items in vectors aren't
  // stable (the vector may need to resize), so we create a *pointer* to a
  // ReadCallback here.
  ReadCallback* read_callback = new ReadCallback(
      boost::bind(&ReadEventLoop::ReadDataAndCallback, this, _1, cb,
                  log_file));
  DCHECK(!cb.empty());

  boost::lock_guard<boost::mutex> l(data_tex_);
  callback_functions_.push_back(read_callback);
  struct event* e = event_new(
      GetEventBase(), file_descriptor, EV_READ | EV_PERSIST,
      &ReadEventLoop::CallReadCallback, read_callback);

  DCHECK(events_.find(file_descriptor) == events_.end())
      << "Can't register more than one callback for a single file descriptor";
  events_.insert(std::make_pair(file_descriptor, e));
  RegisterEvent(e);
}

void ReadEventLoop::RegisterFileDataCallback(
    int file_descriptor, DataCallback cb) {
  RegisterFileDataCallback(file_descriptor, cb, NULL);
}

void ReadEventLoop::CallReadCallback(int file_descriptor, short event_type,
                                 void* callback) {
  CHECK(event_type == EV_READ);
  // libevent requires the argument to be a void* but we know it's the address
  // of a boost::function so cast and call it.
  DCHECK(callback != NULL);
  ReadCallback* read_callback = reinterpret_cast<ReadCallback*>(callback);
  DCHECK(!read_callback->empty());
  (*read_callback)(file_descriptor);
}

void ReadEventLoop::ReadDataAndCallback(int file_descriptor, DataCallback cb,
                                    std::ostream* log_file) {
  // TODO(odain): if the amount of data available is > the kReadBufferSize this
  // loop will exeucte multiple times and thus run the expensive read() system
  // call multiple times. That's "bad". Using readv would allow us to reduce the
  // # of system calls though it would cause us to waste time allocating the
  // array of buffers for readv when a single buffer would hold all the data.
  // Profile and consider the options.
  while (true) {
    std::auto_ptr<BPBuffer> buffer(buffer_pool_.GetBuffer());
    int bytes_read = read(file_descriptor, buffer->buffer(), kReadBufferSize);
    if (bytes_read == -1) {
      // Note: errno is a thread-specific variable and hence thread-safe
      if (errno != EAGAIN && errno != EWOULDBLOCK) {
        const int kErrorBufferSize = 1024;
        char error_buffer[kErrorBufferSize];
        LOG(FATAL) << "Read for file descriptor: "
            << file_descriptor << " failed with unexpected error:\n"
            << strerror_r(errno, error_buffer, kErrorBufferSize);
      }
      break;
    } else {
      if (bytes_read == 0) {
        // This indicates EOF. We remove the event for the file and, if the user
        // has registered an EOF callback we call that.
        LOG(INFO) << "File descriptor " << file_descriptor << " at EOF.";
        RemoveFileDataCallback(file_descriptor);
        auto eof_cb_it = eof_callbacks_.find(file_descriptor);
        if (eof_cb_it != eof_callbacks_.end()) {
          // Call all the EOF callbacks.
          for (auto cb : eof_cb_it->second) {
            DCHECK(cb) << "Trying to call an unbound "
                << "std::function on EOF";
            cb();
          }
        }
        break;
      } else {
        DCHECK(bytes_read > 0);
        if (log_file != NULL) {
          log_file->write(buffer->buffer(), bytes_read);
        }
        Strand* data = new BPBufferStrand(buffer.release(), bytes_read);
        cb(data);
        if (bytes_read < kReadBufferSize) {
          break;
        }
      }
    }
  }
}

void ReadEventLoop::RegisterEOFCallback(int file_descriptor,
                                        EOFCallback cb) {
  eof_callbacks_[file_descriptor].push_back(cb);
}

void ReadEventLoop::RemoveEOFCallbacks(int file_descriptor) {
  LOG(DEBUG) << "Removing EOF callbacks for file descriptor "
             << file_descriptor;
  eof_callbacks_.erase(file_descriptor);
}

void ReadEventLoop::RemoveFileDataCallback(int file_descriptor) {
  boost::lock_guard<boost::mutex> l(data_tex_);
  std::map<int, event*>::iterator i = events_.find(file_descriptor);
  CHECK(i != events_.end());
  event_del(i->second);
  event_free(i->second);
  i->second = NULL;
}
