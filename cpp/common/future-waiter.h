//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class for waiting for a group of futures to all
//                     complete. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Sep 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_FUTURE_WAITER_H_
#define CPP_COMMON_FUTURE_WAITER_H_

#include <functional>
#include <thread>

#include "future.h"
#include "types.h"

/// We often have a set of futures returned from various function calls and we
/// just want to wait for them all to be complete. This class is designed to make
/// that easy. Call Add() for each future you want to wait on. When all the
/// commands have been called you can call Wait(). That will block until all the
/// futures have fired.
template<class T>
class FutureWaiter {
 public:
  FutureWaiter() : num_outstanding_(0) {}

  void Add(Future<T> f) {
    {
      MutexGuard l(data_tex_);
      ++num_outstanding_;
    }
    f.AddCallback(
        std::bind(&FutureWaiter<T>::FutureFired, this, std::placeholders::_1));
  }

  void Wait() {
    UniqueMutexGuard g(data_tex_);
    while (num_outstanding_ > 0) {
      none_pending_cond_.wait(g);
    }
  }
    
 private:
  void FutureFired(T data) {
    MutexGuard l(data_tex_);
    CHECK(num_outstanding_ > 0);
    --num_outstanding_;
    if (num_outstanding_ == 0) {
      none_pending_cond_.notify_all();
    }
  }

  std::mutex data_tex_;
  std::condition_variable none_pending_cond_;
  /// Number of futures that were added but have not yet fired.
  int num_outstanding_;
};


#endif
