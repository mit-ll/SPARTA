//*****************************************************************
// Copyright 2011 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        implementation of Timer class.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Oct 2011   omd            Added this header
//*****************************************************************

#include "timer.h"

#include <iostream>

using namespace std;

const clockid_t CLOCK_TO_USE = CLOCK_MONOTONIC_RAW;

Timer::Timer() {
}

void Timer::Start() {
  clock_gettime(CLOCK_TO_USE, &start_);
}

double Timer::TimespecToDouble(timespec value) {
  const int NumNanoSecondsPerSecond = 1e9;
  double ret = value.tv_sec +
    static_cast<double>(value.tv_nsec) /
    static_cast<double>(NumNanoSecondsPerSecond);
  return ret;
}

double Timer::Elapsed() const {
  double end_sec = RawElapsed();
  double start_sec = TimespecToDouble(start_);
  return end_sec - start_sec;
}

double Timer::RawElapsed() {
  timespec tm;
  clock_gettime(CLOCK_TO_USE, &tm);
  return TimespecToDouble(tm);
}
