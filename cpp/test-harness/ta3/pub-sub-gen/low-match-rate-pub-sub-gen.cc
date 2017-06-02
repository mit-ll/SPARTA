//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of LawMatchRatePubSubGen 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Jan 2013   omd            Original Version
//*****************************************************************

#include "low-match-rate-pub-sub-gen.h"

#include <algorithm>
#include <functional>

#include "common/util.h"

using std::map;
using std::string;
using std::vector;

// A functor used for comparing perfect subsets and perfect subset sizes. This
// inverts the normal ordering so that it returns true if the 1st subset is
// larger than the second so that our subsets_ array is sorted with the bigger
// subsets first. This is overloaded to compare two subsets or a subset and a
// size_t. The latter comparisons are used so we can use upper_bound() or other
// STL functions that search a sorted range for a subset whose size meets some
// criteria without having to acutally constructor a vector of that size.
class SubsetBiggerFunctor {
 public:
  bool operator()(const LowMatchRatePubSubGen::PerfectSubset& s1,
                  const LowMatchRatePubSubGen::PerfectSubset& s2) const {
    return s1.size() > s2.size();
  }

  bool operator()(size_t x,
                  const LowMatchRatePubSubGen::PerfectSubset& s2) const {
    return x > s2.size();
  }

  bool operator()(const LowMatchRatePubSubGen::PerfectSubset& s1,
                  size_t x) const {
    return s1.size() > x;
  }
};

// Explanation of the initialization of max_publication_size_: We need space for
// all the field values, plus all_fields->Size() - 1 "," characters plus the
// null terminator.
LowMatchRatePubSubGen::LowMatchRatePubSubGen(
    const FieldSet* all_fields, int rng_seed, bool keep_exhausted_fields)
    : all_fields_(all_fields), rng_(rng_seed),
      max_publication_size_(all_fields->TotalMaxLength() + all_fields->Size()),
      keep_exhausted_fields_(keep_exhausted_fields) {
  for (size_t i = 0; i < all_fields->Size(); ++i) {
    CHECK(all_fields->Get(i)->NumValues() > 1);
    available_fields_.push_back(i);
    // Initially not fields are used so just create an empty set. Knowing that
    // every field has a set simplifies code later.
    used_field_values_[i] = std::set<string>();
  }
}

void LowMatchRatePubSubGen::GenerateSubscriptions(
    int num_subscriptions, NumPredicatesGenerator num_pred_generator) {
  CHECK(subsets_.size() == 0) << "Subscriptions have already been generated. "
      << "You can't generate subscriptions more than once with the "
      << "same object.";

  int num_sub_generated = 0;
  int num_pred_for_next_group = -1;

  while (num_sub_generated < num_subscriptions) {
    int max_subset_size = num_subscriptions - num_sub_generated;
    PerfectSubset next_subset;
    num_pred_for_next_group = GeneratePerfectSubset(
        max_subset_size, num_pred_for_next_group, &next_subset,
        num_pred_generator);
    num_sub_generated += next_subset.size();
    subsets_.emplace_back(std::move(next_subset));
  }

  // Finally we sort the subsets by size so that we can quickly find all
  // subsets with at least X members when we want to generate publications.
  // There's no real reason to do a stable_sort here other than the fact that it
  // makes unit testing easier later. Ugly, but true ;)
  std::stable_sort(subsets_.begin(), subsets_.end(), SubsetBiggerFunctor());
}

int LowMatchRatePubSubGen::GeneratePerfectSubset(
    size_t max_subset_size, int num_preds_for_next, PerfectSubset* members,
    NumPredicatesGenerator num_pred_generator) {
  LOG(DEBUG) << "\nGenerating a perfect subset";
  DCHECK(members->empty());
  // These are the fields and values used thus far in this subscription
  map<int, string> values_used_this_sub;
 
  // This is an array of the sizes of the subscriptions we should generate for
  // this subset. It will be sorted so that larger values come first. This
  // allows us to easily ensure subscriptions are independent. See the paper in
  // the docs folder for details.
  vector<int> subscription_sizes;
  num_preds_for_next = GenerateSubscriptionSizes(
      max_subset_size, num_preds_for_next, num_pred_generator,
      &subscription_sizes);

  // Check that it is feasible to generate subscription_sizes.size()
  // subscripitions where the largest subscription has
  // subscription_sizes.front() predicates.
  DCHECK((available_fields_.size() - subscription_sizes.front() + 1) >=
         subscription_sizes.size()) << "Error! n - m + 1 == "
      << (available_fields_.size() - subscription_sizes.front() + 1)
      << " with n = " << available_fields_.size()
      << " and m = " << subscription_sizes.front()
      << " but we're trying to generate "
      << subscription_sizes.size() << " members of the subset";

  for (int num_preds : subscription_sizes) {
    LOG(DEBUG) << "Generating subscription with " << num_preds
               << " predicates";
    vector<int> fields_for_sub;
    GetFieldsForSub(num_preds, values_used_this_sub,
                    &fields_for_sub);
    // Generate the subscription
    EqualitySubscription subscription;
    for (auto& f : fields_for_sub) {
      if (values_used_this_sub.find(f) != values_used_this_sub.end()) {
        subscription.Add(EqualityCondition(f, values_used_this_sub[f]));
      } else {
        string value;
        all_fields_->Get(f)->RandomValueExcluding(
            used_field_values_[f], &value);
        subscription.Add(EqualityCondition(f, value));
        values_used_this_sub[f] = value;
        used_field_values_[f].insert(value);
      }
    }
    members->push_back(subscription);
    subscriptions_.push_back(subscription);
  }

  // Only remove things from available_fields_ at the end - it's OK if a field
  // gets used up *in* a subgroup.
  LOG(DEBUG) << "Updating available fields...";
  for (auto& field_pair : values_used_this_sub) {
    LOG(DEBUG) << "Investigating field #" << field_pair.first;
    // If we've used all by one value for a field we can't generate anything
    // else for that field.
    size_t num_field_vals = all_fields_->Get(field_pair.first)->NumValues();
    LOG(DEBUG) << "Field #" << field_pair.first << " has " << num_field_vals
               << " unique values";
    LOG(DEBUG) << "Field #" << field_pair.first << " has used "
               << used_field_values_[field_pair.first].size()
               << " unique values so far";
    DCHECK(num_field_vals > 1);
    if (used_field_values_[field_pair.first].size() >= (num_field_vals - 1)) {
      DCHECK(used_field_values_[field_pair.first].size() ==
            (num_field_vals - 1));

      if (keep_exhausted_fields_) {
        used_field_values_[field_pair.first].clear();
      } else {
        auto to_remove_it = find(
            available_fields_.begin(), available_fields_.end(), field_pair.first);
        DCHECK(to_remove_it != available_fields_.end());
        available_fields_.erase(to_remove_it);
      }
    }
  }

  return num_preds_for_next;
}

void LowMatchRatePubSubGen::GetFieldsForSub(
    size_t num_preds, const map<int, string>& values_used_this_sub,
    vector<int>* fields_for_sub) {
  // Each subscription in a perfect subset must contain at least one field that
  // isn't contained in any other subscription. These calculations ensure that's
  // the case. Making it *exactly* one field maximizes the size of the subset.
  int num_overlapping_fields = std::min(
      num_preds - 1, values_used_this_sub.size());
  int num_new_fields = num_preds - num_overlapping_fields;
  LOG(DEBUG) << "GetFieldsForSub: num fields used so far: "
             << values_used_this_sub.size();
  LOG(DEBUG) << "GetFieldsForSub: num overlapping fields: "
             << num_overlapping_fields;
  DCHECK(num_new_fields > 0);

  // This is pretty inefficient. Here we calculate field sets and put them in
  // vectors so we can randomly select from them. We do this each time this is
  // called instead of maintaining these sets. This makes it easier to guarnatee
  // correctness but at the cost of decreased performance. My assumption is that
  // subscription generation time isn't super time critical (unlike pub
  // generation) and that the number of fileds is fairly small (20 or so) so the
  // correctness guarantee outweights the efficiency concerns. If these
  // assumptions prove wrong this should be re-written.
  vector<int> fields_that_overalp;
  for (auto vu : values_used_this_sub) {
    fields_that_overalp.push_back(vu.first);
  }

  vector<int> unused_available_fields;
  for (auto f : available_fields_) {
    if (values_used_this_sub.find(f) == values_used_this_sub.end()) {
      unused_available_fields.push_back(f);
    }
  }
  LOG(DEBUG) << "GetFieldsForSub: fields NOT used so far: "
             << unused_available_fields.size();

  DCHECK(fields_that_overalp.size() >=
        static_cast<size_t>(num_overlapping_fields));
  DCHECK(unused_available_fields.size() >= static_cast<size_t>(num_new_fields))
      << "Can't select " << num_preds << " fields. There are a total of "
      << available_fields_.size() << " fields avaialable of which "
      << fields_that_overalp.size() << " have already been used in this "
      << "subset. Thus there are only " << unused_available_fields.size()
      << " unused fields left but we need " << num_new_fields;

  if (num_overlapping_fields > 0) {
    RandomSubset(num_overlapping_fields, fields_that_overalp.begin(),
                 fields_that_overalp.end(), &rng_,
                 back_inserter(*fields_for_sub));
  }
  RandomSubset(num_new_fields, unused_available_fields.begin(),
               unused_available_fields.end(), &rng_,
               back_inserter(*fields_for_sub));
}

void LowMatchRatePubSubGen::GetSubsetsGE(
    size_t x, SubsetIterator* start, SubsetIterator* end) {
  *start = subsets_.begin();
  *end = std::upper_bound(subsets_.begin(), subsets_.end(),
                          x, SubsetBiggerFunctor());
}

int LowMatchRatePubSubGen::GenerateSubscriptionSizes(
    int max_size, int size_of_first, NumPredicatesGenerator num_pred_generator,
    vector<int>* subscription_sizes) {
  // size_of_first may no longer be feasible if some fields got "used up"
  // buildling the last subset. In that case we discard it and draw a new
  // number. size_of_first can also be -1 when this is called for the 1st subset
  // in which case we need to generate the 1st random number.
  if (static_cast<size_t>(size_of_first) > available_fields_.size()
      || size_of_first == -1) {
    if (size_of_first > 0) {
      LOG(DEBUG) << size_of_first << " fields are no longer available. "
          << "Drawing a new random value.";
    }
    size_of_first = num_pred_generator(available_fields_.size());
    DCHECK(static_cast<size_t>(size_of_first) <= available_fields_.size());
  }
  //LOG(DEBUG) << "GenerateSubscriptionSizes: size_of_first: " << size_of_first;
  LOG(DEBUG) << "GenerateSubscriptionSizes: available_fields: " 
            << available_fields_.size();
  // As per the paper in the docs sub-folder, the maximum number of
  // subscriptions in a group is bounded by n - m + 1 >= s, where n is the
  // number of available fields, m is the maximum subscription size, and s is
  // the number of elements in the subgroup. Thus, we keep generating
  // subscription sizes until the new size violates this constraint.
  int m = size_of_first;
  DCHECK((available_fields_.size() - m + 1) >= 1);

  int next_size = size_of_first;

  // As long as we can fit another subscription whose size is <= m add that to
  // the set of subscription sizes and generate a new next_size value.
  while ((subscription_sizes->size() + 1) <=
         (available_fields_.size() - m + 1) &&
         subscription_sizes->size() < static_cast<size_t>(max_size)) {
    subscription_sizes->push_back(next_size);
    next_size = num_pred_generator(available_fields_.size());
    DCHECK(static_cast<size_t>(next_size) <= available_fields_.size());
    m = std::max(m, next_size);
  }

  sort(subscription_sizes->begin(), subscription_sizes->end(),
       std::greater<int>());

  return next_size;
}
    
const std::set<string>* LowMatchRatePubSubGen::GetUsedValuesForField(
    int field_id) const {
  CHECK(static_cast<size_t>(field_id) < all_fields_->Size());
  auto used_it = used_field_values_.find(field_id);
  CHECK(used_it != used_field_values_.end());
  return &used_it->second;
}

vector<EqualitySubscription> LowMatchRatePubSubGen::GetPublication(
    int n, size_t max_pub_len, char* pub_out) {
  vector<EqualitySubscription> matching_subscriptions;
  matching_subscriptions.reserve(n);

  SubsetIterator subset_start, subset_end;
  LOG(DEBUG) << "Searching for sets with >= " << n << " subscriptions";
  GetSubsetsGE(n, &subset_start, &subset_end);
  LOG(DEBUG) << "Found " << (subset_end - subset_start) << " sets  with >= " << n << " subscriptions";
  if (subset_start == subset_end) {
    *pub_out = '\0';
    return matching_subscriptions;
  }

  std::uniform_int_distribution<> dist(0, subset_end - subset_start - 1);
  int subset_idx = dist(rng_);
  LOG(DEBUG) << "Picking subset #" << subset_idx;

  const PerfectSubset& subset = *(subset_start + subset_idx);
  LOG(DEBUG) << "Subset #" << subset_idx << " has " << subset.size() 
             << " items";
  RandomSubset(n, subset.begin(), subset.end(), &rng_,
               std::back_inserter(matching_subscriptions));
  GetPublication(matching_subscriptions.begin(), matching_subscriptions.end(),
                 max_pub_len, pub_out);

  return matching_subscriptions;
}
