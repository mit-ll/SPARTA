//*****************************************************************
// Copyright 2011 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Performance timing class.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Oct 2011   omd            Added this header
//*****************************************************************

#ifndef MYSQL_CLIENT_TIMER_H_
#define MYSQL_CLIENT_TIMER_H_

#include <time.h>

/// Getting accurate timing information is somewhat complex and system
/// dependent.  This factors out the specific time fetching mechanism so we
/// can easily replace it for different stystems, clocks, etc. if necerssary.
class Timer {
 public:
  Timer();
  virtual ~Timer() {}
  /// Call once to start the timer.
  void Start();
  /// Call as many times as desired. Returns the number of seconds that have
  /// elapsed since Start() was called.
  double Elapsed() const;
  /// Returns the number of seconds that have elapsed since some unspecified
  /// start time. This is a global timer so multiple processes may get a
  /// timestamp this way and these times may be meaningufully compared.
  static double RawElapsed();

 private:
  /// Convert a struct timespec object to a double representing a number of
  /// seconds. Note that clock_gettime returns the amount of time elapsed from
  /// some unspecified start point so this is not a meaningful value by itself.
  static double TimespecToDouble(timespec value);
  friend class TestableTimer;

  timespec start_;
};

#endif
