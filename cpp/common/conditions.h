//*****************************************************************
// Copyright 2011 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Handy wrappers for condition variables
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Oct 2011   omd            Added this header
//*****************************************************************

#ifndef MYSQL_CLIENT_CONDITIONS_H_
#define MYSQL_CLIENT_CONDITIONS_H_

#include <boost/thread/thread.hpp>

/// In order to use boost::condition_variable for a simple boolean condition you
/// need a mutex, a condition_variable, and a boolean variable. This class wraps
/// up those items to create a single, very easy to use condition variable for
/// any single value. The type of the value is given by the template parameter
/// and it must support operator==.  This calls notify_all when the value changes
/// in any way. In many instances that's actually faster than calling notify only
/// when a specific condition has occured (and in the case of a Boolean variable
/// it's exactly the same) but in other situations it's worse. Thus there may
/// still be instances where it's faster to manually manage the mutex, value, and
/// condition variable.
template<class ValueT>
class SimpleCondition {
 public:
  SimpleCondition(ValueT init_value) : value_(init_value) {}
  void Wait(ValueT wait_for) {
    boost::unique_lock<boost::mutex> lock(tex_);
    while (value_ != wait_for) {
      cond_.wait(lock);
    }
  }

  void Set(ValueT new_value) {
    boost::lock_guard<boost::mutex> lock(tex_);
    value_ = new_value;
    cond_.notify_all();
  }

  /// See the comments on GetLock().
  void SetButDoNotLock(ValueT new_value) {
    value_ = new_value;
    cond_.notify_all();
  }

  /// See the comments on GetLock().
  ValueT GetButDoNotLock() const {
    return value_;
  }

  /// Manually grab the lock. This is generally used for an atomic get-and-set,
  /// for example, to increment an integer SimpleCondition. The user is
  /// responsible for calling ReleaseLock() when they are done! Do *not* call
  /// Set() or Wait() while the lock is held or you will deadlock! Instead, call
  /// SetButDoNotLock() or GetButDoNoLock().
  void GetLock() {
    tex_.lock();
  }

  void ReleaseLock() {
    tex_.unlock();
  }

 private:
  boost::mutex tex_;
  boost::condition_variable cond_;
  ValueT value_;
};

#endif
