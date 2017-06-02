//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        KnotLogger implmentatoin 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 13 Sep 2012   omd            Original Version
//*****************************************************************

#include "general-logger.h"

#include <iostream>

#include "types.h"

using namespace std;

////////////////////////////////////////////////////////////////////////////////
// OstreamTimeLoggerBase
////////////////////////////////////////////////////////////////////////////////

OstreamTimeLoggerBase::OstreamTimeLoggerBase(std::ostream* output)
    : output_(output), owns_stream_(true), unbuffered_(false) {
  Setup();
}

OstreamTimeLoggerBase::OstreamTimeLoggerBase(std::ostream* output,
                                             bool owns_stream)
    : output_(output), owns_stream_(owns_stream), unbuffered_(false) {
  Setup();
}

OstreamTimeLoggerBase::OstreamTimeLoggerBase(std::ostream* output,
                                             bool owns_stream,
                                             bool unbuffered)
    : output_(output), owns_stream_(owns_stream), unbuffered_(unbuffered) {
  Setup();
}

void OstreamTimeLoggerBase::Setup() {
  // Show nanosecond precision
  const int kNumDigitsAfterTheDecimal = 9;
  output_->setf(ios::showpoint | ios::fixed);
  (*output_) << setprecision(kNumDigitsAfterTheDecimal);
}

OstreamTimeLoggerBase::~OstreamTimeLoggerBase() {
  if (!owns_stream_) {
    output_.release();
  }
}

// TODO(odain): The repetition here is a bummer. But template methods can't be
// virtual so I don't know of any better way to do this :(
void OstreamTimeLoggerBase::Log(const Knot& data) {
  // Get the time before we try to get the mutex in case that blocks.
  double elapsed = GetTime();
  MutexGuard l(output_tex_);
  LogHeader(elapsed);
  (*output_) << data << "\n";
  if (unbuffered_) {
    UnguardedFlush();
  }
}

void OstreamTimeLoggerBase::Log(const char* data) {
  // Get the time before we try to get the mutex in case that blocks.
  double elapsed = GetTime();
  MutexGuard l(output_tex_);
  LogHeader(elapsed);
  (*output_) << data << "\n";
  if (unbuffered_) {
    UnguardedFlush();
  }
}

void OstreamTimeLoggerBase::Log(const std::string& data) {
  // Get the time before we try to get the mutex in case that blocks.
  double elapsed = GetTime();
  MutexGuard l(output_tex_);
  LogHeader(elapsed);
  (*output_) << data << "\n";
  if (unbuffered_) {
    UnguardedFlush();
  }
}

void OstreamTimeLoggerBase::Flush() {
  MutexGuard l(output_tex_);
  output_->flush();
}

void OstreamTimeLoggerBase::UnguardedFlush() {
  output_->flush();
}

void OstreamTimeLoggerBase::LogHeader(double elapsed) {
  (*output_) << "[" << elapsed << "] ";
}

////////////////////////////////////////////////////////////////////////////////
// OstreamElapsedTimeLogger
////////////////////////////////////////////////////////////////////////////////

double OstreamElapsedTimeLogger::GetTime() {
  return timer_.Elapsed();
}

////////////////////////////////////////////////////////////////////////////////
// OstreamRawTimeLogger
////////////////////////////////////////////////////////////////////////////////

double OstreamRawTimeLogger::GetTime() {
  return Timer::RawElapsed();
}
