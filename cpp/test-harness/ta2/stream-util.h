//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Container for FileHandleXStreams that enable
//                     logging facilities. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Oct 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA2_UTIL_H_
#define CPP_TEST_HARNESS_TA2_UTIL_H_

#include <memory>
#include <string>
#include <iostream>

// A TestHarnessXStream is a container that own a std::iostream and a
// std::ofstream. It manages and logs the communication between the test-harness
// and the SUT. When the test-harness sends data to the SUT, it calls Write() on
// a TestHarnessOStream. When it receives data from the SUT, it calls Read() on
// a TestHarnessIStream.

class TestHarnessIStream {
 public:
  // The constructor takes as input the std::istream which is actually used
  // to read data from the SUT. Since the logging stream is not set, input from
  // the SUT will not be logged.
  TestHarnessIStream(std::unique_ptr<std::istream> stream);

  bool good() const;
  
  // Reads from stream_ until a newline character is found and stores it in 
  // line. The newline character is not included in line. If the debug stream is
  // set, this line also gets written to file along with linefeed.
  void Read(std::string* line);

  // Reads size number of bytes from stream_ and stores it in buf. If the debug
  // stream is set, buf also gets written to file.
  void Read(char* buf, unsigned int size);

  // Sets and takes ownership of the debug stream. Setting a logger may impact
  // performance. The boolean parameter buffered states whether or not the debug
  // stream is buffered.
  void SetDebugLogStream(
      std::unique_ptr<std::ostream> debug_stream, bool buffered);

 private:
  std::unique_ptr<std::istream> stream_;
  std::unique_ptr<std::ostream> debug_stream_;
  bool buffered_;
};

class TestHarnessOStream {
 public:
  // The constructor takes as input the std::ostream which is actually used
  // to write data to the SUT. Since the logging stream is not set, output from
  // the test-harness will not be logged
  TestHarnessOStream(std::unique_ptr<std::ostream> stream);

  // Writes the specified line to stream_ and inserts a linefeed. The string
  // itself should not contain a newline character. If the debug stream is set,
  // this line also gets written to file with a linefeed.
  void Write(const std::string& line);

  // Writes the specified character array to stream_. size indicates the number
  // of bytes to write. If the debug stream is set, buf also gets written to
  // file.
  void Write(const char* buf, unsigned int size);
  
  // Sets and takes ownership of the debug stream. Setting a logger may impact
  // performance. The boolean parameter buffered states whether or not the debug
  // stream is buffered.
  void SetDebugLogStream(
      std::unique_ptr<std::ostream> debug_stream, bool buffered);

 private:
  std::unique_ptr<std::ostream> stream_;
  std::unique_ptr<std::ostream> debug_stream_;
  bool buffered_;
};

#endif
