//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Various utilites. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 May 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_COMMON_UTIL_H_
#define CPP_COMMON_UTIL_H_

#include <ext/stdio_filebuf.h>
#include <iostream>
#include <memory>
#include <random>
#include <set>
#include <string>
#include <vector>

#include "check.h"

class GeneralLogger;

/// Standard C++ doesn't provide any way to create an iostream object from a file
/// handle. But many useful functions (e.g. exec and pipe) return file handles
/// and don't have C++ equivalents. This class and FileHandleIStream convert a
/// file handle into an iostream object. They do this using g++ extensions that
/// may not be available on other platforms.
class FileHandleOStream : public std::ostream {
 public:
  /// Construct a output stream for the file handle given by fd.
  FileHandleOStream(int fd);
  virtual ~FileHandleOStream() {}
  /// Close the output stream.
  void close();
 private:
  /// This is a g++ extension - it's a filebuf that's constructed from a file
  /// handle.
  __gnu_cxx::stdio_filebuf<char> buf_;
  int fd_;
};

/// VERY similar to FileHandleOStream. See that class for details.
///
/// Unfortunately, there's just enough difference that we can't easily create a
/// base class and then an istream and an ostream subclass. Differences include
/// the argument passed to the buf_ constructor and the fact that you need to
/// flush() an ostream before closing but you can't flush an istream.
class FileHandleIStream : public std::istream {
 public:
  FileHandleIStream(int fd);
  virtual ~FileHandleIStream() {}
  void close();
 private:
  __gnu_cxx::stdio_filebuf<char> buf_;
  int fd_;
};

/// Sets up a pipe. On return, read_fd is a file descriptor that the user can
/// read from and write_fd is one that the user can write to.
void SetupPipe(int* read_fd, int* write_fd);

/// Convenience function that sets up pipes for a notional process. Similar to
/// SetupPipe, on return, the user has read/write access to the notional process'
/// stdin and stdout. This can be used to facilitate process simulation in unit
/// tests.
void SetupPipes(int* proc_stdout_read_fd, int* proc_stdout_write_fd,
                int* proc_stdin_read_fd, int* proc_stdin_write_fd);

/// Spawning a child process in C++ is a huge pain - especially if you want to
/// connect iostreams to stdin and stdout of the process. This function takes
/// care of all the ugliness.
///
/// Arguments:
///   executable: Path to the binary to run
///   args: vector of arguments to pass to the executable
///   process_stdin: on return this will hold a pointer to an ostream. Writing to
///      stream sends data to the process' stdin.
///   process_stdout: on return this holds a pointer to an istream. Reading from
///      this stream retreives input from the process' stdout.
int SpawnAndConnectPipes(
    const std::string& executable, const std::vector<std::string>& args,
    std::auto_ptr<FileHandleOStream>* process_stdin,
    std::auto_ptr<FileHandleIStream>* process_stdout);

/// Overloaded version of the above but takes all the arguments as one long
/// string.
int SpawnAndConnectPipes(
    const std::string & executable, const std::string& args,
    std::auto_ptr<FileHandleOStream>* process_stdin,
    std::auto_ptr<FileHandleIStream>* process_stdout);

/// Another overloaded version which returns file handles instead of
/// FileHandle*Stream objects
int SpawnAndConnectPipes(
    const std::string& executable, const std::vector<std::string>& args,
    int* process_stdin_handle, int* process_stdout_handle);

/// And another version! This one returns file handles and takes the args as a
/// string instead of a vector<string>.
int SpawnAndConnectPipes(
    const std::string& executable, const std::string& args,
    int* process_stdin_handle, int* process_stdout_handle);

/// Many low-level C-library calls set errno if there is an error. This returns a
/// string that contains a text represenation of the error.
std::string ErrorMessageFromErrno(int errnum);

/// Logs the system time using the provided logger.
void LogRealTime(GeneralLogger* logger);

/// Gets a nicely formatted string containing the current local time
std::string GetCurrentTime();

/// Randomly selects n elements from the range defined by src_start (inclusive)
/// and src_end (exclusive), without replacement, and puts them in the range
/// starting with out_iter. rng is used to generate the random numbers. src_start
/// and src_end must be random access iterators, out_iter must be an output
/// iterator, and rng must conform to the STL (C++11) random library interface
/// for random number generators (e.g. mt1997 would work).
///
/// TODO(odain) This should proabably use some new C++ static-assert type
/// functionality to generate a nice compiler error if the iterators aren't
/// random access.
template<class InIterT, class RngT, class OutIterT>
void RandomSubset(int n, InIterT src_start, InIterT src_end,
                  RngT* rng, OutIterT out_iter);


////////////////////////////////////////////////////////////////////////////////
// Template function definitions
////////////////////////////////////////////////////////////////////////////////

/// This uses Floyd's algorithm to efficiently select n elements in O(n log(m))
/// time. For details see:
///
/// http://math.stackexchange.com/questions/178690/
/// whats-the-proof-of-correctness-for-robert-floyds-algorithm-
/// for-selecting-a-sin
template<class InIterT, class RngT, class OutIterT>
void RandomSubset(int n, InIterT src_start, InIterT src_end, RngT* rng,
                  OutIterT out_iter) {
  DCHECK(rng != nullptr);
  int range_size = src_end - src_start;
  DCHECK(range_size > 0);
  if (range_size == n) {
    /// special case for "subset" is the entire set.
    std::copy(src_start, src_end, out_iter);
  } else {
    DCHECK(n < range_size);
    std::set<int> selected;
    for (int i = range_size - n; i < range_size; ++i) {
      DCHECK(i > 0);
      std::uniform_int_distribution<> dist(0, i);
      int idx = dist(*rng);
      if (selected.find(idx) == selected.end()) {
        selected.insert(idx);
        *out_iter = *(src_start + idx);
      } else {
        DCHECK(selected.find(i) == selected.end());
        selected.insert(i);
        *out_iter = *(src_start + i);
      }
      ++out_iter;
    }
    DCHECK(selected.size() == static_cast<size_t>(n));
  }
}

#endif
