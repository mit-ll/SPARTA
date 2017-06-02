//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class that creates a Unix FIFO and provides
//                     iostream access to it. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 04 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_FILE_PIPE_H_
#define CPP_COMMON_FILE_PIPE_H_

#include <memory>

#include "util.h"

/// In order to unit test things like LineRawInput we need to be able to send a
/// partial line or other partial input to LineRawInput and then send more data.
/// stringstream won't work as it returns EOF as soon as you read past the
/// end of the *current* string (e.g. you can't read what's there and then add
/// more). So the solution is to used pipes. But:
///
/// 1) There's no platform independent way to create pipes.
///
/// 2) There' no standard way, even on Unix, to wrap the file descriptors
/// returned by pipe() or mkfifo() with an istream or an ostream.
///
/// This class creates the necessary istream and ostream members and lets you
/// close either end of the pipe. It does it in a way that's specific to g++ and
/// Linux. However, since I've got this factored out into a separate class we
/// could write different versions for different platforms if necessary.
class FilePipe {
 public:
  FilePipe();
  virtual ~FilePipe() {}

  /// Get the output stream created by the constructor. Writing to this stream
  /// puts data into the pipe.
  std::ostream* GetWriteStream() {
    return out_stream_.get();
  }

  /// Get the input stream created by the constructor. Reading from this stream
  /// reads data from the pipe.
  std::istream* GetReadStream() {
    return in_stream_.get();
  }

  /// Close the output stream. ostream object's don't have a close method so this
  /// closes the underlying file handle.
  void CloseWriteStream();
  /// Close the input stream. istream object's don't have a close method so this
  /// closes the underlying file handle.
  void CloseReadStream();

 private:
  /// The pipe() call returns an array of file handles. The constants indicate
  /// which handle corresponds to which end of the pipe.
  static const int INPUT_STREAM_IDX = 0;
  static const int OUTPUT_STREAM_IDX = 1; 
  std::auto_ptr<FileHandleOStream> out_stream_;
  std::auto_ptr<FileHandleIStream> in_stream_;
};


#endif
