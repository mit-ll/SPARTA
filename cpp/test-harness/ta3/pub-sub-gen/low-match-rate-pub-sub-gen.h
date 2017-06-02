//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A generator for low match rates. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Jan 2013   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA3_PUB_SUB_GEN_LOW_MATCH_RATE_PUB_SUB_GEN_H_
#define CPP_TEST_HARNESS_TA3_PUB_SUB_GEN_LOW_MATCH_RATE_PUB_SUB_GEN_H_

#include <functional>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include "common/check.h"
#include "common/string-algo.h"
#include "test-harness/ta3/fields/field-base.h"
#include "test-harness/ta3/fields/field-set.h"

class EqualityCondition : public std::pair<int, std::string> {
 public:
  EqualityCondition(int fid, const std::string& val) :
      std::pair<int, std::string>(fid, val) {}
  int field() const { return first; }
  const std::string& value() const { return second; }
};

class EqualitySubscription {
 public:
  int NumPredicates() const {
    return conditions_.size();
  }

  const EqualityCondition* GetCondition(int i) const {
    CHECK(i < NumPredicates());
    return &conditions_[i];
  }
  void Add(const EqualityCondition& condition) {
    conditions_.emplace_back(condition);
  }
  void Add(const EqualityCondition&& condition) {
    conditions_.emplace_back(condition);
  }

  std::string ToString() {
    std::string output;
    for (auto cond : conditions_) {
      output += itoa(cond.field()) + ":" + cond.value() + ","; 
    }
    return output;
  }
 private:
  std::vector<EqualityCondition> conditions_;
};

/// This class is designed to generate subscriptions and publications such that
/// it is quite flexible in the set of subscriptions that will match the
/// publication. See the docs subfolder for details on how this class works and
/// an introduction to some of the terminology used here.
class LowMatchRatePubSubGen {
 public:
  /// Constructor. Does not take ownership of all_fields. rng_seed is the seed
  /// for the random number generator used to generate publications and
  /// subscriptions.
  LowMatchRatePubSubGen(const FieldSet* all_fields,
                        int rng_seed, bool keep_exhausted_fields);
  virtual ~LowMatchRatePubSubGen() {}

  /// A function that returns the number of predicates the conjunction clause
  /// should contain. This can be deterministic or random depending on the test
  /// we want to perform. The argument is the number of fields that are
  /// available. The returned value must always be <= the number of available
  /// fields.
  typedef std::function<int (int)> NumPredicatesGenerator;
  /// Generates num_subscriptions each in a perfectly compatible subset that is
  /// as large as possible. overlap is the desired number of subscriptions that
  /// in each subset that overlap (e.g. it's v in the paper in the docs
  /// subfolder). num_pred_generator indicates how many fields each subscription
  /// should have (see docs on the typedef above).
  void GenerateSubscriptions(
      int num_subscriptions, NumPredicatesGenerator num_pred_generator);

  /// Given the subscriptions yielded by iterating over [sub_start, sub_end)
  /// generate a publication that matches those subscriptions and no others.
  /// Dereference sub_start must yeild an EqualitySubscription.  On return
  /// pub_out will be a comma separated set of field values with the desired
  /// properties. pub_out must point to an array of size MaxPublicationSize().
  /// It may be handy to use this with a BufferPool whose buffers are all
  /// MaxPublicationSize() bytes in size. Note that this *will* null-terminate
  /// put_out. max_pub_len is the memory avaialable to pub_out. It is here just
  /// as a sanity check (e.g. snprintf vs. sprintf).
  template<class InIterT>
  void GetPublication(
      InIterT sub_start, InIterT sub_end,
      size_t max_pub_len, char* pub_out) const;

  /// A convenience method that generates a random publication that will match n
  /// subscriptions. Returns the subscriptions that should match.  If it is
  /// impossible to generate such a publication because n is too large
  /// *pub_out == '\0' on return and the returned vector will be empty.
  ///
  /// This method is not const as it uses the random number generator.
  std::vector<EqualitySubscription> GetPublication(
      int n, size_t max_pub_len, char* pub_out);

  /// The maximum size any publication could have.
  size_t MaxPublicationSize() const {
    return max_publication_size_;
  }

  /// Returns the set of all subscriptions. Note that these are *not* grouped by
  /// perfectly compatible subgroup and so probably can't easily be used to
  /// generate publications. However, GetSubsetsGE can be used for that purpose.
  const std::vector<EqualitySubscription>* GetAllSubscriptions() const {
    return &subscriptions_;
  }

  /// A set of subscriptions that forms a perfectly compatible subset.
  typedef std::vector<EqualitySubscription> PerfectSubset;
  typedef std::vector<PerfectSubset>::const_iterator SubsetIterator;
  /// Given pointers to two random access iterators and a number, x, sets the
  /// iterators so they the PerfectSubsets between the start (inclusive) and
  /// end (exclusive) all have >= x subscriptions in them.
  void GetSubsetsGE(size_t x, SubsetIterator* start, SubsetIterator* end);

  /// Returns all the subsets. Basically the same thing as GetSubsetsGE(0, ...)
  /// except that it returns a vector instead of setting iterators.
  const std::vector<PerfectSubset>* GetAllSubsets() const {
    return &subsets_;
  }

  const std::set<std::string>* GetUsedValuesForField(int field_id) const;

 private:
  /// Generates a single perfectly compatible subset. Args:
  ///
  /// max_subset_size: The maximum number of subscriptions in the subset.
  /// num_preds_for_next: The number of predicates that the 1st subscription
  ///     should have. -1 indicates that a random value should be drawn.
  ///     See the return value for details.
  /// members: This will be filled in with new subscripitions.
  /// num_pred_generator: A function that will be used to generate the number of
  ///     predicates in each subscription. It will be called once for each
  ///     subscription generated.
  ///
  /// Returns:
  ///    The value of num_preds_for_next that should be passed to generate the
  ///    next subset. We do this because we keep generating subscriptions until
  ///    the number of predicates requested in the next subscription isn't
  ///    possible. If we simply discarded that value and num_pred_generator was a
  ///    random number generator we'd skew the distribution towards smaller
  ///    subscriptions. Thus we return the last value generated so it can be
  ///    passed in to the next call ensuring that the next subscription starts
  ///    with this many predicates.
  int GeneratePerfectSubset(
      size_t max_subset_size, int num_preds_for_next, PerfectSubset* members,
      NumPredicatesGenerator num_pred_generator);

  /// Generates a size for each subscription in a perfect subset. Will generate
  /// up to max_size of them if possible. It uses num_pred_generator to generate
  /// the subscriptions and will ensure that the 1st subscription contains
  /// size_of_first predicates. It returns the number of predicates the 1st
  /// subscription in the *next* subset should have. The reason for size_of_first
  /// and the return value is the same as num_preds_for_next and the return value
  /// on GeneratePerfectSubset; see that method for details.
  int GenerateSubscriptionSizes(
    int max_size, int size_of_first, NumPredicatesGenerator num_pred_generator,
    std::vector<int>* subscription_sizes);

  /// Given a subscription that is going to have num_preds_for_next predicates
  /// and a map indicating the values used so far in this subgroup select fields
  /// for the new subscription and put them in fields_for_sub.
  void GetFieldsForSub(
    size_t num_preds_for_next,
    const std::map<int, std::string>& values_used_this_sub,
    std::vector<int>* fields_for_sub);

  /// This is the list of all generated subscriptions though not grouped by
  /// perfect subset.
  std::vector<EqualitySubscription> subscriptions_;

  /// After all subscriptions get generated this gets sorted by subset size. That
  /// way we can quickly find all subsets that could satisfy a publication
  /// request.
  std::vector<PerfectSubset> subsets_;
  /// Map from field number to the set of values used in any subscription.
  std::map<int, std::set<std::string> > used_field_values_;
  /// All the fields being used in the test.
  const FieldSet* all_fields_;

  /// Initially all fields are "available" to be used in a subscription. However,
  /// we have to always leave at least one value that's not used in any
  /// subscription so we can generate publications that don't match hosts using
  /// that field. This is the set of fields (as a vector so we can easily
  /// randomly choose values from it) that are still available for use.
  std::vector<int> available_fields_;

  std::mt19937 rng_;

  int max_publication_size_;

  bool keep_exhausted_fields_;
};

////////////////////////////////////////////////////////////////////////////////
// Template method definitions
////////////////////////////////////////////////////////////////////////////////

template<class InIterT>
void LowMatchRatePubSubGen::GetPublication(
    InIterT sub_start, InIterT sub_end,
    size_t max_pub_len, char* pub_out) const {
  CHECK(max_pub_len >= MaxPublicationSize());
  /// map from fields in the subscriptions to the values they must have.
  std::map<int, std::string> sub_field_map;
  for (InIterT i = sub_start; i != sub_end; ++i) {
    for (int cond_i = 0; cond_i < i->NumPredicates(); ++cond_i) {
      const EqualityCondition* cond = i->GetCondition(cond_i);
      auto sub_field_map_it = sub_field_map.find(cond->field());
      if (sub_field_map_it == sub_field_map.end()) {
        sub_field_map[cond->field()] = cond->value();
      } else {
        CHECK(sub_field_map[cond->field()] == cond->value())
            << "Subscriptions passed to GetPublication are not compatible.";
      }
    }
  }

  char* out_ptr = pub_out;
  for (size_t f_id = 0; f_id < all_fields_->Size(); ++f_id) {
    auto sf_it = sub_field_map.find(f_id);
    if (sf_it == sub_field_map.end()) {
      const FieldBase* f = all_fields_->Get(f_id);
      out_ptr = f->RandomValueExcluding(
          used_field_values_.at(f_id), f->MaxLength(), out_ptr);
    } else {
        memcpy(out_ptr, sf_it->second.data(), sf_it->second.size());
        out_ptr += sf_it->second.size();
    }
    if (f_id < (all_fields_->Size() - 1)) {
      *out_ptr = ',';
      ++out_ptr;
    }
  }
  *out_ptr = '\0';
}

#endif
