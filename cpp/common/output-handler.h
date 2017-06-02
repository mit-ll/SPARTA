//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class for handling output from multiple threads and
//                     ensuring that each output is done atomically. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 08 May 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_COMMON_OUTPUT_HANDLER_H_
#define CPP_COMMON_OUTPUT_HANDLER_H_

#include <boost/thread.hpp>
#include <iostream>
#include <map>
#include <memory>
#include <string>

class OutputHandler;

/// This is a implementation detail. Users of OutputHandler should ignore this
/// class!!
///
/// This class maintains a map from std::ostream* to output handlers for those
/// streams, constructing new OutHandler instances the 1st time one is requested
/// for a stream. The main reason for putting this in a separate class is that it
/// makes it easy to manage the lifetime of the OutputStream pointers. The
/// desctructor of this class free's all the OutputHandler objects and the
/// OutputHandler class has a single static member of type
/// OutputHandlerRegistry. Thus the C++ framework will ensure that the registry's
/// destructor is called at program exit freeing all the handlers.
class OutputHandlerRegistry {
 public:
  virtual ~OutputHandlerRegistry();
  OutputHandler* GetHandler(std::ostream* stream);

 private:
  std::map<std::ostream*, OutputHandler*> handler_map_;
  /// protects handler_map_;
  boost::mutex handler_map_tex_;
};

void InitializeHandlerRegistry();
class LineRawToOutputHandler;

/// Simple class for ensuring atomic access to an output stream. Calling Write()
/// blocks until the stream is available and then writes it to the stream.
///
/// In order to ensure atomic access there must be exactly 1 handler per stream
/// as the handler is the thing that maintains the mutex. Thus the constructor
/// for OutputHandler is private. The only way to get a handler is vai
/// GetHandler() which will return an existing handler for a stream if one has
/// already been constructed. If not, a new one is constructed and returned. This
/// is fairly safe unless the user opens the same file twice thus getting two
/// ostream* pointers to the same file. Don't do that!!!
class OutputHandler {
 public:
  /// Returns an OutputHandler for safe multi-threaded access to the stream. Note
  /// that this call involves a mutex lock and map lookup so it is probably a
  /// good idea to cache the returned handler and pass it to other methods rather
  /// than relying on this method to return the handler on demand.
  static OutputHandler* GetHandler(std::ostream* stream);
  /// Will block until the output stream is available and then write the output
  /// atomically to the stream.
  void Write(const std::string& output) {
    boost::lock_guard<boost::mutex> l(output_stream_tex_);
    output_stream_->write(output.c_str(), output.size());
    output_stream_->flush();
  }

 private:
  OutputHandler(std::ostream* output_stream) {
    output_stream_ = output_stream;
  }

  /// The following 4 methods are for directly manipulating the locks and the
  /// underlying stream. They are used by LineRawToOutputHandler but shouldn't be
  /// used directly by users as using them correctly is error-prone.
  void Lock() {
    output_stream_tex_.lock();
  }

  void Unlock() {
    output_stream_tex_.unlock();
  }

  /// Write to the stream without obtaining the lock first. This should only be
  /// called if Lock() has already been called.
  void WriteLocked(const std::string& output) {
    output_stream_->write(output.c_str(), output.size());
  }

  void WriteLocked(const char* data, unsigned int length) {
    output_stream_->write(data, length);
  }

  template<class T>
  OutputHandler& operator<<(const T& data) {
    *output_stream_ << data;
    return *this;
  }

  void Flush() {
    output_stream_->flush();
  }

  friend class OutputHandlerRegistry;
  friend class LineRawToOutputHandler;
  friend void InitializeHandlerRegistry();
  static std::auto_ptr<OutputHandlerRegistry> handler_registry_;

  std::ostream* output_stream_;
  boost::mutex output_stream_tex_;
};



#endif
