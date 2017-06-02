//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Definition and implementation of a future class 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 05 Jul 2012   omd            Original Version
//*****************************************************************


#ifndef COMMON_FUTURE_H_
#define COMMON_FUTURE_H_

#include <condition_variable>
#include <functional>
#include <memory>
#include <thread>
#include <list>

#include "check.h"

/// This define a Future class. A Future is used to make asynchronous code easier
/// to write and understand. Suppose the function ComputeAValue() take a while to
/// complete it's computation (e.g. it has to read it off a disk, make a network
/// call to retreive the value, or it does a complex calcuation in another
/// thread). The function can return a Future which will, in the *future*, hold
/// the result of the calculation. The caller can then ask to be notified when
/// the result is ready via a callback, they can Wait() until the computation is
/// complete, or they can call Value() which will Wait() for the computation to
/// be complete and then return the result.
///
/// For example:
///
/// Future<int> f = CompteAValue();
/// .. Do some other stuff ...
/// int result = f.Value();
///
/// For a more complex example, consider a TA1 throughput/loaded latency test.
/// To do this we'd fire off a bunch of queries. Since TA1 clients are allowed to
/// be asynchronous we'd tell them to execute the query and they tell us some
/// time later when the query is done. With the right API we can use future's to
/// both get notified as soon as the query completes so we can log the time for
/// latency testing and easily know when all the queries are complete so we know
/// when the test is complete. It might look like this:
///
/// for (int i = 0; i < kNumQueriesInTest; ++i) {
///   future = TellClientToRunQuery(test_query[i]);
///   future.AddCallback(&LogQueryResultTime);
///   pending_queries.push_back(future);
/// }
///  
/// ... Other stuff ...
/// for (j = pending_queries.begin(); j != pending_queries.end(); ++j) {
///   j->Wait();
/// }
/// ... Here we know that all the queries have finished and we can start another
/// test...
///
/// Also note that Future's are designed to be copied by value inexpensively.
/// This makes it easier to manage the memory associated with an object that will
/// be held and accessed from several different threads and objects.

template<class T>
class Future {
 public:
  Future();
  Future(const Future<T>& other);
  virtual ~Future() {}
  typedef std::function<void (T)> FutureCallback;
  /// Call cb with the value passed to fire as soon as possible after Fire() is
  /// called. If the Future has already fired when this is called cb will be
  /// called immediately.
  void AddCallback(FutureCallback cb);

  /// Fire the future. This causes any threads blocked on Wait() or Value() to
  /// release and any callbacks to be called.
  void Fire(T value);
  /// Block until some thread calls Fire()
  void Wait();
  /// Block until some thread calls Fire(). Then return the value passed to
  /// Fire().
  T Value();
  /// Return true if this future has fired. False otherwise. If this returns
  /// true a call to Wait() or Value() will not block.
  bool HasFired() const;
 private:
  /// To make copying inexpensive we put all the data in struct and then use a
  /// smart pointer to manage the memory.
  struct FutureData {
    FutureData() : fired(false) {}
    /// All the callbacks that need to be called after Fire()
    std::list<FutureCallback> callbacks;
    /// Become true when Fire() is called.
    bool fired;
    /// The value passed to Fire(). Meaningless until fire == true
    T value;
    /// Protects all the data in this struct.
    std::mutex data_tex;
    /// Condition variable to wake sleeping Wait() and Value() callers.
    std::condition_variable fired_cond;
  };
  std::shared_ptr<FutureData> data_;
};

////////////////////////////////////////////////////////////////////////////////
// Implementation
////////////////////////////////////////////////////////////////////////////////

template<class T>
Future<T>::Future() : data_(new FutureData) {
}

template<class T>
Future<T>::Future(const Future<T>& other) : data_(other.data_) {
}

template<class T>
void Future<T>::AddCallback(Future<T>::FutureCallback cb) {
  std::lock_guard<std::mutex> l(data_->data_tex);
  if (data_->fired) {
    // The future has already fired so call the callback immediately.
    cb(data_->value);
  } else {
    data_->callbacks.push_back(cb);
  }
}

template<class T>
void Future<T>::Fire(T value) {
  // It should be safe to set the value without holding the mutex. Only 1 thread
  // should ever fire and nobody should be reading the value until we've fired.
  data_->value = value;

  // Call all the callbacks. The mutex must be held here or we can't guarantee
  // what happens if another thread tries to add a new callback while Fire() is
  // running. This means that callbacks should never try to use the Future
  // itself. That should be safe as the callbacks are passed Value() and they
  // know HasFired() is true.
  {
    std::lock_guard<std::mutex> l(data_->data_tex);
    typename std::list<FutureCallback>::iterator cb_i;
    for (cb_i = data_->callbacks.begin();
         cb_i != data_->callbacks.end(); ++cb_i) {
      (*cb_i)(value);
    }
    // Once the callbacks are called we don't need them anymore.
    data_->callbacks.clear();

    data_->fired = true;
    data_->fired_cond.notify_all();
  }
}

template<class T>
void Future<T>::Wait() {
  std::unique_lock<std::mutex> lock(data_->data_tex);
  while (!data_->fired) {
    data_->fired_cond.wait(lock);
  }
}

template<class T>
bool Future<T>::HasFired() const {
  std::lock_guard<std::mutex> l(data_->data_tex);
  return data_->fired;
}

template<class T>
T Future<T>::Value() {
  Wait();
  return data_->value;
}

#endif
