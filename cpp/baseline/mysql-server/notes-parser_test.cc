//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for NotesParser 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Oct 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE NotesParserTest
#include "common/test-init.h"

#include "notes-parser.h"

#include <boost/assign/list_inserter.hpp>
#include <set>
#include <string>

#include "common/knot.h"

using namespace std;

// Check that parsing works on normal data.
BOOST_AUTO_TEST_CASE(ParserWorks) {
  set<string> stopwords;
  NotesParser parser(stopwords);

  // This is the example from the test plan.
  Knot d1(new string(
          "this is word-like! Really."));

  set<string> words;
  parser.Parse(d1, &words);

  BOOST_CHECK_EQUAL(words.size(), 5);
  BOOST_CHECK(words.find("this") != words.end());
  BOOST_CHECK(words.find("is") != words.end());
  BOOST_CHECK(words.find("word") != words.end());
  BOOST_CHECK(words.find("like") != words.end());
  BOOST_CHECK(words.find("really") != words.end());

  Knot d2(new string(
          "  ;,More?WORDS   in this it's  ,.!"));
  words.clear();
  parser.Parse(d2, &words);

  BOOST_CHECK_EQUAL(words.size(), 5);
  BOOST_CHECK(words.find("more") != words.end());
  BOOST_CHECK(words.find("words") != words.end());
  BOOST_CHECK(words.find("in") != words.end());
  BOOST_CHECK(words.find("this") != words.end());
  BOOST_CHECK(words.find("it's") != words.end());

  Knot d3(new string("this is short"));
  words.clear();
  parser.Parse(d3, &words);

  BOOST_CHECK_EQUAL(words.size(), 3);
  BOOST_CHECK(words.find("this") != words.end());
  BOOST_CHECK(words.find("is") != words.end());
  BOOST_CHECK(words.find("short") != words.end());
}

BOOST_AUTO_TEST_CASE(EmptyNotesWorks) {
  set<string> stopwords;
  NotesParser parser(stopwords);
  Knot empty;
  set<string> words;

  parser.Parse(empty, &words);
  BOOST_CHECK_EQUAL(words.size(), 0);
}

BOOST_AUTO_TEST_CASE(AllDelimsWorks) {
  set<string> stopwords;
  NotesParser parser(stopwords);
  Knot all_delims(new string(" ,!?;--! "));
  set<string> words;

  parser.Parse(all_delims, &words);
  BOOST_CHECK_EQUAL(words.size(), 0);
}

BOOST_AUTO_TEST_CASE(SingleWordWorks) {
  set<string> stopwords;
  NotesParser parser(stopwords);
  Knot one_word(new string("hello"));
  set<string> words;

  parser.Parse(one_word, &words);
  BOOST_CHECK_EQUAL(words.size(), 1);
  BOOST_CHECK(words.find("hello") != words.end());
}

BOOST_AUTO_TEST_CASE(StopWordsWork) {
  set<string> stopwords;
  boost::assign::insert(stopwords)
      ("is")("and")("longer")("stop");
  NotesParser parser(stopwords);

  Knot data(new string(
          "This is? a series of words; and .?longer things stop!!"));

  set<string> words;
  parser.Parse(data, &words);
  BOOST_CHECK_EQUAL(words.size(), 6);
  BOOST_CHECK(words.find("this") != words.end());
  BOOST_CHECK(words.find("a") != words.end());
  BOOST_CHECK(words.find("series") != words.end());
  BOOST_CHECK(words.find("of") != words.end());
  BOOST_CHECK(words.find("words") != words.end());
  BOOST_CHECK(words.find("things") != words.end());

  BOOST_CHECK(words.find("is") == words.end());
  BOOST_CHECK(words.find("longer") == words.end());
  BOOST_CHECK(words.find("and") == words.end());
  BOOST_CHECK(words.find("stop") == words.end());
}

BOOST_AUTO_TEST_CASE(AllStopWords) {
  set<string> stopwords;
  boost::assign::insert(stopwords)
      ("is")("and")("it's")("stop");
  NotesParser parser(stopwords);

  Knot data(new string(
          "  ,is and it's ;!is and. and  .is stop!"));

  set<string> words;
  parser.Parse(data, &words);
  BOOST_CHECK_EQUAL(words.size(), 0);
}
