//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for ToplologicalIterator 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 May 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE TopologicalIteratorTest

#include "topological-iterator.h"

#include <algorithm>
#include <boost/random.hpp>
#include <ctime>
#include <iostream>
#include <vector>
#include <set>

#include "test-init.h"

// Create a directed graph that has only a single valid generation ordering and
// make sure that is the order that is, in fact, generated.
BOOST_AUTO_TEST_CASE(CheckBasic) {
  TopologicalIterator<char> topo;
  topo.Add('A');
  topo.Add('B');
  topo.Add('C');
  topo.Add('D');
  topo.Add('E');
  
  topo.OrderConstraint('C', 'B');
  topo.OrderConstraint('C', 'D');
  topo.OrderConstraint('C', 'E');
  topo.OrderConstraint('B', 'A');
  topo.OrderConstraint('B', 'D');
  topo.OrderConstraint('D', 'E');
  topo.OrderConstraint('E', 'A');

  BOOST_REQUIRE(topo.HasNext());
  BOOST_CHECK_EQUAL(topo.Next(), 'C');

  BOOST_REQUIRE(topo.HasNext());
  BOOST_CHECK_EQUAL(topo.Next(), 'B');
  
  BOOST_REQUIRE(topo.HasNext());
  BOOST_CHECK_EQUAL(topo.Next(), 'D');
  
  BOOST_REQUIRE(topo.HasNext());
  BOOST_CHECK_EQUAL(topo.Next(), 'E');
  
  BOOST_REQUIRE(topo.HasNext());
  BOOST_CHECK_EQUAL(topo.Next(), 'A');

  BOOST_CHECK_EQUAL(topo.HasNext(), false);
}

// Run several iterations of a test where we generate a random graph and then
// ensure that the iterator generates items in a legal order.
BOOST_AUTO_TEST_CASE(CheckRandom) {
  // Set up boost::random to generate true/false values with 0.5 probability.
  boost::mt19937 rng;
  boost::bernoulli_distribution<> bernoulli(0.5);
  boost::variate_generator<boost::mt19937&, boost::bernoulli_distribution<> >
      rand_connect(rng, bernoulli);

  // Generate NUM_TRIALS random graphs and make sure they're valid.
  const int NUM_TRIALS = 50;
  // Set and print out the random seed. That way if this crashes we'll be able
  // to manually set the seed to reproduce.
  unsigned int seed = (static_cast<unsigned int>(std::time(0)));
  std::cout << "Seed for CheckRandom: " << seed << std::endl;
  rng.seed(seed);

  for (int t = 0; t < NUM_TRIALS; ++t) {
    TopologicalIterator<char> topo;

    // 20 Characters 'A' - 'U'
    std::vector<char> items;
    for (char item = 'A'; item < 'U'; ++item) {
      items.push_back(item);
      topo.Add(item);
    }

    // Now shuffle them so we can generate a random acyclic graph. We'll connect
    // the item at the front of the list, randomly, to some of the items that
    // come later, but never vice-versa. That way we always have a valid graph
    // and it never has cycles.
    boost::uniform_int<> uniform_dist;
    boost::variate_generator<boost::mt19937&, boost::uniform_int<> >
        shuffle_gen(rng, uniform_dist);
    std::random_shuffle(items.begin(), items.end(), shuffle_gen);

    std::vector<char>::iterator i, j;
    // Keep track of what depends on what.
    std::map<char, std::set<char> > must_come_before;
    for (i = items.begin(); i != items.end(); ++i) {
      for (j = i + 1; j != items.end(); ++j) {
        if (rand_connect()) {
          topo.OrderConstraint(*i, *j);
          must_come_before[*j].insert(*i);
        }
      }
    }

    // Now we've got a random graph and must_come_before[i] tells us all the
    // things that must be generated before i. So we use the
    // ToplologicalIterator and make sure things are genereated in a way that
    // doesn't violate that constraint.
    while (topo.HasNext()) {
      char value = topo.Next();
      // There shouldn't be anything left that had to come 1st.
      BOOST_CHECK_EQUAL(must_come_before[value].size(), 0);
      // Iterate through all the other items and remove value from the list of
      // things we're waiting on.
      std::map<char, std::set<char> >::iterator other_items_it;
      for (other_items_it = must_come_before.begin();
           other_items_it != must_come_before.end();
           ++other_items_it) {
        other_items_it->second.erase(value);
      }
    }
  }  
}
