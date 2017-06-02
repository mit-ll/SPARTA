//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for LowMatchRatePubSubGen 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 28 Jan 2013   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE LowMatchRatePubSubGenTest
#include "common/test-init.h"

#include "low-match-rate-pub-sub-gen.h"

#include <boost/assign/list_inserter.hpp>
#include <boost/assign/list_of.hpp>
#include <chrono>
#include <map>
#include <set>
#include <sstream>
#include <string>

#include "num-predicate-generators.h"
#include "test-harness/ta3/fields/testing-field-set.h"

using namespace std;
namespace assign = boost::assign;
using boost::assign::list_of;

// Adds to a boost::test_tools::predicate_result message a listing of the
// field/value assignments for every subscription in the passed subset.
void AppendSubscriptionDefinitions(
    const FieldSet& all_fields,
    const LowMatchRatePubSubGen::PerfectSubset& subset,
    boost::test_tools::predicate_result* res) {
  for (size_t i = 0; i < subset.size(); ++i) {
    res->message() << i << ": ";
    for (int j = 0; j < subset[i].NumPredicates(); ++j) {
      const EqualityCondition* cond = subset[i].GetCondition(j);
      res->message() << "(" << all_fields.Get(cond->field())->name()
          << " = '" << cond->value() << "') ";
    }
    res->message() << "\n";
  }
}

// Called AppendSubscriptionDefinitions for each subset.
void AppendSubsetDefinitions(
    const FieldSet& all_fields,
    const std::vector<LowMatchRatePubSubGen::PerfectSubset>& subsets,
    boost::test_tools::predicate_result* res) {
  int i = 0;
  for (const auto& subset : subsets) {
    res->message() << "\n=====\nSubset " << i << ":\n";
    ++i;
    AppendSubscriptionDefinitions(all_fields, subset, res);
  }
}

// Re-used in several unit tests. This takes a std::multiset of expected number
// of predicates as input. It checks that the number of subscriptions in the
// subset match the size of the multiset and it checks that number of
// predicates in each subscription matches the values in the multiset. This
// modifies the multiset as part of it's processing.
boost::test_tools::predicate_result
NumberOfPredicatesMatches(
    const FieldSet& fs,
    const LowMatchRatePubSubGen::PerfectSubset& subset,
    multiset<int>* expected) {
  if (subset.size() != expected->size()) {
    boost::test_tools::predicate_result res(false);
    res.message() << "Subset was expected to contain "
        << expected->size() << " subscriptions but it "
        << "contained " << subset.size()
        << ". Subset:\n";
    AppendSubscriptionDefinitions(fs, subset, &res);
    return res;
  }

  for (const auto& subscription : subset) {
    auto sub_size_it = expected->find(subscription.NumPredicates());
    if (sub_size_it == expected->end()) {
      boost::test_tools::predicate_result res(false);
      res.message() << "Subscription with "
          << subscription.NumPredicates() << " predicates "
          << " unexpected. Subscriptions in subset:\n";
      AppendSubscriptionDefinitions(fs, subset, &res);
      return res;
    }

    expected->erase(sub_size_it);
  }
  CHECK(expected->empty());

  return true;
}


// The following is re-used in several tests to ensure that an ostensibly
// perfectly compatible subset had the same value assigned to a field in all
// subscriptions that match against that field. Thus, if subscription A in a
// subset has a condition like 'fname =  X' and subscription C has a condition
// like 'fname = Z' we require that X = Z.
boost::test_tools::predicate_result
OverlappingFieldsSame(const FieldSet& all_fields,
                      const LowMatchRatePubSubGen::PerfectSubset& subset) {
  // map from field # to the value it was assigned in the subset.
  map<int, string> assigned_vals;
  for (auto& sub : subset) {
    for (int i = 0; i < sub.NumPredicates(); ++i) {
      const EqualityCondition* cond = sub.GetCondition(i);
      if (assigned_vals.find(cond->field()) == assigned_vals.end()) {
        assigned_vals[cond->field()] = cond->value();
      } else {
        if (assigned_vals[cond->field()] != cond->value()) {
          boost::test_tools::predicate_result res(false);
          res.message()
              << "Error! Subscription assigned "
              << cond->value() << " to "
              << all_fields.Get(cond->field())->name()
              << " but that field was already assigned "
              << assigned_vals[cond->field()]
              << ". Subscriptions:\n";
          AppendSubscriptionDefinitions(all_fields, subset, &res);
          return res;
        }
      }
    }
  }
  return true;
}

// Re-used in several tests to ensure that every subscription in a perfectly
// compatible subset contains a match on a field that no other subscription in
// the set does. That's how we can be sure to target any individual host in the
// subset.
boost::test_tools::predicate_result
AllSubscriptionsHaveUniqueField(
    const FieldSet& all_fields,
    const LowMatchRatePubSubGen::PerfectSubset& subset) {
  for (size_t i = 0; i < subset.size(); ++i) {
    // Build a set containing the fields in this subscription.
    set<int> fields_in_cur_sub;
    for (int k = 0; k < subset[i].NumPredicates(); ++k) {
      fields_in_cur_sub.insert(subset[i].GetCondition(k)->field());
    }

    // Now check that every other subscription contains at least one field not
    // in this subscription.
    for (size_t j = 0; j < subset.size(); ++j) {
      if (i == j) continue;
      bool sub_ok = false;
      // Extract all fields in all predicates in subscription j
      for (int k = 0; k < subset[j].NumPredicates(); ++k) {
        const EqualityCondition* cond = subset[j].GetCondition(k);
        if (fields_in_cur_sub.find(cond->field()) ==
            fields_in_cur_sub.end()) {
          sub_ok = true;
          break;
        }
      }

      if (! sub_ok) {
        boost::test_tools::predicate_result res( false );
        res.message() << "Error! Subscription " << i
            << " and " << j << "subscribe use the same set of fields. "
            << "Subscriptions:\n";
        AppendSubscriptionDefinitions(all_fields, subset, &res);
        return res;
      }
    }
  }

  return true;
}

// Helper method used by SubsetsIndependent. Fills in mapping so mapping[i] ==
// the value the subset assigns to field i. Also makes sure that mappings are
// unique in the subset.
void GetFieldMappings(
    const LowMatchRatePubSubGen::PerfectSubset& subset,
    map<int, string>* mapping) {
  for (const auto& subscription : subset) {
    for (int cond_i = 0; cond_i < subscription.NumPredicates(); ++cond_i) {
      const EqualityCondition* cond = subscription.GetCondition(cond_i);
      if (mapping->find(cond->field()) == mapping->end()) {
        mapping->insert(make_pair(cond->field(), cond->value()));
      } else {
        CHECK(mapping->at(cond->field()) == cond->value())
            << "Very unexpected error! Subset has two different "
            << "subscriptions with different values for the same field. "
            << "Field " << cond->field() << " is assigned "
            << cond->value() << " and " << mapping->at(cond->field());
      }
    }
  }
}

// Also a general, re-usable check. This ensures that a publication that
// subscriptions in one subset are "independent" of another; in other words a
// publication can be crafted to match subscriptions in one subgroup that don't
// hit any subscriptions in the other. The only caveat here is when the overlap
// is non-zero. In that case it is permissible for up to two other subsets
// to have up to overlap subscriptions that aren't independent of the source
// subset. 2 are allowed as a subset can have overlap with the subset that was
// generated before it and the one that was generated after it.
boost::test_tools::predicate_result
SubsetsIndependent(
    const FieldSet& all_fields,
    const vector<LowMatchRatePubSubGen::PerfectSubset>& subsets) {
  for (size_t i = 0; i < subsets.size(); ++i) {
    // For each subset build a map of the fields -> values that define the
    // subset.
    map<int, string> cur_field_mappings;
    GetFieldMappings(subsets[i], &cur_field_mappings);

    for (size_t j = 0; j < subsets.size(); ++j) {
      if (i == j) continue;
      
      int num_overlapping_subscriptions = 0;
      for (const auto& subscription : subsets[j]) {
        bool subscription_overlaps = true;
        for (int cond_i = 0; cond_i < subscription.NumPredicates();
             ++cond_i) {
          const EqualityCondition* cond = subscription.GetCondition(cond_i);
          if (cur_field_mappings.find(cond->field()) !=
              cur_field_mappings.end()) {
            if (cur_field_mappings[cond->field()] != cond->value()) {
              // There's at least one field that doesn't match
              // cur_field_mappings so this subscription doesn't overlap
              subscription_overlaps = false;
              break;
            }
          } else {
            // We have a field that's not in the other subset at all.
            subscription_overlaps = false;
            break;
          }
        }
        if (subscription_overlaps) {
          ++num_overlapping_subscriptions;
        }
      }
      if (num_overlapping_subscriptions > 0) {
        boost::test_tools::predicate_result res(false);
        res.message() << "Error! "<< num_overlapping_subscriptions
            << " subscriptions overlap. Offending subsets are "
            << i << " and " << j << ".\nSubsets:\n";
        AppendSubsetDefinitions(all_fields, subsets, &res);
        return res;
      }
    }
  }

  return true;
}

// Check that we can correctly generate subscriptions with two fields in each
// subscription.
BOOST_AUTO_TEST_CASE(TwoFieldsPerSubscriptionsWorks) {
  TestingFieldSet fs;
  istringstream fields_file(
      "fname EQFakeFactory Oliver Nick Mayank Ben\n"
      "lname EQFakeFactory Dain Hwang Varia Price\n"
      "state EQFakeFactory MA OR WA NY CO ME FL CA NJ DC\n"
      "city EQFakeFactory Eugene Cambridge Lincoln Oakridge\n");
  fs.AppendFromFile(&fields_file);
  
  LowMatchRatePubSubGen psg(&fs, 0, false);
  auto num_pred_gen = [](int num_flds_avail){
    BOOST_REQUIRE_EQUAL(num_flds_avail, 4);
    return 2;
  };
  psg.GenerateSubscriptions(9, num_pred_gen);

  // Make sure we generated the requested number of subscriptions.
  BOOST_CHECK_EQUAL(psg.GetAllSubscriptions()->size(), 9);

  // Here n = 4 and m = 2 so each subgroup should have (n - m + 1) = 3 members
  // in it. Since we asked for 9 total subscriptions we should have 3
  // completely full subsets.
  LowMatchRatePubSubGen::SubsetIterator i1, i2;
  psg.GetSubsetsGE(0, &i1, &i2);
  BOOST_CHECK_EQUAL(i2 - i1, 3);

  // Check the integrity of each generated subset.
  for (LowMatchRatePubSubGen::SubsetIterator i = i1; i != i2; ++i) {
    BOOST_CHECK_EQUAL(i->size(), 3);
    BOOST_CHECK(OverlappingFieldsSame(fs, *i));
    BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, *i));
    // Make sure all subscriptions have 2 predicates.
    for (const auto& sub : *i) {
      BOOST_CHECK_EQUAL(sub.NumPredicates(), 2);
    }
  }
  BOOST_CHECK(SubsetsIndependent(fs, *psg.GetAllSubsets()));
}

// A functor used as a generator for the number of predicates in each
// subscription. Returns 1, 2, 3 and then repeats.
class OneTwoThreeGen {
 public:
  OneTwoThreeGen() : num_(0) {
  }
  int operator()(int max_pred) {
    int to_return = num_ + 1;
    num_ = (num_ + 1) % 3;
    if (to_return > max_pred) {
      return max_pred;
    }
    return to_return;
  }

 private:
  int num_;
};

// Check that we can correctly generate subsets if the number of predicates in
// each subscription cycles through 1, 2, and then 3 predicates. The subsets
// generated should be as follows, where I'm using the notation (x)(y)..(z) to
// denote a subset with x predicates in the 1st subscription, y in the 2nd, etc.
//
// 1) (1)(2): The next value generated by OneTwoThreeGen would be 3 but that's
//    not possible so the next subscription should start with 3.
// 2) (3)(1): With m = 3 and 4 fields only 2 subscriptions are possible.
// 3) (2)(3)
// 4) (1)(2)
// 5) (3): At this point we've generated the requested 9 subsets so even though
//     we could add another subscription and maintain the perfectly compatible
//     property we don't.
//
// Note that we explicitly test the above but since subscription sizes are
// sorted the last one to come first. Also note that this test relies on the
// fact that subsets are sorted by size using a *stable* sort. That's not very
// robust but obviously makes testing much easier.
BOOST_AUTO_TEST_CASE(OneTwoThreePredicateSubscriptionsWork) {
  TestingFieldSet fs;
  istringstream fields_file(
      "fname EQFakeFactory Oliver Nick Mayank Ben Gourdy Alice\n"
      "lname EQFakeFactory Dain Hwang Varia Price Keegans McGee\n"
      "state EQFakeFactory MA OR WA NY CO ME FL CA NJ DC\n"
      "city EQFakeFactory Eugene Cambridge Lincoln Oakridge Kirkland NY\n");
  fs.AppendFromFile(&fields_file);
  
  LowMatchRatePubSubGen psg(&fs, 0, false);
  OneTwoThreeGen num_pred_gen;
  psg.GenerateSubscriptions(9, std::ref(num_pred_gen));

  // Make sure we generated the requested number of subscriptions.
  BOOST_CHECK_EQUAL(psg.GetAllSubscriptions()->size(), 9);

  const vector<LowMatchRatePubSubGen::PerfectSubset>* subsets =
      psg.GetAllSubsets();
  BOOST_REQUIRE_EQUAL(subsets->size(), 5);

  multiset<int> expected;
  assign::insert(expected)(1)(2);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(0), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(0)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(0)));

  expected.clear();
  assign::insert(expected)(3)(1);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(1), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(1)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(1)));

  expected.clear();
  assign::insert(expected)(2)(3);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(2), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(2)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(2)));

  expected.clear();
  assign::insert(expected)(1)(2);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(3), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(3)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(3)));

  expected.clear();
  assign::insert(expected)(3);
  // No need to check overlapping fields or that all subscriptions have unique
  // fields as here we're checking that there's only 1 subscription so the other
  // conditions are trivially true.
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(4), &expected));

  BOOST_CHECK(SubsetsIndependent(fs, *subsets));
}

// Sometimes a field can get "exhaused". For example, a field like "sex" that
// has just two values can only be used in 1 perfect subset as we have to
// reserve the other value so we can create publications that don't match
// anyting in the subset that used "sex". Here we generate some fields with just
// a few values so that they will get exhausted, but at different times, and
// then check that the subscriptions generated are still valid. All
// subscriptiosn should contain 3 predicates.
//
// The generated subsets should be as follows:
//
// 1) Initially there are 6 feilds avaiable so the 1st subscription should
//    contain 6 - 3 + 1 = 4 subscriptions.
// 2) The 1st subset will exhaust the sex field so there are now only 5 fields
//    available. Thus the next subset should contain 5 - 3 + 1 = 3
//    subscriptions.
// 3) group is now exhausted so the next should contain 2 subscriptions
// 4) type is now exhaused so this should contain only 1 subscription
// 5) This too should contain 1 subscription
BOOST_AUTO_TEST_CASE(ExhaustedFieldsWork) {
  TestingFieldSet fs;
  istringstream fields_file(
      "sex EQFakeFactory Male Female\n"
      "fname EQFakeFactory Oliver Nick Mayank Ben Gourdy Alice\n"
      "lname EQFakeFactory Dain Hwang Varia Price Keegans McGee\n"
      "group EQFakeFactory A B C\n"
      "city EQFakeFactory Eugene Cambridge Lincoln Oakridge Kirkland NY\n"
      "type EQFakeFactory W X Y Z\n");
  fs.AppendFromFile(&fields_file);

  LowMatchRatePubSubGen psg(&fs, 2, false);


  auto num_pred_gen = [](int num_flds_avail){
    BOOST_REQUIRE_GE(num_flds_avail, 3);
    return 3;
  };
  psg.GenerateSubscriptions(11, num_pred_gen);

  // Since, initially, there are 6 available fields the 1st subset should
  // contain 6 - 3 + 1 = 3 subscriptions with 3 predicates each.
  const vector<LowMatchRatePubSubGen::PerfectSubset>* subsets =
      psg.GetAllSubsets();
  BOOST_CHECK_EQUAL(psg.GetAllSubscriptions()->size(), 11);

  BOOST_REQUIRE_EQUAL(subsets->size(), 5);

  multiset<int> expected;
  assign::insert(expected)(3)(3)(3)(3);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(0), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(0)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(0)));

  expected.clear();
  assign::insert(expected)(3)(3)(3);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(1), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(1)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(1)));

  expected.clear();
  assign::insert(expected)(3)(3);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(2), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(2)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(2)));

  expected.clear();
  assign::insert(expected)(3);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(3), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(3)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(3)));

  expected.clear();
  assign::insert(expected)(3);
  BOOST_CHECK(NumberOfPredicatesMatches(fs, subsets->at(4), &expected));
  BOOST_CHECK(OverlappingFieldsSame(fs, subsets->at(4)));
  BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subsets->at(4)));

  // Now make sure that there's a value of sex, group, and type that was never
  // used.
  const set<string>* used_sex = psg.GetUsedValuesForField(0);
  BOOST_CHECK(used_sex->find("Male") == used_sex->end() ||
              used_sex->find("Female") == used_sex->end());

  
  const set<string>* used_group = psg.GetUsedValuesForField(3);
  BOOST_CHECK(used_group->find("A") == used_group->end() ||
              used_group->find("B") == used_group->end() ||
              used_group->find("C") == used_group->end());
  
  const set<string>* used_type = psg.GetUsedValuesForField(5);
  BOOST_CHECK(used_type->find("W") == used_type->end() ||
              used_type->find("X") == used_type->end() ||
              used_type->find("Y") == used_type->end() ||
              used_type->find("Z") == used_type->end());

  BOOST_CHECK(SubsetsIndependent(fs, *subsets));
}

// Generate random subscriptions with the number of predicates having a Poisson
// distribution. Try various means and seeds and ensure the generated subgroups
// are valid.
BOOST_AUTO_TEST_CASE(RandomPoissonSubscriptionsValid) {
  TestingFieldSet fs;
  istringstream fields_file(
      "sex EQFakeFactory Male Female\n"
      "state EQFakeFactory OR WA MA NY CO NC\n"
      "int1 IntegerField %d 1 5\n"
      "int2 IntegerField %d 1 100\n"
      "int2 IntegerField %d 200 5000\n"
      "int3 IntegerField %d 5 25\n"
      "int4 IntegerField %d 0 200\n"
      "int5 IntegerField %d 0 1000\n");
  fs.AppendFromFile(&fields_file);

  int seed = std::chrono::system_clock::to_time_t(
      std::chrono::system_clock::now());
  LOG(INFO) << "Seed for this test: " << seed;

  fs.SetSeed(seed);

  // Run one test for each of the following 
  vector<int> means = list_of(1)(2)(3)(5);
  for (int mean : means) {
    LOG(INFO) << "Testing with mean = " << mean;
    LowMatchRatePubSubGen psg(&fs, seed, false);

    const int kNumSubscriptions = 100;
    TruncatedPoissonNumGenerator num_pred_generator(mean, seed);
    psg.GenerateSubscriptions(kNumSubscriptions, std::ref(num_pred_generator));

    BOOST_CHECK_EQUAL(psg.GetAllSubscriptions()->size(), kNumSubscriptions);

    const vector<LowMatchRatePubSubGen::PerfectSubset>* subsets =
        psg.GetAllSubsets();
    BOOST_CHECK(SubsetsIndependent(fs, *subsets));

    for (const auto& subset : *subsets) {
      BOOST_CHECK(OverlappingFieldsSame(fs, subset));
      BOOST_CHECK(AllSubscriptionsHaveUniqueField(fs, subset));
    }
  }
}

typedef vector<EqualitySubscription> SubscriptionVector;

// pub is a CSV publication. This checks that it matches all of the
// subscriptions in match_subscriptions and only match_subscriptions.size()
// subscrptions in all_subscriptions (match_subscriptions is a subset of
// all_subscriptions).
boost::test_tools::predicate_result
PublicationMatchesOnly(
    const FieldSet& fs, char* pub,
    const SubscriptionVector& match_subscriptions,
    const SubscriptionVector& all_subscriptions) {
  string pub_str(pub);
  vector<string> pub_vals = Split(pub_str, ',');
  if (pub_vals.size() != fs.Size()) {
    boost::test_tools::predicate_result res(false);
    res.message() << "The publication contains "
        << pub_vals.size() << " values but there are "
        << fs.Size() << " fields.";
    return res;
  }

  // Ensure that it matches all the subscription in match_subscriptions
  for (const auto& subscription : match_subscriptions) {
    for (int pred_i = 0; pred_i < subscription.NumPredicates(); ++pred_i) {
      const EqualityCondition* cond = subscription.GetCondition(pred_i);
      if (pub_vals[cond->field()] != cond->value()) {
        boost::test_tools::predicate_result res(false);
        res.message() << "A publication with value " << pub_vals[cond->field()]
            << " will not match a subscription with value "
            << cond->value() << " on field " << fs.Get(cond->field())->name()
            << ". Publication:\n" << pub << "\nSubscription:\n";
        return res;
      }
    }
  }

  // And make sure it matches only match_subscriptions.size() subscriptions in
  // all_subscriptions.
  size_t matching_subs = 0;
  for (const auto& subscription : all_subscriptions) {
    bool matches = true;
    for (int pred_i = 0; pred_i < subscription.NumPredicates(); ++pred_i) {
      const EqualityCondition* cond = subscription.GetCondition(pred_i);
      if (pub_vals[cond->field()] != cond->value()) {
        matches = false;
        break;
      }
    }

    if (matches) ++matching_subs;
  }

  if (matching_subs != match_subscriptions.size()) {
    boost::test_tools::predicate_result res(false);
    res.message() << matching_subs << " subscriptions matched\n"
        << pub << " but only " << match_subscriptions.size()
        << " should have. Subscriptions:\n";
    AppendSubscriptionDefinitions(fs, all_subscriptions, &res);
    return res;
  }

  return true;
}

// Make sure we can generate publications.
BOOST_AUTO_TEST_CASE(PublicationsWork) {
  TestingFieldSet fs;
  istringstream fields_file(
      "sex EQFakeFactory Male Female\n"
      "state EQFakeFactory OR WA MA NY CO NC\n"
      "int1 IntegerField %d 1 5\n"
      "int2 IntegerField %d 1 100\n"
      "int2 IntegerField %d 200 5000\n"
      "int3 IntegerField %d 5 25\n"
      "int4 IntegerField %d 0 200\n"
      "int5 IntegerField %d 0 1000\n");
  fs.AppendFromFile(&fields_file);

  int seed = std::chrono::system_clock::to_time_t(
      std::chrono::system_clock::now());
  LOG(INFO) << "Seed for this test: " << seed;

  fs.SetSeed(seed);

  LowMatchRatePubSubGen psg(&fs, seed, false);

  const int kNumSubscriptions = 100;
  TruncatedPoissonNumGenerator num_pred_generator(3, seed);
  psg.GenerateSubscriptions(kNumSubscriptions, std::ref(num_pred_generator));

  size_t max_pub_len = psg.MaxPublicationSize();
  char pub[max_pub_len];

  vector<EqualitySubscription> matching_subs =
      psg.GetPublication(1, max_pub_len, pub);
  BOOST_CHECK(PublicationMatchesOnly(fs, pub, matching_subs,
                                     *psg.GetAllSubscriptions()));


  matching_subs =
      psg.GetPublication(2, max_pub_len, pub);
  // This could, in very rare circumstances, fail. That should only happen if
  // there is not perfect subset of size >= 2 and that should only happen if the
  // num_pred_generator returned all very large values.
  BOOST_REQUIRE_EQUAL(matching_subs.size(), 2);
  BOOST_CHECK(PublicationMatchesOnly(fs, pub, matching_subs,
                                     *psg.GetAllSubscriptions()));

  matching_subs =
      psg.GetPublication(3, max_pub_len, pub);
  // As above, this could fail in very rare circumstances.
  BOOST_REQUIRE_EQUAL(matching_subs.size(), 3);
  BOOST_CHECK(PublicationMatchesOnly(fs, pub, matching_subs,
                                     *psg.GetAllSubscriptions()));

}
