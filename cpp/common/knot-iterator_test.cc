//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for Knot::iterator. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 14 Aug 2012   omd            Original Version
//*****************************************************************

#include "knot.h"

#include <algorithm>
#include <boost/assign/list_of.hpp>
#include <cstring>

#define BOOST_TEST_MODULE KnotIteratorTest
#include "test-init.h"
#include "string-algo.h"

using namespace std;
using boost::assign::list_of;

BOOST_AUTO_TEST_CASE(ForwardIterationWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts to")(" tes")("t iteration.");
  
  Knot knot;
  vector<string>::const_iterator i;
  string complete_string;
  for (i = parts.begin(); i != parts.end(); ++i) {
    knot.Append(StrDup(i->c_str()), i->size());
    complete_string += *i;
  }

  string::const_iterator si;
  Knot::iterator ki;

  BOOST_CHECK_EQUAL(knot.Size(), complete_string.size());

  si = complete_string.begin();
  ki = knot.begin();

  while (si != complete_string.end() &&
         ki != knot.end()) {
    BOOST_CHECK_EQUAL(*ki, *si);
    ++ki;
    ++si;
  }
  BOOST_CHECK(ki == knot.end());
  BOOST_CHECK(si == complete_string.end());
}

BOOST_AUTO_TEST_CASE(BackwardIterationWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts to")(" tes")("t iteration.");
  
  Knot knot;
  vector<string>::const_iterator i;
  string complete_string;
  for (i = parts.begin(); i != parts.end(); ++i) {
    knot.Append(StrDup(i->c_str()), i->size());
    complete_string += *i;
  }

  string::const_iterator si;
  Knot::iterator ki;

  BOOST_CHECK_EQUAL(knot.Size(), complete_string.size());

  si = complete_string.end();
  ki = knot.end();

  --si;
  --ki;
  BOOST_CHECK_EQUAL(*ki, '.');
  BOOST_CHECK_EQUAL(*si, '.');

  while (true) {
    BOOST_CHECK_EQUAL(*ki, *si);
    if (si == complete_string.begin()) {
      BOOST_CHECK(ki == knot.begin());
      break;
    }
    if (ki == knot.begin()) {
      BOOST_CHECK(si == complete_string.begin());
      break;
    }
    --ki;
    --si;
  }
}

// Use some STL algorithms with Knot::iterator to make sure it really is an STL
// compatible iterator.
BOOST_AUTO_TEST_CASE(STLCompatible) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts to")(" tes")("t iteration.");
  
  Knot knot;
  vector<string>::const_iterator i;
  string complete_string;
  for (i = parts.begin(); i != parts.end(); ++i) {
    knot.Append(StrDup(i->c_str()), i->size());
    complete_string += *i;
  }

  string string_from_iter(knot.begin(), knot.end());
  BOOST_CHECK_EQUAL(string_from_iter, complete_string);

  Knot::iterator ki = find(knot.begin(), knot.end(), ' ');
  BOOST_CHECK_EQUAL(*ki, ' ');
  ++ki;
  BOOST_CHECK_EQUAL(*ki, 'i');

  int num_i = count(knot.begin(), knot.end(), 'i');
  BOOST_CHECK_EQUAL(num_i, 6);
}

BOOST_AUTO_TEST_CASE(OperatorMinusWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts to")(" tes")("t iteration.");
  
  Knot knot;
  for (vector<string>::const_iterator i = parts.begin();
       i != parts.end(); ++i) {
    knot.Append(StrDup(i->c_str()), i->size());
  }

  // i1 starts at the beginning of the knot and runs to the end
  Knot::iterator i1 = knot.begin();
  // This keeps track of the index of the character pointed to by i1
  int i1_position = 0;
  // i2 starts at i1 and goes to the end of the knot
  Knot::iterator i2 = i1;
  // Keeps track of the index of the character pointed to by i2
  int i2_position = 0;
  while (i1 != knot.end()) {
    i2 = i1;
    i2_position = i1_position;
    while (i2 != knot.end()) {
      // operator- should return the difference between the characters pointed
      // to by i2 and i1.
      BOOST_CHECK_EQUAL(i2 - i1, i2_position - i1_position);
      ++i2;
      ++i2_position;
    }
    ++i1;
    ++i1_position;
  }
}

// Similar to the above, but we check that operator- works correctly if one or
// both of the iterators == end().
BOOST_AUTO_TEST_CASE(OperatorMinusWithEndWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts to")(" tes")("t iteration.");
  
  Knot knot;
  for (vector<string>::const_iterator i = parts.begin();
       i != parts.end(); ++i) {
    knot.Append(StrDup(i->c_str()), i->size());
  }

  Knot::iterator end_it = knot.end();

  // it_position == the index of the character to which it points.
  int it_position = 0;
  Knot::iterator it;
  for (it = knot.begin(); it != knot.end(); ++it) {
    BOOST_CHECK_EQUAL(end_it - it, knot.Size() - it_position); 
    ++it_position;
  }

  // The difference between two end iterators should be 0.
  BOOST_CHECK(it == knot.end());
  BOOST_CHECK_EQUAL(end_it - it, 0);

}
