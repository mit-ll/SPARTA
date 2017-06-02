//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A node in the knot's tree. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 30 Jul 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_KNOT_IMPL_KNOT_NODE_H_
#define CPP_COMMON_KNOT_IMPL_KNOT_NODE_H_

#include <boost/shared_ptr.hpp>

#include "common/check.h"
#include "strand.h"

// This is what is stored in the KnotNodeDeque. It holds just two data items: a
// shared pointer to a strand, and a cumulative character count which indicates
// the number of characters from the beginning of the Knot up to, and including,
// this strand. This can be used to find the character at any given offset in
// Log(m) time where m == the number of strands in the Knot.
class KnotNode {
 public:
  typedef boost::shared_ptr<const Strand> SharedStrand;
  KnotNode(const Strand* strand) : strand_(strand) {}
  KnotNode(SharedStrand strand)
      : strand_(strand) {}
  KnotNode(const KnotNode& other)
      : cum_char_count_(other.cum_char_count_), strand_(other.strand_) {}

  SharedStrand strand() const { return strand_; }

  int cum_char_count() const {
    return cum_char_count_;
  }

  void set_cum_char_count(int value) {
    cum_char_count_ = value;
  }

 private:
  // The number of characters in this node and all nodes to the left of this
  // node in the *full* deque. This is the number to the left in the *deque*,
  // not the *tree*. Maintaining the count in the deque can be done in O(1) time
  // and we cna then find any character by binary search. We can also easily
  // reverse engineer the count to the left in tree given the count in the
  // deque.  Subknots do not necessarily share the full deque and so will have
  // to adjust this accordingly.
  int cum_char_count_;
  SharedStrand strand_;
};

#endif
