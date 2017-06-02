//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of TestHarnessXStream 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Oct 2012  yang            Original Version
//*****************************************************************

#include "stream-util.h"
#include "common/check.h"

using namespace std;

TestHarnessIStream::TestHarnessIStream(unique_ptr<istream> stream)
    : stream_(move(stream)), debug_stream_(), buffered_(true) { 
}

void TestHarnessIStream::Read(string* line) {
  getline(*stream_, *line);
  if (debug_stream_.get() != nullptr) {
    if (!buffered_)
      *debug_stream_ << *line << endl;
    else
      *debug_stream_ << *line << '\n';
  }
}

bool TestHarnessIStream::good() const {
  return stream_->good();
}

void TestHarnessIStream::Read(char* buf, unsigned int size) {
  stream_->read(buf, size);
  if (debug_stream_.get() != nullptr) {
    debug_stream_->write(buf, size);
    if (!buffered_)
      debug_stream_->flush();
  }
}

void TestHarnessIStream::SetDebugLogStream(
    unique_ptr<ostream> debug_stream, bool buffered) {
  CHECK(debug_stream.get() != nullptr);
  debug_stream_ = move(debug_stream);
  buffered_ = buffered;
}

TestHarnessOStream::TestHarnessOStream(unique_ptr<ostream> stream)
    : stream_(move(stream)), debug_stream_(), buffered_(true) {
}

void TestHarnessOStream::Write(const string& line) {
  *stream_ << line << endl;
  if (debug_stream_.get() != nullptr) {
    if (!buffered_)
      *debug_stream_ << line << endl;
    else
      *debug_stream_ << line << '\n';
  }
}

void TestHarnessOStream::Write(const char* buf, unsigned int size) {
  stream_->write(buf, size);
  if (debug_stream_.get() != nullptr) {
    debug_stream_->write(buf, size);
    if (!buffered_)
      debug_stream_->flush();
  }
}

void TestHarnessOStream::SetDebugLogStream(
    unique_ptr<ostream> debug_stream, bool buffered) {
  CHECK(debug_stream.get() != nullptr);
  debug_stream_ = move(debug_stream);
  buffered_ = buffered;
}
