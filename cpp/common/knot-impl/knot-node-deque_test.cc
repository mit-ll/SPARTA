//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for KnotNodeDeque, its iterator, etc.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jul 2012   omd            Original Version
//*****************************************************************

#include "knot-node-deque.h"

#include <boost/assign/list_of.hpp>
#include <cstring>
#include <sstream>
#include <vector>

#include "knot-node.h"
#include "strand.h"
#include "common/string-algo.h"

#define BOOST_TEST_MODULE KnotNodeDequeTest

#include "common/test-init.h"

using namespace std;
using boost::assign::list_of;

// Check that I can create a left sub-deque (e.g. it's all the characters
// starting at the left, up to some point) from a deque. Also check that after
// free the full deque the sub-deque is still defined.
BOOST_AUTO_TEST_CASE(LeftSubDequeWorks) {
  auto_ptr<KnotNodeDeque> full(new KnotNodeDeque);

  vector<const char*> parts;
  parts.push_back("This is ");
  parts.push_back("a series ");
  parts.push_back("of strings ");
  parts.push_back("that make one long deque ");
  for (vector<const char*>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand* s = new CharPtrStrand(StrDup(*i), strlen(*i));
    full->Append(s);
  }

  auto_ptr<KnotNodeDeque> sub(full->GetSubDeque(0, 2, NULL, NULL));

  BOOST_REQUIRE_EQUAL(full->GetNumStrands(), 4);
  for (int i = 0; i < 4; ++i) {
    BOOST_CHECK_EQUAL(full->GetStrand(i)->ToString(), parts[i]);
  }

  BOOST_REQUIRE_EQUAL(sub->GetNumStrands(), 2);
  for (int i = 0; i < 2; ++i) {
    BOOST_CHECK_EQUAL(sub->GetStrand(i)->ToString(), parts[i]);
  }

  full.reset();

  // The sub-deque should still be valid.
  BOOST_REQUIRE_EQUAL(sub->GetNumStrands(), 2);
  for (int i = 0; i < 2; ++i) {
    BOOST_CHECK_EQUAL(sub->GetStrand(i)->ToString(), parts[i]);
  }
}

// Check that we can delete the sub-knot before the full knot and that works.
// Note that the destructor has extra check in debug builds to ensure that
// everything was, in fact, freed.
BOOST_AUTO_TEST_CASE(DeleteLeftSubSubBeforeFull) {
  auto_ptr<KnotNodeDeque> full(new KnotNodeDeque);

  vector<const char*> parts;
  parts.push_back("This is ");
  parts.push_back("a series ");
  parts.push_back("of strings ");
  parts.push_back("that make one long deque ");
  for (vector<const char*>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand* s = new CharPtrStrand(StrDup(*i), strlen(*i));
    full->Append(s);
  }

  auto_ptr<KnotNodeDeque> sub(full->GetSubDeque(0, 2, NULL, NULL));
  BOOST_REQUIRE_EQUAL(sub->GetNumStrands(), 2);
  for (int i = 0; i < 2; ++i) {
    BOOST_CHECK_EQUAL(sub->GetStrand(i)->ToString(), parts[i]);
  }
  sub.reset();

  // The full deque should still be valid.
  BOOST_REQUIRE_EQUAL(full->GetNumStrands(), 4);
  for (int i = 0; i < 4; ++i) {
    BOOST_CHECK_EQUAL(full->GetStrand(i)->ToString(), parts[i]);
  }
}

// Test that a sub-knot with a replacement node on the right works.
BOOST_AUTO_TEST_CASE(LeftSubWithReplaceWorks) {
  auto_ptr<KnotNodeDeque> full(new KnotNodeDeque);

  vector<const char*> parts;
  parts.push_back("s1 ");
  parts.push_back("s2 ");
  parts.push_back("s3 ");
  parts.push_back("longer string here ");
  parts.push_back("s5 ");
  parts.push_back("s6 ");
  parts.push_back("s7 ");
  for (vector<const char*>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand* s = new CharPtrStrand(StrDup(*i), strlen(*i));
    full->Append(s);
  }

  auto_ptr<KnotNodeDeque> sub(
      full->GetSubDeque(0, 4, NULL, full->GetStrand(3)->GetSubstrand(0, 4)));

  BOOST_CHECK_EQUAL(sub->GetStrand(0)->ToString(), "s1 ");
  BOOST_CHECK_EQUAL(sub->GetStrand(1)->ToString(), "s2 ");
  BOOST_CHECK_EQUAL(sub->GetStrand(2)->ToString(), "s3 ");
  BOOST_CHECK_EQUAL(sub->GetStrand(3)->ToString(), "long");
}

// Create a subknot that holds the characters from some point in the middle up
// to and including the end.
BOOST_AUTO_TEST_CASE(RightSubDequeWorks) {
  auto_ptr<KnotNodeDeque> full(new KnotNodeDeque);

  vector<string> parts = list_of("Part 1")("Part 2")("Part 3")("Part 4")
      ("Part 5");

  for (vector<string>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand *s = new CharPtrStrand(StrDup(i->c_str()), i->size());
    full->Append(s);
  }

  auto_ptr<KnotNodeDeque> sub(full->GetSubDeque(2, 3, NULL, NULL));

  BOOST_REQUIRE_EQUAL(sub->GetNumStrands(), 3);
  BOOST_CHECK_EQUAL(sub->GetStrand(0)->ToString(), parts[2]);
  BOOST_CHECK_EQUAL(sub->GetStrand(1)->ToString(), parts[3]);
  BOOST_CHECK_EQUAL(sub->GetStrand(2)->ToString(), parts[4]);

  // The full deque should still be valid.
  BOOST_REQUIRE_EQUAL(full->GetNumStrands(), parts.size());
  for (int i = 0; i < 4; ++i) {
    BOOST_CHECK_EQUAL(full->GetStrand(i)->ToString(), parts[i]);
  }
}

// Check that I can create a sub-deque, free it, and the full deque is still
// valid.
BOOST_AUTO_TEST_CASE(DeleteRightSubBeforeFullWorks) {
  auto_ptr<KnotNodeDeque> full(new KnotNodeDeque);

  vector<string> parts = list_of("Part 1")("Part 2")("Part 3")("Part 4")
      ("Part 5");

  for (vector<string>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand *s = new CharPtrStrand(StrDup(i->c_str()), i->size());
    full->Append(s);
  }

  auto_ptr<KnotNodeDeque> sub(full->GetSubDeque(2, 2, NULL, NULL));

  BOOST_REQUIRE_EQUAL(sub->GetNumStrands(), 2);
  BOOST_CHECK_EQUAL(sub->GetStrand(0)->ToString(), parts[2]);
  BOOST_CHECK_EQUAL(sub->GetStrand(1)->ToString(), parts[3]);

  // Free the sub-deque
  sub.reset();

  // The full deque should still be valid.
  BOOST_REQUIRE_EQUAL(full->GetNumStrands(), parts.size());
  for (int i = 0; i < 4; ++i) {
    BOOST_CHECK_EQUAL(full->GetStrand(i)->ToString(), parts[i]);
  }

}

// Make sure a right-subknot with a left ghost strand works.
BOOST_AUTO_TEST_CASE(RightSubDequeWithGhostWorks) {
  auto_ptr<KnotNodeDeque> full(new KnotNodeDeque);

  vector<string> parts = list_of("Part 1")("Part 2")("Part 3")("Part 4")
      ("Part 5");

  for (vector<string>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand *s = new CharPtrStrand(StrDup(i->c_str()), i->size());
    full->Append(s);
  }

  auto_ptr<KnotNodeDeque> sub(full->GetSubDeque(
          2, 2, full->GetStrand(2)->GetSubstrand(3, 3), NULL));

  BOOST_REQUIRE_EQUAL(sub->GetNumStrands(), 2);
  // The first node should be a sub-strand.
  BOOST_CHECK_EQUAL(sub->GetStrand(0)->ToString(), "t 3");
  BOOST_CHECK_EQUAL(sub->GetStrand(1)->ToString(), parts[3]);

  // The full deque should still be valid.
  BOOST_REQUIRE_EQUAL(full->GetNumStrands(), parts.size());
  for (int i = 0; i < 4; ++i) {
    BOOST_CHECK_EQUAL(full->GetStrand(i)->ToString(), parts[i]);
  }
}

// Make sure StrandWithChar works on a regular, full deque.
BOOST_AUTO_TEST_CASE(StrandWithCharWorks) {
  KnotNodeDeque full_d;

  vector<string> parts = list_of("Part 1")("Part 2")("Part 3")("Part 4")
      ("Part 5");

  string complete_string;

  for (vector<string>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand *s = new CharPtrStrand(StrDup(i->c_str()), i->size());
    full_d.Append(s);
    complete_string += *i;
  }

  for (size_t i = 0; i < complete_string.size(); ++i) {
    int strand_idx, offset;
    strand_idx = full_d.StrandWithChar(i, &offset);
    BOOST_CHECK_EQUAL(full_d.GetStrand(strand_idx)->CharAt(offset),
                      complete_string[i]);
  }
}

// First test to check that StrandWithChar works properly with a subknot that's
// the right sub-knot. This checks that it works when the right sub-knot
// includes the 1st node in the deque.
BOOST_AUTO_TEST_CASE(StrandWithCharRightSubFirstNode) {
  KnotNodeDeque full_d;

  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test");

  string complete_string;
  for (vector<string>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand *s = new CharPtrStrand(StrDup(i->c_str()), i->size());
    full_d.Append(s);
    complete_string += *i;
  }

  auto_ptr<KnotNodeDeque> sub(full_d.GetSubDeque(
          0, 4, full_d.GetStrand(0)->GetSubstrand(3, Strand::npos), NULL));
  string substr(complete_string.begin() + 3, complete_string.end());

  for (size_t i = 0; i < substr.size(); ++i) {
    int strand_idx, offset;
    strand_idx = sub->StrandWithChar(i, &offset);
    BOOST_CHECK_EQUAL(sub->GetStrand(strand_idx)->CharAt(offset), substr[i]);
  }
}

// Similar to the above but the subknot starts in the 2nd node and there are no
// ghost nodes at all.
BOOST_AUTO_TEST_CASE(StrandWithCharRightSubSecondNodeNoGhost) {
  KnotNodeDeque full_d;

  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test");

  string complete_string;
  for (vector<string>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand *s = new CharPtrStrand(StrDup(i->c_str()), i->size());
    full_d.Append(s);
    complete_string += *i;
  }

  auto_ptr<KnotNodeDeque> sub(full_d.GetSubDeque(
          1, 3, NULL, NULL));
  string substr(complete_string.begin() + parts[0].size(),
                complete_string.end());

  for (size_t i = 0; i < substr.size(); ++i) {
    int strand_idx, offset;
    strand_idx = sub->StrandWithChar(i, &offset);
    BOOST_CHECK_EQUAL(sub->GetStrand(strand_idx)->CharAt(offset), substr[i]);
  }
}

// Like the above but also uses a left ghost node.
BOOST_AUTO_TEST_CASE(StrandWithCharRightSubSecondNodeWithGhost) {
  KnotNodeDeque full_d;

  vector<string> parts = list_of("This is")(" a goo")("d unit")(" test");

  string complete_string;
  for (vector<string>::iterator i = parts.begin(); i != parts.end(); ++i) {
    Strand *s = new CharPtrStrand(StrDup(i->c_str()), i->size());
    full_d.Append(s);
    complete_string += *i;
  }

  auto_ptr<KnotNodeDeque> sub(full_d.GetSubDeque(
          1, 3, full_d.GetStrand(1)->GetSubstrand(1, Strand::npos), NULL));
  string substr(complete_string.begin() + parts[0].size() + 1,
                complete_string.end());

  for (size_t i = 0; i < substr.size(); ++i) {
    int strand_idx, offset;
    strand_idx = sub->StrandWithChar(i, &offset);
    BOOST_CHECK_EQUAL(sub->GetStrand(strand_idx)->CharAt(offset), substr[i]);
  }
}

// Create a sub-deque that contains the middle of a deque. Then delete the full
// deque and make sure the sub-deque is still valid and that character access
// works as expected.
BOOST_AUTO_TEST_CASE(MiddleSubAfterDeleteFullWorks) {
  auto_ptr<KnotNodeDeque> full(new KnotNodeDeque);
  string full_string;

  vector<string> parts = list_of("part 1 ")("part 2 ")("longer part 3")
      (" also part 4.")(" There's a part 5 for fun.")(" and one to grow on!");

  for (vector<string>::iterator i = parts.begin(); i != parts.end(); ++i) {
    full->Append(new StringStrand(new string(*i)));
    full_string += *i;
  }

  // Now create a sub-deque. This will contain part of the 2nd strand, all of
  // strands 3 and 4, and part of strand 5 (all 1-indexed here).
  auto_ptr<KnotNodeDeque> sub(full->GetSubDeque(
          1, 4, full->GetStrand(1)->GetSubstrand(4, 3),
          full->GetStrand(4)->GetSubstrand(0, 6)));
  // sub should now contain the data " 2 longer part 3 also part 4. There". Make
  // sure this is true on a character-by-character basis.
  string sub_str = full_string.substr(11, 35);

  for (size_t i = 0; i < sub_str.size(); ++i) {
    int strand_idx, offset;
    strand_idx = sub->StrandWithChar(i, &offset);
    BOOST_CHECK_EQUAL(sub->GetStrand(strand_idx)->CharAt(offset), sub_str[i]);
  }

  // Now free the base deque and make sure the sub-deque is still valid.
  full.reset();
  for (size_t i = 0; i < sub_str.size(); ++i) {
    int strand_idx, offset;
    strand_idx = sub->StrandWithChar(i, &offset);
    BOOST_CHECK_EQUAL(sub->GetStrand(strand_idx)->CharAt(offset), sub_str[i]);
  }
}
