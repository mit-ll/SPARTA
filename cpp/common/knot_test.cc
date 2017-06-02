//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for Knot class.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 06 Aug 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE KnotTest

#include "test-init.h"

#include "knot.h"
#include "string-algo.h"
#include "util.h"

#include <boost/assign/list_of.hpp>
#include <cstring>
#include <fcntl.h>
#include <string>

using namespace std;
using boost::assign::list_of;

// Given a vector<string> construct a Knot by repeatedly appending the strings
// in the vector to out_knot.
void FillKnot(const vector<string>& parts, Knot* out_knot) {
  vector<string>::const_iterator i;
  for (i = parts.begin(); i != parts.end(); ++i) {
    char* data = new char[i->size()];
    memcpy(data, i->c_str(), i->size());
    out_knot->Append(data, i->size());
  }
}

// Given a vector<string> return a new string that is the concatenation of all
// the string in the vector.
string ConcatenateStrings(const vector<string>& parts) {
  string result;
  vector<string>::const_iterator i;
  for (i = parts.begin(); i != parts.end(); ++i) {
    result += *i;
  }
  return result;
}

// Simple test that we can construct a knot and convert it to a string.
BOOST_AUTO_TEST_CASE(ConstructAndToStringWorks) {
  const char kTestString[] = "This is the test string.";
  Knot k(StrDup(kTestString), strlen(kTestString));
  string result;
  k.ToString(&result);
  BOOST_CHECK_EQUAL(result, kTestString);
}

// Try appending several strings and make sure we get the correct results.
BOOST_AUTO_TEST_CASE(AppendWorks) {
  const char kString1[] = "String 1 ";
  const char kString2[] = "String 2 ";
  const char kString3[] = "String 3";

  Knot k(StrDup(kString1), strlen(kString1));
  BOOST_CHECK_EQUAL(k.ToString(), kString1);

  k.Append(StrDup(kString2), strlen(kString2));
  BOOST_CHECK_EQUAL(k.ToString(), string(kString1) + kString2);

  k.Append(StrDup(kString3), strlen(kString3));
  BOOST_CHECK_EQUAL(k.ToString(), string(kString1) + kString2 + kString3);
}

BOOST_AUTO_TEST_CASE(AppendOwnedWorks) {
  const char kString1[] = "String 1 ";
  const char kString2[] = "String 2 ";
  const char kString3[] = "String 3";

  Knot k;
  k.AppendOwned(kString1, strlen(kString1));
  BOOST_CHECK_EQUAL(k.ToString(), kString1);

  k.AppendOwned(kString2, strlen(kString2));
  BOOST_CHECK_EQUAL(k.ToString(), string(kString1) + kString2);

  k.AppendOwned(kString3, strlen(kString3));
  BOOST_CHECK_EQUAL(k.ToString(), string(kString1) + kString2 + kString3);
}

// Try the Find method.
BOOST_AUTO_TEST_CASE(FindWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts~to")(" tes")("t find!");
  Knot knot;
  FillKnot(parts, &knot);

  Knot::iterator it;
  it = knot.Find('~');
  BOOST_CHECK_EQUAL(*it, '~');
  ++it;
  BOOST_CHECK_EQUAL(*it, 't');

  it = knot.Find(' ');
  BOOST_CHECK_EQUAL(*it, ' ');
  ++it;
  BOOST_CHECK_EQUAL(*it, 'i');

  it = knot.Find('!');
  BOOST_CHECK_EQUAL(*it, '!');
  ++it;
  BOOST_CHECK(it == knot.end());
}

BOOST_AUTO_TEST_CASE(LatCharIterWorks) {
  vector<string> parts = list_of("part 1")(" part 2")("final!");
  Knot knot;
  FillKnot(parts, &knot);

  Knot::iterator i = knot.LastCharIter();
  BOOST_CHECK_EQUAL(*i, '!');
  ++i;
  BOOST_CHECK(i == knot.end());

  // Try the edge case with a single character knot.
  Knot knot2;
  knot2.Append(StrDup("A"), 1);
  Knot::iterator i2 = knot2.LastCharIter();
  BOOST_CHECK_EQUAL(*i2, 'A');
  BOOST_CHECK(i2 == knot2.begin());
  ++i2;
  BOOST_CHECK(i2 == knot2.end());

}

// Try the find with offset method.
BOOST_AUTO_TEST_CASE(FindWithOffsetWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts~to")(" tes")("t find!");
  Knot knot;
  FillKnot(parts, &knot);
  string complete_string = ConcatenateStrings(parts);

  // Basically do a split on the knot and make sure we get the same thing as
  // we'd get if we split the full string.
  vector<string> knot_words;
  Knot::iterator start_it = knot.begin();
  while (true) {
    Knot::iterator space_it = knot.Find(' ', start_it);
    if (space_it == knot.end()) {
      knot_words.push_back(string(start_it, knot.end()));
      break;
    } else {
      knot_words.push_back(string(start_it, space_it));
      start_it = space_it;
      ++start_it;
    }
  }

  vector<string> complete_words = Split(complete_string, ' ');

  BOOST_REQUIRE_EQUAL(knot_words.size(), complete_words.size());
  for (size_t i = 0; i < knot_words.size(); ++i) {
    BOOST_CHECK_EQUAL(knot_words[i], complete_words[i]);
  }
}

// Get an iterator into a Knot, then append to the knot, then call Find using
// the old iterator as a start offset.
BOOST_AUTO_TEST_CASE(FindWithOffsetAfterAppendWorks) {
  const char kString1[] = "String1";
  const char kString2[] = "String2";
  const char kString3[] = "String3 and more";

  Knot k(StrDup(kString1), strlen(kString1));
  Knot::iterator found_it = k.Find(' ');
  BOOST_CHECK(found_it == k.end());

  Knot::iterator start_it = k.LastCharIter();
  k.Append(StrDup(kString2), strlen(kString2));
  ++start_it;
  BOOST_REQUIRE(start_it != k.end());
  found_it = k.Find(' ', start_it);
  BOOST_CHECK(found_it == k.end());

  start_it = k.LastCharIter();
  k.Append(StrDup(kString3), strlen(kString3));
  ++start_it;
  BOOST_REQUIRE(start_it != k.end());
  found_it = k.Find(' ', start_it);
  BOOST_REQUIRE(found_it != k.end());

  BOOST_CHECK_EQUAL(string(start_it, found_it), "String3");

  start_it = found_it;
  ++start_it;
  found_it = k.Find(' ', start_it);
  BOOST_REQUIRE(found_it != k.end());
  BOOST_CHECK_EQUAL(string(start_it, found_it), "and");
}

BOOST_AUTO_TEST_CASE(IteratorForCharWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts~to")(" tes")("t find!");
  Knot knot;
  FillKnot(parts, &knot);
  string complete_string = ConcatenateStrings(parts);

  BOOST_REQUIRE_EQUAL(knot.Size(), complete_string.size());
  for (size_t i = 0; i < knot.Size(); ++i) {
    Knot::iterator knot_it = knot.IteratorForChar(i);
    BOOST_CHECK_EQUAL(*knot_it, complete_string[i]);
  }
}

BOOST_AUTO_TEST_CASE(RightSubKnotWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts~to")(" tes")("t find!");
  Knot knot;
  FillKnot(parts, &knot);
  string complete_string = ConcatenateStrings(parts);

  BOOST_REQUIRE_EQUAL(knot.Size(), complete_string.size());
  for (size_t i = 0; i < knot.Size() - 1; ++i) {
    string sub_str = complete_string.substr(i, string::npos);
    Knot sub_knot = knot.SubKnot(knot.IteratorForChar(i), knot.end());
    BOOST_CHECK_EQUAL(sub_knot.Size(), sub_str.size());
    BOOST_CHECK_EQUAL(sub_knot.ToString(), sub_str);
  }
}

BOOST_AUTO_TEST_CASE(LeftSubKnotWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts~to")(" tes")("t find!");
  Knot knot;
  FillKnot(parts, &knot);
  string complete_string = ConcatenateStrings(parts);

  BOOST_REQUIRE_EQUAL(knot.Size(), complete_string.size());
  for (size_t length = 1; length < knot.Size(); ++length) {
    string sub_str = complete_string.substr(0, length);
    Knot sub_knot = knot.SubKnot(knot.begin(), knot.IteratorForChar(length));
    BOOST_CHECK_EQUAL(sub_knot.Size(), sub_str.size());
    BOOST_CHECK_EQUAL(sub_knot.ToString(), sub_str);
  }
}

// Take subknots of subknots and make sure that works.
BOOST_AUTO_TEST_CASE(RepeatedRightSubKnotWorks) {
  vector<string> p1 = list_of("First part. ")("Second part. ")
      ("Third part.");
  Knot k1;
  FillKnot(p1, &k1);
  string cs1 = ConcatenateStrings(p1);

  Knot k1s1 = k1.SubKnot(k1.IteratorForChar(1), k1.end());
  BOOST_CHECK_EQUAL(k1s1.ToString(), cs1.substr(1, string::npos));

  Knot k1s2 = k1s1.SubKnot(k1s1.IteratorForChar(1), k1s1.end());
  BOOST_CHECK_EQUAL(k1s2.ToString(), cs1.substr(2, string::npos));

  Knot k1s3 = k1s2.SubKnot(k1s2.IteratorForChar(15), k1s2.end());
  BOOST_CHECK_EQUAL(k1s3.ToString(), cs1.substr(17, string::npos));
  // And make sure the original knots are all still valid.
  BOOST_CHECK_EQUAL(k1s2.ToString(), cs1.substr(2, string::npos));
  BOOST_CHECK_EQUAL(k1s1.ToString(), cs1.substr(1, string::npos));
  BOOST_CHECK_EQUAL(k1.ToString(), cs1);

  // Same thing but now each subknot removes a whole strand or more.
  vector<string> p2 = list_of("s1")("s2")("s3")("s4");
  Knot k2;
  FillKnot(p2, &k2);
  string cs2 = ConcatenateStrings(p2);

  Knot k2s1 = k2.SubKnot(k2.IteratorForChar(2), k2.end());
  BOOST_CHECK_EQUAL(k2s1.ToString(), cs2.substr(2, string::npos));

  Knot k2s2 = k2s1.SubKnot(k2s1.IteratorForChar(4), k2s1.end());
  BOOST_CHECK_EQUAL(k2s2.ToString(), cs2.substr(6, string::npos));
  // And make sure the older knots are still valid.
  BOOST_CHECK_EQUAL(k2s1.ToString(), cs2.substr(2, string::npos));
  BOOST_CHECK_EQUAL(k2, cs2);
}

// Like the above but take right-hand subknots instead.
BOOST_AUTO_TEST_CASE(RepeatedLeftSubKnotWorks) {
  vector<string> parts = list_of("First part. ")("Second part. ")
      ("Third part.");
  Knot k;
  FillKnot(parts, &k);
  string cs1 = ConcatenateStrings(parts);

  Knot ks1 = k.SubKnot(k.begin(), k.IteratorForChar(20));
  BOOST_CHECK_EQUAL(ks1.ToString(), cs1.substr(0, 20));

  Knot ks2 = ks1.SubKnot(ks1.begin(), ks1.IteratorForChar(18));
  BOOST_CHECK_EQUAL(ks2.ToString(), cs1.substr(0, 18));

  Knot ks3 = ks2.SubKnot(ks2.begin(), ks2.IteratorForChar(5));
  BOOST_CHECK_EQUAL(ks3.ToString(), cs1.substr(0, 5));
  // And make sure the earlier Knots are all still valid too.
  BOOST_CHECK_EQUAL(ks2.ToString(), cs1.substr(0, 18));
  BOOST_CHECK_EQUAL(ks1.ToString(), cs1.substr(0, 20));
  BOOST_CHECK_EQUAL(k.ToString(), cs1);

}

BOOST_AUTO_TEST_CASE(LeftEraseWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts~to")(" tes")("t find!");
  string complete_string = ConcatenateStrings(parts);

  for (size_t length = 1; length < complete_string.size(); ++length) {
    Knot knot;
    FillKnot(parts, &knot);
    BOOST_REQUIRE_EQUAL(knot.Size(), complete_string.size());

    string erased_str = complete_string.substr(length, string::npos);
    knot.LeftErase(knot.IteratorForChar(length));
    BOOST_CHECK_EQUAL(knot.Size(), erased_str.size());
    BOOST_CHECK_EQUAL(knot.ToString(), erased_str);
  }
}

BOOST_AUTO_TEST_CASE(RepeatedLeftEraseWorks) {
  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test")
      ("with")(" lots")("of p")("arts~to")(" tes")("t find!");
  string complete_string = ConcatenateStrings(parts);
  Knot knot;
  FillKnot(parts, &knot);

  knot.LeftErase(knot.IteratorForChar(5));
  BOOST_CHECK_EQUAL(knot.ToString(), complete_string.substr(5, string::npos));

  knot.LeftErase(knot.IteratorForChar(5));
  BOOST_CHECK_EQUAL(knot.ToString(), complete_string.substr(10, string::npos));

  knot.LeftErase(knot.IteratorForChar(15));
  BOOST_CHECK_EQUAL(knot.ToString(), complete_string.substr(25, string::npos));
}

BOOST_AUTO_TEST_CASE(SplitWorks) {
  vector<string> parts = list_of("p1 ")("p2 ")("p 3 ")
      ("and a long strand with lots of characters")
      (" short")(" final.");
  string complete_string = ConcatenateStrings(parts);

  for (size_t i = 1; i < complete_string.size(); ++i) {
    Knot knot;
    FillKnot(parts, &knot);
    BOOST_REQUIRE_EQUAL(knot.Size(), complete_string.size());

    string left_str = complete_string.substr(0, i);
    string right_str = complete_string.substr(i, string::npos);
    Knot left_knot = knot.Split(knot.IteratorForChar(i));

    BOOST_CHECK_EQUAL(left_knot.Size(), left_str.size());
    BOOST_CHECK_EQUAL(left_knot.ToString(), left_str);

    BOOST_CHECK_EQUAL(knot.Size(), right_str.size());
    BOOST_CHECK_EQUAL(knot.ToString(), right_str);
  }
}

// Check that the StartsWith(const char*, int) method works.
BOOST_AUTO_TEST_CASE(StartsWithCharLengthWorks) {
  vector<string> parts = list_of("One long string")(" in two parts")
      (" or maybe three");
  Knot knot;
  FillKnot(parts, &knot);

  const char kTest1[] = "One lo";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest1, strlen(kTest1)), true);

  const char kTest2[] = "One-lo";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest2, strlen(kTest2)), false);

  const char kTest3[] = "O";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest3, 1), true);

  const char kTest4[] = "One long string";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest4, strlen(kTest4)), true);

  const char kTest5[] = "One long string ";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest5, strlen(kTest5)), true);

  const char kTest6[] = "One long string in two pa";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest6, strlen(kTest6)), true);

  const char kTest7[] = "One long string in two parts";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest7, strlen(kTest7)), true);

  const char kTest8[] = "One long string in two parts or maybe";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest8, strlen(kTest8)), true);

  const char kTest9[] = "One long string in two parts or maybe three";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest9, strlen(kTest9)), true);

  const char kTest10[] = "One long strinA";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest10, strlen(kTest10)), false);

  const char kTest11[] = "One ling string ";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest11, strlen(kTest11)), false);

  const char kTest12[] = "Xne long string in two pa";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest12, strlen(kTest12)), false);

  const char kTest13[] = "One long string in two partt";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest13, strlen(kTest13)), false);

  const char kTest14[] = "One long string in two parts or maybe thre4";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest14, strlen(kTest14)), false);

  // This one is 1 character too long so it should fail.
  const char kTest15[] = "One long string in two parts or maybe three ";
  BOOST_CHECK_EQUAL(knot.StartsWith(kTest15, strlen(kTest15)), false);
}

// Small test to make sure the string version works. We can make this small
// since the string version just dispatches to the char* version so we're
// really only checking edge cases.
BOOST_AUTO_TEST_CASE(StartsWithStringWorks) {
  vector<string> parts = list_of("s1")("s2")("s3");
  Knot knot;
  FillKnot(parts, &knot);

  BOOST_CHECK_EQUAL(knot.StartsWith(string("s1")), true);
  BOOST_CHECK_EQUAL(knot.StartsWith(string("s")), true);
  BOOST_CHECK_EQUAL(knot.StartsWith(string("x")), false);
  BOOST_CHECK_EQUAL(knot.StartsWith(string("s1s2s")), true);
  BOOST_CHECK_EQUAL(knot.StartsWith(string("s1s2x")), false);
  BOOST_CHECK_EQUAL(knot.StartsWith(string("s1s2s3")), true);
  BOOST_CHECK_EQUAL(knot.StartsWith(string("s1s2s4")), false);
  BOOST_CHECK_EQUAL(knot.StartsWith(string("s1s2s3 ")), false);
}

BOOST_AUTO_TEST_CASE(OperatorEqualityWorks) {
  Knot k1;
  const char kString1[] = "String 1 is long";
  k1.Append(StrDup(kString1), strlen(kString1));
  BOOST_CHECK(k1 == string(kString1));
  BOOST_CHECK(! (k1 == string("String 1 is lon")));
  BOOST_CHECK(! (k1 == string("String 1 is longg")));
  BOOST_CHECK(! (k1 == string("String 1 is lonn")));
  BOOST_CHECK(! (k1 == string("String 1 it long")));

  Knot k2;
  vector<string> parts = list_of("A mult")("i part")(" string");
  FillKnot(parts, &k2);
  BOOST_CHECK(k2 == string("A multi part string"));
  BOOST_CHECK(! (k2 == string("A multi part strin")));
  BOOST_CHECK(! (k2 == string("A multi part stringg")));
  BOOST_CHECK(! (k2 == string("A Multi part string")));
}


BOOST_AUTO_TEST_CASE(ClearWorks) {
  vector<string> parts = list_of("s1")("s2")("s3");
  Knot k1;
  FillKnot(parts, &k1);

  BOOST_CHECK_EQUAL(k1.Size(), 6);
  k1.Clear();
  BOOST_CHECK_EQUAL(k1.Size(), 0);

  vector<string> parts2 = list_of("sec")("ond k")("not");
  FillKnot(parts2, &k1);
  BOOST_CHECK_EQUAL(k1.Size(), 11);
  BOOST_CHECK(k1.Equal("second knot", 11));

  // Make sure calling clear doesn't invalidate other knots.
  Knot k2 = k1;
  BOOST_CHECK_EQUAL(k1.ToString(), "second knot");
  BOOST_CHECK_EQUAL(k2.ToString(), "second knot");

  k1.Clear();
  BOOST_CHECK_EQUAL(k1.Size(), 0);
  BOOST_CHECK_EQUAL(k2.ToString(), "second knot");
}

BOOST_AUTO_TEST_CASE(KnotAppendWorks) {
  vector<string> parts1 = list_of("This ")("is")(" pa")("rt 1.");
  Knot k1;
  FillKnot(parts1, &k1);

  vector<string> parts2 = list_of("Part")(" 2 here.");
  auto_ptr<Knot> k2(new Knot);
  FillKnot(parts2, k2.get());

  BOOST_CHECK_EQUAL(k1.ToString(), "This is part 1.");
  BOOST_CHECK_EQUAL(k2->ToString(), "Part 2 here.");

  k1.Append(*k2);
  BOOST_CHECK_EQUAL(k1.ToString(), "This is part 1.Part 2 here.");
  BOOST_CHECK_EQUAL(k2->ToString(), "Part 2 here.");

  // Free k2 and make sure k1 is still valid.
  k2.reset();
  BOOST_CHECK_EQUAL(k1.ToString(), "This is part 1.Part 2 here.");
}

BOOST_AUTO_TEST_CASE(OutputOperatorWorks) {
  vector<string> parts = list_of("A mult")("i part")(" string");
  Knot knot;
  FillKnot(parts, &knot);

  ostringstream output_stream;
  output_stream << knot;

  BOOST_CHECK_EQUAL(output_stream.str(), "A multi part string");
}

// Check that I can append to a Knot that has had LeftErase called on it.
BOOST_AUTO_TEST_CASE(AppendAfterLeftErase) {
  Knot knot;
  knot.Append(new string("Long part 1"));
  BOOST_CHECK_EQUAL(knot.ToString(), "Long part 1");

  knot.LeftErase(knot.IteratorForChar(5));
  BOOST_CHECK_EQUAL(knot.ToString(), "part 1");
  knot.Append(new string(" part 2"));
  BOOST_CHECK_EQUAL(knot.ToString(), "part 1 part 2");

  knot.LeftErase(knot.IteratorForChar(7));
  BOOST_CHECK_EQUAL(knot.ToString(), "part 2");

  knot.Append(new string(" part 3"));
  BOOST_CHECK_EQUAL(knot.ToString(), "part 2 part 3");
}

// Take a knot, erase part of it to the left, then take a sub-knot of the left
// part of  what remains. Do this in multiple combinations and make sure we get
// the right results.
BOOST_AUTO_TEST_CASE(LeftSubKnotAfterLeftErase) {
  vector<string> parts = list_of("Part 1 ")("Part 2")(" 3 ")
      ("Part 4 is longer")(" p5");
  string full_str = ConcatenateStrings(parts);

  // Do left erase for all possible characters and then follow that by Appending
  // an additional string.
  for (size_t i = 1; i < full_str.size() - 2; ++i) {
    Knot knot;
    FillKnot(parts, &knot);
    knot.LeftErase(knot.IteratorForChar(i));
    string after_erase = full_str.substr(i, string::npos);

    BOOST_REQUIRE_EQUAL(knot.ToString(), after_erase);
    for (size_t j = 1; j < after_erase.size(); ++j) {
      Knot subknot = knot.SubKnot(knot.begin(), knot.IteratorForChar(j));
      string sub_str = after_erase.substr(0, j);

      BOOST_CHECK_MESSAGE(subknot.ToString() == sub_str,
                          "'" << subknot.ToString() << "' != '" << sub_str
                          << "'. After left erase the string was: '"
                          << after_erase << "'");
    }
  }
}

// Make sure copy-on-write semantics work as expected.
BOOST_AUTO_TEST_CASE(CopyOnWriteWorks) {
  vector<string> parts = list_of("This is")(" the")(" base st")("ring.");
  Knot base;
  FillKnot(parts, &base);

  Knot equal_assign;
  Knot copy_construct(base);
  copy_construct.Append(new string(" Copy Construct!"));
  equal_assign = base;
  equal_assign.Append(new string(" Equal Assign!"));

  BOOST_CHECK_EQUAL(base.ToString(), "This is the base string.");
  BOOST_CHECK_EQUAL(equal_assign.ToString(),
                    "This is the base string. Equal Assign!");
  BOOST_CHECK_EQUAL(copy_construct.ToString(),
                    "This is the base string. Copy Construct!");
}

// Make sure WriteToFileDescriptor works, even if multiple calls are required to
// keep from blocking.
BOOST_AUTO_TEST_CASE(WriteToFileDescriptorWorks) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  // Put the write end in non-blocking mode.
  int cur_flags = fcntl(write_end_fd, F_GETFL);
  fcntl(write_end_fd, F_SETFL, cur_flags | O_NONBLOCK);

  FileHandleIStream pipe_read_stream(read_end_fd);

  // First check that a small write, which should complete in a single write()
  // call, works.
  Knot k1;
  k1.Append(new string("This is not "));
  k1.Append(new string("a lot "));
  k1.Append(new string("of data."));

  Knot::iterator write_it = k1.WriteToFileDescriptor(write_end_fd);
  BOOST_REQUIRE_MESSAGE(write_it == k1.end(),
                        "Either all the data could not be written "
                        "to the pipe, or there's a bug.");

  const int kBufferSize = 1 << 20; // 1 MB
  char read_buffer[kBufferSize];
  int bytes_read = pipe_read_stream.readsome(read_buffer, kBufferSize);
  BOOST_CHECK_EQUAL(string(read_buffer, bytes_read),
                    "This is not a lot of data.");

  Knot k2;
  // Here we're going to build a really big knot that we think won't fit in the
  // pipe buffer so we can test WriteToFileDescriptor really doesn't block and
  // that the iterator version of things can write out the remainder of the
  // string.
  string all_data;
  const char* kStringPiece = "This is just a part of what will be a very "
      "long string. It will be repeated mutliple times. ";
  const int kNumStringPieceRepeats = 1000;
  for (int i = 0; i < kNumStringPieceRepeats; ++i) {
    k2.Append(StrDup(kStringPiece), strlen(kStringPiece));
    all_data += kStringPiece;
  }

  write_it = k2.WriteToFileDescriptor(write_end_fd);
  BOOST_REQUIRE_MESSAGE(write_it != k2.end(),
                        "This test relies on us building a string that's too "
                        "big to be written all at once, but it wasn't big "
                        "enough. There's nothing wrong with Knot, but the "
                        "test string needs to be longer.");

  string all_read;
  while (write_it != k2.end()) {
    // Read as much data as we can from the pipe
    do {
      bytes_read = pipe_read_stream.readsome(read_buffer, kBufferSize);
      all_read += string(read_buffer, bytes_read);
    } while (bytes_read > 0);
    write_it = k2.WriteToFileDescriptor(write_end_fd, write_it);
  }
  // Read all the remaining data from the pipe.
  do {
    bytes_read = pipe_read_stream.readsome(read_buffer, kBufferSize);
    all_read += string(read_buffer, bytes_read);
  } while (bytes_read > 0);

  BOOST_CHECK_EQUAL(all_read.size(), all_data.size());
  BOOST_CHECK_EQUAL(all_read, all_data);
}

// Check that the version of WriteToFileDescriptor that takes an iterator works.
BOOST_AUTO_TEST_CASE(WriteToFileDescriptorFromIteratorWorks) {
  int pipe_descriptors[2];
  int ret = pipe(pipe_descriptors);
  BOOST_REQUIRE_EQUAL(ret, 0);

  // The constants 0 and 1 here are as per the pipe() call.
  int read_end_fd = pipe_descriptors[0];
  int write_end_fd = pipe_descriptors[1];

  // Put the write end in non-blocking mode.
  int cur_flags = fcntl(write_end_fd, F_GETFL);
  fcntl(write_end_fd, F_SETFL, cur_flags | O_NONBLOCK);

  FileHandleIStream pipe_read_stream(read_end_fd);

  // First check that a small write, which should complete in a single write()
  // call, works.
  Knot knot;
  knot.Append(new string("This is not "));
  knot.Append(new string("a lot "));
  knot.Append(new string("of data.\n"));

  // This is the contents of the Knot without the terminating "\n" as that won't
  // be returned by getline below.
  string base_str = "This is not a lot of data.";
  for (size_t i = 0; i < base_str.size(); ++i) {
    Knot::iterator it = knot.IteratorForChar(i);
    BOOST_CHECK_EQUAL(*it, base_str[i]);
    Knot::iterator return_it = knot.WriteToFileDescriptor(write_end_fd, it);

    BOOST_REQUIRE_MESSAGE(return_it == knot.end(),
                          "All the data was not written!");

    string read_str;
    getline(pipe_read_stream, read_str);
    BOOST_CHECK_EQUAL(read_str, base_str.substr(i));
  }
}

// Perform pretty much all the operations supported by Knot in pretty much every
// possible way and make sure we get the same results as we'd get if we
// performed thos operations on a std::string.
BOOST_AUTO_TEST_CASE(StressTest) {
  vector<string> parts = list_of("A kno")("t wit")("h many, ")
      ("many part")("s")("both long and")(" ")("short.")("This should be ")
      ("a ve")("ry")(" robust test!!!");

  // We will preform the following sequence of operations to both the Knot and a
  // string and make sure the results are identical:
  //
  // 1) Append some, but not all, of the strands in parts.
  // 2) Take all possible sub-knots of that.
  // 3) Do all possible left-erases of that.
  // 4) Append the remaining strands from parts.

  for (size_t initial_strands = 1; initial_strands < parts.size();
       ++initial_strands) {
    // Initialize base_knot and base_str so they contain the first
    // initial_strands of data from parts.
    Knot base_knot;
    string base_str;
    for (size_t i = 0; i < initial_strands; ++i) {
      base_knot.Append(new string(parts[i]));
      base_str += parts[i];
    }

    BOOST_CHECK_EQUAL(base_knot.ToString(), base_str);

    // Take all possible sub-knots. The subknot will contain the characters
    // [left_char_idx, right_char_idx).
    for (size_t left_char_idx = 0;
         left_char_idx < base_str.size(); ++left_char_idx) {
      for (size_t right_char_idx = left_char_idx + 1;
           right_char_idx <= base_str.size(); ++right_char_idx) {
        Knot::iterator right_it;
        if (right_char_idx == base_str.size()) {
          right_it = base_knot.end();
        } else {
          right_it = base_knot.IteratorForChar(right_char_idx);
        }

        Knot sub_knot = base_knot.SubKnot(
            base_knot.IteratorForChar(left_char_idx), right_it);
        string sub_str = base_str.substr(left_char_idx,
                                         right_char_idx - left_char_idx);

        BOOST_CHECK_EQUAL(sub_knot.ToString(), sub_str);

        // Now do all possible left-erases.
        for (size_t char_to_keep = 1; char_to_keep < sub_str.size();
             ++char_to_keep) {
          Knot erased_knot = sub_knot;
          erased_knot.LeftErase(erased_knot.IteratorForChar(char_to_keep));
          string erased_str = sub_str.substr(char_to_keep, string::npos);

          BOOST_CHECK_EQUAL(erased_knot, erased_str);

          // Finally, append any strands remaining in parts.
          for (size_t j = initial_strands; j < parts.size(); ++j) {
            erased_knot.Append(new string(parts[j]));
            erased_str += parts[j];

            BOOST_CHECK_EQUAL(erased_knot, erased_str);
          }
        }
      }
    }
  }
}
