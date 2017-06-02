//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Tiny wrapper around ifstream, ofstream, and fstream that
//                     will CHECK fail if opening a file failed. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 10 Dec 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_SAFE_FILE_STREAM_H_
#define CPP_COMMON_SAFE_FILE_STREAM_H_

#include <fstream>
#include <string>

#include "logging.h"
#include "util.h"


/// This file includes 3 classes, SafeIFStream, SafeOFStream, and SafeFStream.
/// These should be used in place of std::ifstream, std::ofstream, and
/// std::fstream respectively. They override the constructor and open() methods
/// to CHECK for failure and print an error message if opening the file failed.
/// They are all inherited from ifstream, ofstream, and fstream and so can be
/// used in place of those classes everywhere.

/// Do NOT use this directly. Use one of the named subclasses below.
template<class T>
class SafeStreamBase : public T {
 public:
  SafeStreamBase() : T() {}
  SafeStreamBase(const char* filename, std::ios_base::openmode mode)
      : T(filename, mode) {
    CheckForFailure(filename);
  }

  SafeStreamBase(const std::string& filename, std::ios_base::openmode mode)
      : T(filename, mode) {
    CheckForFailure(filename);
  }

  virtual ~SafeStreamBase() {}

  void open(const char* filename, std::ios_base::openmode mode) {
    T::open(filename, mode);
    CheckForFailure(filename);
  }

  void open(const std::string& filename, std::ios_base::openmode mode) {
    T::open(filename, mode);
    CheckForFailure(filename);
  }

 private:
  void CheckForFailure(const std::string& filename) {
    LOG(DEBUG) << "Checking that file opened properly...";
    /// NOTE: Most current implementations use errno but it's not guaranteed. It
    /// appears that gnu C++ does *not* use errno and there is no easy way to get
    /// a nice error message expalining what went wrong :(
    if (T::fail()) {
      LOG(FATAL) << "Error opening file " << filename;
    }
    LOG(DEBUG) << "File opened successfully.";
  }
};

/// For the sake of compatability we want to have the right default value for the
/// open mode for all subclasses so we have non-trivial subclasses here :(
class SafeIFStream : public SafeStreamBase<std::ifstream> {
 public:
  SafeIFStream() : SafeStreamBase<std::ifstream>() {}
  SafeIFStream(
      const char* filename, std::ios_base::openmode mode = std::ios_base::in)
      : SafeStreamBase<std::ifstream>(filename, mode) {}
  SafeIFStream(
      const std::string& filename,
      std::ios_base::openmode mode = std::ios_base::in)
      : SafeStreamBase<std::ifstream>(filename, mode) {}

  virtual ~SafeIFStream() {}

  void open(const char* filename,
            std::ios_base::openmode mode = std::ios_base::in) {
    SafeStreamBase<std::ifstream>::open(filename, mode);
  }

  void open(const std::string& filename,
            std::ios_base::openmode mode = std::ios_base::in) {
    SafeStreamBase<std::ifstream>::open(filename, mode);
  }
};

class SafeOFStream : public SafeStreamBase<std::ofstream> {
 public:
  SafeOFStream() : SafeStreamBase<std::ofstream>() {}
  SafeOFStream(
      const char* filename, std::ios_base::openmode mode = std::ios_base::out)
      : SafeStreamBase<std::ofstream>(filename, mode) {}
  SafeOFStream(
      const std::string& filename,
      std::ios_base::openmode mode = std::ios_base::out)
      : SafeStreamBase<std::ofstream>(filename, mode) {}

  virtual ~SafeOFStream() {}

  void open(const char* filename,
            std::ios_base::openmode mode = std::ios_base::out) {
    SafeStreamBase<std::ofstream>::open(filename, mode);
  }

  void open(const std::string& filename,
            std::ios_base::openmode mode = std::ios_base::out) {
    SafeStreamBase<std::ofstream>::open(filename, mode);
  }
};

class SafeFStream : public SafeStreamBase<std::fstream> {
 public:
  SafeFStream() : SafeStreamBase<std::fstream>() {}
  SafeFStream(
      const char* filename,
      std::ios_base::openmode mode = std::ios_base::out | std::ios_base::in)
      : SafeStreamBase<std::fstream>(filename, mode) {}
  SafeFStream(
      const std::string& filename,
      std::ios_base::openmode mode = std::ios_base::out | std::ios_base::in)
      : SafeStreamBase<std::fstream>(filename, mode) {}

  virtual ~SafeFStream() {}

  void open(
      const char* filename,
      std::ios_base::openmode mode = std::ios_base::out | std::ios_base::in) {
    SafeStreamBase<std::fstream>::open(filename, mode);
  }

  void open(
      const std::string& filename,
      std::ios_base::openmode mode = std::ios_base::out | std::ios_base::in) {
    SafeStreamBase<std::fstream>::open(filename, mode);
  }
};

#endif
