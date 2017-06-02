//*****************************************************************
// Copyright 2011 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for ObjectThreads.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 26 Oct 2011   omd            Added this header
//*****************************************************************

#include "object_threads.h"

#define BOOST_TEST_MODULE ObjectThreadsTest

#include <boost/bind.hpp>
#include <boost/random/mersenne_twister.hpp>
#include <boost/random/uniform_int.hpp>
#include <boost/thread/barrier.hpp>
#include <boost/thread/thread.hpp>
#include <ctime>
#include <iostream>

#include "conditions.h"
#include "test-init.h"

using std::cout;
using std::endl;

class TestClass {
 public:
  TestClass() {}
  // Method that waits for a condition variable to become true.
  void BlockingWork(SimpleCondition<bool>* condition, bool* work_done) {
    condition->Wait(true);
    *work_done = true;
  }

  // This method does not wait on anything. It just runs.
  void NonBlockingWork(bool* work_done) {
    *work_done = true;
  }

  // Do num_iters of cpu intensive work
  void CPUWork(int num_iters, int* iters_done) {
    for (int i = 0; i < num_iters; ++i) {
      *iters_done += 1;
    }
  }
};

TestClass* TestClassMaker() {
  return new TestClass;
}

BOOST_AUTO_TEST_CASE(BasicTest) {
  // Booleans that should be set to true when the work is complete
  bool work1_done = false;
  bool work2_done = false;
  bool work3_done = false;

  // Scope so ot gets destructed. Since the destrcutor waits for all threads to
  // exit we can check the work*_done bools at the end of the scope.
  {
    ObjectThreads<TestClass> ot(&TestClassMaker);
    SimpleCondition<bool> condition(false);

    ot.AddWork(boost::bind(&TestClass::BlockingWork, _1, &condition,
                           &work1_done));
    BOOST_CHECK_EQUAL(ot.NumThreads(), 1);
    // Since the 1st thread is busy (blocked on condition) this should spawn
    // a new thread.
    ot.AddWork(boost::bind(&TestClass::BlockingWork, _1, &condition,
                           &work2_done));
    BOOST_CHECK_EQUAL(ot.NumThreads(), 2);
    // Wake up both threads so they finish.
    condition.Set(true);

    // Wait for the threads to finish and become inactive.
    while (ot.NumInactiveThreads() < 2) {
      BOOST_TEST_MESSAGE("Some threads still active. Sleeping");
      boost::this_thread::sleep(boost::posix_time::milliseconds(100));
    }
    BOOST_TEST_MESSAGE("Threads are all inactive");
    BOOST_CHECK(work1_done);
    BOOST_CHECK(work2_done);

    BOOST_CHECK_EQUAL(ot.NumThreads(), 2);
    // Since there are two free threads this shouldn't createa new one. Instead,
    // one of the existing threads should be reused.
    ot.AddWork(boost::bind(&TestClass::NonBlockingWork, _1, &work3_done));
    BOOST_CHECK_EQUAL(ot.NumThreads(), 2);
  }
  BOOST_CHECK(work3_done);
}

// Construct an instance of ObjectThreads, give it some work to do, let its
// destructor get called so all the work completes. Do it again. The idea here
// is to trigger any deadlocks or other issues with only a single thread so its
// easy to debug.
BOOST_AUTO_TEST_CASE(SingleThreadStress) {
  const int NUM_ITERS = 100;
  const int NUM_CPU_ITERS = 100;
  for (int i = 0; i < NUM_ITERS; ++i) {
    int work_done = 0;
    {
      ObjectThreads<TestClass> ot(&TestClassMaker);
      ot.AddWork(boost::bind(
              &TestClass::CPUWork, _1, NUM_CPU_ITERS, &work_done));
    }
    BOOST_CHECK_EQUAL(work_done, NUM_CPU_ITERS);
  }
}

// Spawn a ton of threads and make sure they all eventually run.
BOOST_AUTO_TEST_CASE(StressTest) {
  // We'll do this many CPU intensive calls.
  const int NUM_CPU_INTENSIVE_TASKS = 1000;
  const int MIN_CPU_ITERS = 100;
  const int MAX_CPU_ITERS = 100000;
  // This is how many iterations we'd like to do per cpu intensive task.
  vector<int> cpu_iters;
  cpu_iters.reserve(NUM_CPU_INTENSIVE_TASKS);
  boost::mt19937 rng(std::time(0));
  boost::uniform_int<> dist(MIN_CPU_ITERS, MAX_CPU_ITERS);
  // Randomly generate the number of iterations to do for each task.
  for (int i = 0; i < NUM_CPU_INTENSIVE_TASKS; ++i) {
    cpu_iters.push_back(dist(rng));
  }
  // This is how many iterations were actually done. When all the threads have
  // exited it should be equal to the cpu_iters vector above.
  vector<int> cpu_work_done(NUM_CPU_INTENSIVE_TASKS, 0);

  {
    ObjectThreads<TestClass> ot(&TestClassMaker);
    for (int i = 0; i < NUM_CPU_INTENSIVE_TASKS; ++i) {
      ot.AddWork(boost::bind(&TestClass::CPUWork, _1, cpu_iters[i],
                             &cpu_work_done[i]));
    }
    // We should have re-used some threads. There's no exactly correct number
    // here but I'd expect at least half of the threads to be reused.
    BOOST_CHECK_LT(ot.NumThreads(), NUM_CPU_INTENSIVE_TASKS / 2);
  }

  for (int i = 0; i < NUM_CPU_INTENSIVE_TASKS; ++i) {
    BOOST_CHECK_EQUAL(cpu_work_done[i], cpu_iters[i]);
  }
}

// Make sure we can prespawn threads
BOOST_AUTO_TEST_CASE(SpawnTest) {
  const int NUM_THREADS = 10;
  bool work_done = false;
  {
    ObjectThreads<TestClass> ot(&TestClassMaker);
    ot.Spawn(NUM_THREADS);
    BOOST_CHECK_EQUAL(ot.NumThreads(), NUM_THREADS);
    BOOST_CHECK_EQUAL(ot.NumInactiveThreads(), NUM_THREADS);
    BOOST_CHECK_EQUAL(ot.NumRunningThreads(), 0);

    ot.AddWork(boost::bind(&TestClass::NonBlockingWork, _1, &work_done));
    // ot should have re-used an existing thread to do this work.
    BOOST_CHECK_EQUAL(ot.NumThreads(), NUM_THREADS);
  }
  // Now that ot has gone out of scope the work should be done.
  BOOST_CHECK_EQUAL(work_done, true);
}

// This method will be used in several threads in the ThreadsSharingPool test
// below. See that test for details.
void RunInPool(int num_iters, bool* work_done,
               ObjectThreads<TestClass>* thread_pool) {
  for (int i = 0; i < num_iters; ++i) {
    thread_pool->AddWork(
        boost::bind(&TestClass::NonBlockingWork, _1, work_done + i));
  }
}

// We want to be able to have multiple threads that share an ObjectThreads pool.
// This requires the AddWord method to be thread safe. This test ensures that if
// we have multiple threads sharing the pool we don't end up with more threads
// than the max allowed.
BOOST_AUTO_TEST_CASE(ThreadsSharingPool) {
  const int kNumThreadsSharing = 5;
  const int kNumItersPerThread = 100;
  // We need to check that all the work gets done eventually. We can't use
  // vector<bool> as that does weird proxy-stuff so we allocate an array of
  // arrays, one array for each of the sharing threads.
  bool* work_done[kNumThreadsSharing];
  for (int i = 0; i < kNumThreadsSharing; ++i) {
    work_done[i] = new bool[kNumItersPerThread];
    memset(work_done[i], false, kNumItersPerThread * sizeof(bool));
  }

  // Enclosing scope. When ObjectThreads goes out of scope it will block until
  // all the threads in the pool are done. At that point we can check tha they
  // all completed successfully.
  {
    ObjectThreads<TestClass> ot(&TestClassMaker);
    const int kNumThreadsInPool = 2;
    ot.set_max_threads(kNumThreadsInPool);


    // Each thread will be spawned and do 100 iterations of non-CPU intensive
    // work so that the threads collide often.
    vector<boost::thread*> threads;

    for (int i = 0; i  < kNumThreadsSharing; ++i) {
      boost::thread* t = new boost::thread(&RunInPool, kNumItersPerThread,
                                           work_done[i], &ot);
      threads.push_back(t);
    }

    // Now wait for all the threads to complete.
    for (auto i = threads.begin(); i != threads.end(); ++i) {
      (*i)->join();
      delete *i;
    }

    BOOST_CHECK_LE(ot.NumThreads(), kNumThreadsInPool);
  }

  for (int i = 0; i < kNumThreadsSharing; ++i) {
    for (int j = 0; j < kNumItersPerThread; ++j) {
      BOOST_CHECK_EQUAL(work_done[i][j], true);
    }
    delete[] work_done[i];
  }
}
