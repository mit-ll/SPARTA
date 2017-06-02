//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Definition and implmentation of AggregatingFuture and
//                     supporting classes.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 15 Nov 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_AGGREGATING_FUTURE_H_
#define CPP_COMMON_AGGREGATING_FUTURE_H_

#include "future.h"

/// FutureAggregator is used to aggregate many partial results and then combine
/// them into a single Future. Consider a simple example. Suppose you have a long
/// running thread that is going to compute a long string of integers and you
/// want to compute the sum of those integers. With a non-aggregating future you
/// could have a Future<list<int> >, have the thread concatenate all of the
/// integers into a list and then Fire the future. The waiting thread could then
/// sum up all the integers once the future has been fired. However, this
/// requires that all the integers generated get stored in memory until Fire is
/// called. A more efficient alternative is to sum up the integers as they are
/// generated.
///
/// To support this you can construct a AggregatingFuture and pass that to the
/// data generating thread.  The generating thread(s) can then call
/// AddPartialResult on the FutureAggregator each time a new integer is created.
/// Finally, when the generation process is done, the generator calls Done().
/// This will cause the AggregatingFuture to call Finalize() in order to get the
/// final result (which may have a different type from the intermediate results).
/// From there, everything proceeds as it would with a normal future. For
/// example:
///
/// // Computes the mean of a set of integers. Thus AddPartialResult expects
/// // integers and Finalize() returns a float.
/// class AverageComputer : public FutureAggregator<float, int> {
///  public:
///   AverageComputer() : sum_(0), n_(0) {}
///   virtual void AddPartialResult(const int& v) {
///     ++n_;
///     sum_ += v;
///   }
///
///   virtual float Finalize() {
///     return float(sum_) / float(n_);
///   }
/// };
///
/// AverageComputer* agg = new AverageComputer;
///
/// ComputeIntegersInThread(agg);
///
/// Future<float> f = agg->GetFuture();
///
/// ... Do other stuff while the integers are generated ...
///
/// cout << "The average of the integers is: " << f.Value();
///
/// Note that FutureAggregator inherits from PartialFutureAggregator and the
/// template for that only specifies the type of the intermediate results, not
/// the type of the final result (which is the type of the returned Future).
/// Thus, the generating process works regardless of the type of the aggregation
/// result. For example, a very simple generator might look like:
///
/// void ComputeIntegers(PartialFutureAggregator<int> agg) {
///   for (int i = 1; i <= 100; ++i) {
///     agg.AddPartialResult(i);
///   }
///   agg.Done();
/// }
///
/// And this would work with an aggregator that concatenates all the integers
/// into a long string as well as it would work with one that computes the
/// average.
///
/// Note that AddPartialResult is not thread safe and no ordering is enforced.
/// The threads calling AddPartialResult must generate results in the correct
/// order if the FutureAggregator cares about ordering (e.g. one that computes a
/// sum is order independent while one that concatenates the results into a list
/// is order dependent). If ordering matters or multiple threads are calling
/// AddPartialResult either the FutureAggregator subclass or the generating
/// process must use proper synchronization.
///
/// Also note that aggregators are generally stateful and that this is carefully
/// designed to ensure that the data generating process is as ignorant as
/// possible of the functionality of the aggregator. Thus, generating processes
/// should not assume the FutureAggregator of PartialFutureAggregator can be
/// cheaply copied. The generators should generally take a pointer to the
/// aggregator.


/// Forward declaration.
template<class ResultT, class AggT> class FutureAggregator;

/// As noted above, this is used by data generation processes so they don't have
/// to be aware of the type returned by FutureAggregator::Finalize().
template<class AggT>
class PartialFutureAggregator {
 public:
  virtual ~PartialFutureAggregator() {}
  /// Data generation processes call this when part of the results are ready.
  virtual void AddPartialResult(const AggT& partial_result) = 0;
  /// Data generation processes call this when the data generation is complete.
  /// This cases the Finalize() method to be called on the associated
  /// FutureAggregator and the associated Future to fire.
  virtual void Done() = 0;
 private:
  /// Ensure that only FutureAggregator can construct one of these.
  PartialFutureAggregator() {}
  template<class ResultT, class AggType> friend class FutureAggregator;
};

template<class ResultT, class AggT>
class FutureAggregator : public PartialFutureAggregator<AggT> {
 public:
  virtual ~FutureAggregator() {}
  virtual void AddPartialResult(const AggT& partial_result) = 0;

  Future<ResultT> GetFuture() {
    return future_;
  }

  virtual void Done() {
    future_.Fire(Finalize());
  }

 protected:
  virtual ResultT Finalize() = 0;

 private:
  Future<ResultT> future_;
};


#endif
