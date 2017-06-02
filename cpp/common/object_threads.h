//*****************************************************************
// Copyright 2011 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Easy management/spawning of stateful threads.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Oct 2011   omd            Added this header
//*****************************************************************

#ifndef MYSQL_CLIENT_OBJECT_THREADS_H_
#define MYSQL_CLIENT_OBJECT_THREADS_H_

#include <boost/function.hpp>
#include <boost/thread/thread.hpp>
#include <climits>
#include <iostream>
#include <list>
#include <memory>
#include <vector>

#include "conditions.h"

using std::list;
using std::cout;
using std::endl;
using std::vector;

/// MySQL does not support an asynchronous interface. Thus we need one thread for
/// each pending request. Similarly, we need one MySQL connection per pending
/// operation. Creating a connection is expensive so we'd like to re-use
/// connections whenever possible. Similarly, creating threads is expensive so
/// we'd like to re-use those as well. Its difficult to know in advance what the
/// right number of threads will be so we create new ones as needed and re-use
/// existing ones whenever possible. In order to make this more general and to
/// make unit testing easier this is all abstracted so that it works for any
/// stateful class. Each thread is associated with a single object of that class.
/// The object's state in the case of MySQL would be the connection but other
/// usage patterns are allowed.
///
/// Specifically, an instance of ObjectThreads<T> is used as follows:
///
/// 1) An instance, ot, of ObjectThreads<T> is constructed. The constructor takes
///    a callback function that creates objects of type T.
/// 2) When the user has work that they'd like a T to perform in a thread they
///    call ot.AddWork(cb) where cb is a callback function that takes a T* as an
///    argument. This combined with boost::function and boost::bind allows for a
///    great deal of flexability as you can simply pass a pointer to a member
///    function of a T and it will work, you can pass a pointer to any function
///    or functor that takes a T* as an argument and that will work, and you can
///    use boost::bind to pre-bind some arguments of methods or members. See
///    object_threas_test.c for some examples. 
/// 3) When ot.AddWork is called ot checks for available threads. If no threads
///    are available a new T is constructed (via the function passed to the
///    constructor), a new thread is spawned, and cb(T) is executed on that
///    thread. If a thread is available it's T is re-used to execute cb().

template<class T> class SingleObjectThread;
typedef boost::lock_guard<boost::mutex> LockGuard;

template<class T>
class ObjectThreads {
 public:
  ObjectThreads(boost::function<T* ()> t_factory)
      : t_factory_(t_factory),
        max_threads_(INT_MAX) {}
  virtual ~ObjectThreads();
  void Run();
  void AddWork(boost::function<void (T*)> work);
  /// Spawn num_threads new theads that will wait for work (e.g. they don't have
  /// anything to do yet).
  void Spawn(int num_threads);
  /// Set a limit on the maximum number of threads.
  void set_max_threads(unsigned int num) { max_threads_ = num; }
  int NumThreads() const;
  int NumRunningThreads() const;
  int NumInactiveThreads() const;
 protected:
  friend class SingleObjectThread<T>;
  typedef typename list<SingleObjectThread<T>*>::iterator
      RunningThreadPointer;
  /// This is called by SingleObjectThread when it completes a work item.
  void MarkInactive(RunningThreadPointer p);
  /// Protects access to running_sothreads_ and inactive_sothreads_.
  mutable boost::mutex threads_mutex_;
  boost::condition_variable all_threads_inactive_;
  boost::condition_variable inactive_threads_available_;
  list<SingleObjectThread<T>*> running_sothreads_;
  list<SingleObjectThread<T>*> inactive_sothreads_;
  /// All the threads managed by this object. Note that this is only accessed
  /// from the main thread and so it is not protected by a mutex.
  vector<boost::thread*> threads_;
  boost::function<T* ()> t_factory_;
  /// Don't spawn more than this many threads.
  unsigned int max_threads_;
};

/// There is one instance of this class per thread managed by ObjectThreads. Each
/// ObjectThreads thread is executing SingleObjectThread::Run which is just a
/// loop that waits for new work items to appear.
///
/// The thread on which Run() is executing is detatched. When the Run() method
/// completes (after a call to Exit()) this class will delete itself. It is thus
/// not safe to touch an object of this class in any way after calling Exit().
template<class T>
class SingleObjectThread {
 public:
  SingleObjectThread(ObjectThreads<T>* parent, T* worker_object)
      : parent_(parent), worker_object_(worker_object),
        work_available_(false), exit_(false) {}
  /// This method runs a while(true) loop executing any work added via AddWork()
  /// until Exit() is called.
  void Run();
  void AddWork(boost::function<void (T*)> new_work,
               typename ObjectThreads<T>::RunningThreadPointer
                 thread_pointer);
  /// Make the Run() method exit. Exit() can only be called on an inactive thread
  /// (e.g. a thread in ObjectThreads::inactive_sothreads_) and you must be sure
  /// that no other calls to AddWork will be made concurrently. Since this is
  /// called only in the ObjectThreads destructor this should all be safe.
  void Exit() {
    exit_ = true;
    /// Work isn't really available but we need to wake the thread so it can
    /// complete.
    work_available_.Set(true);
  }

 private:
  ObjectThreads<T>* parent_;
  std::auto_ptr<T> worker_object_;
  /// Each time a new work item is added the thread associated with Run() gets
  /// moved to the running_sothreads_ queue of the ObjectThreads instance that
  /// added the work. We hold a pointer to that place in running_sothreads_ so
  /// that we can pass it to ObjectThreads::MarkInactive when the piece of work
  /// is completed.
  typename ObjectThreads<T>::RunningThreadPointer thread_pointer_;
  /// Condition variable that indicates when work is available.
  SimpleCondition<bool> work_available_;
  /// The function that's currently executing.
  boost::function<void (T*)> cur_work_;
  /// A boolean that indicates if the Run method should exit and a mutex to
  /// protect it. Note that the mutex is not necessary as Exit() call only be
  /// called on an inactive thread.
  bool exit_;
};

// Implementation of SingleObjectThread
template<class T>
void SingleObjectThread<T>::Run() {
  while (true) {
    work_available_.Wait(true);
    if (exit_) {
      break;
    }
    assert(cur_work_);
    // Call the cur_work_ callback passing the worker object as an argument.
    cur_work_(worker_object_.get());
    cur_work_ = NULL;
    // Now we've completed the work.
    work_available_.Set(false);
    parent_->MarkInactive(thread_pointer_);
  }
  // Delete self!
  delete this;
}

template<class T>
void SingleObjectThread<T>::AddWork(
    boost::function<void (T*)> new_work,
    typename ObjectThreads<T>::RunningThreadPointer thread_pointer) {
  cur_work_ = new_work;
  thread_pointer_ = thread_pointer;
  work_available_.Set(true);
}

// Implementation of ObjectThreads

template<class T>
ObjectThreads<T>::~ObjectThreads() {
  // We need to wait for all the current work to be completed.
  {
    boost::unique_lock<boost::mutex> thread_lock(threads_mutex_);
    while (running_sothreads_.size() > 0) {
      all_threads_inactive_.wait(thread_lock);
    }

    typename list<SingleObjectThread<T>*>:: iterator i;
    for (i = inactive_sothreads_.begin(); i != inactive_sothreads_.end(); ++i) {
      (*i)->Exit();
    }
  }
  // end of scope of thread_lock so threads_mutex_ no longer held here.

  // Now wait for all threads to actually stop. We need to do this or we'll have
  // problems when the completed threads call MarkInactive or otherwise try to
  // interact with this object.
  vector<boost::thread*>::iterator ti;
  for (ti = threads_.begin(); ti != threads_.end(); ++ti) {
    assert(running_sothreads_.size() == 0);
    (*ti)->join();
    delete *ti;
  }
}

template<class T>
void ObjectThreads<T>::Spawn(int num_threads) {
  assert(t_factory_);
  assert(num_threads >= 0);
  LockGuard l(threads_mutex_);
  for (int i = 0; i < num_threads; ++i) {
    T* worker_object = t_factory_();
    SingleObjectThread<T>* cur_thread =
        new SingleObjectThread<T>(this, worker_object);
    boost::function<void ()> run = boost::bind(
            &SingleObjectThread<T>::Run, cur_thread);
    assert(run);
    boost::thread* new_thread = new boost::thread(run);

    threads_.push_back(new_thread);
    inactive_sothreads_.push_back(cur_thread);
  }
}

template<class T>
void ObjectThreads<T>::AddWork(boost::function<void (T*)> work) {
  boost::unique_lock<boost::mutex> lock(threads_mutex_);
  while (running_sothreads_.size() >= max_threads_ &&
      inactive_sothreads_.size() == 0) {
    inactive_threads_available_.wait(lock);
  }
  SingleObjectThread<T>* cur_thread;
  if (inactive_sothreads_.size() > 0) {
    cur_thread = inactive_sothreads_.front();
    inactive_sothreads_.erase(inactive_sothreads_.begin());
    RunningThreadPointer i = running_sothreads_.insert(
        running_sothreads_.end(), cur_thread);
    cur_thread->AddWork(work, i);
  } else {
    assert(t_factory_);
    T* worker_object = t_factory_();
    cur_thread = new SingleObjectThread<T>(this, worker_object);
    RunningThreadPointer i = running_sothreads_.insert(
        running_sothreads_.end(), cur_thread);
    cur_thread->AddWork(work, i);
    boost::function<void ()> run = boost::bind(
            &SingleObjectThread<T>::Run, cur_thread);
    assert(run);
    boost::thread* new_thread = new boost::thread(run);
    threads_.push_back(new_thread);
  }
}

template<class T>
void ObjectThreads<T>::MarkInactive(RunningThreadPointer i) {
  LockGuard l(threads_mutex_);
  SingleObjectThread<T>* cur_thread = *i;
  running_sothreads_.erase(i);
  inactive_sothreads_.push_back(cur_thread);
  inactive_threads_available_.notify_all();
  if (running_sothreads_.size() == 0) {
    all_threads_inactive_.notify_all();
  }
}

template<class T>
int ObjectThreads<T>::NumThreads() const {
  LockGuard l(threads_mutex_);
  return running_sothreads_.size() + inactive_sothreads_.size();
}

template<class T>
int ObjectThreads<T>::NumRunningThreads() const {
  LockGuard l(threads_mutex_);
  return running_sothreads_.size();
}

template<class T>
int ObjectThreads<T>::NumInactiveThreads() const {
  LockGuard l(threads_mutex_);
  return inactive_sothreads_.size();
}

#endif
