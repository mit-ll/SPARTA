//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        A deque that also implicitly encodes a tree.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jul 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_KNOT_IMPL_KNOT_NODE_DEQUE_H_
#define CPP_COMMON_KNOT_IMPL_KNOT_NODE_DEQUE_H_

#include <deque>

#include "knot-node.h"
#include "common/logging.h"
#include "common/check.h"

/// Main KnotNodeDeque class. This is is used by the Knot class to maintain the
/// deque of nodes.
class KnotNodeDeque {
 public:
  KnotNodeDeque();
  KnotNodeDeque(const KnotNodeDeque& other);
  virtual ~KnotNodeDeque();

  /// Returns the strand at the given offset (e.g. if offset == 0 returns the 1st
  /// strand, if it == 1 it returns the 2nd strand, etc.)
  const Strand* GetStrand(int offset) const {
    DCHECK(offset >= 0);
    DCHECK(static_cast<size_t>(offset) < deque_.size());
    return deque_[offset]->strand().get();
  }

  /// Append this strand to the Deque.  This takes ownership of strand.
  void Append(const Strand* strand);
  /// Append this strand. Increments the reference count of the shared strand.
  void Append(KnotNode::SharedStrand strand);

  /// Returns the index of the strand containing the character with index
  /// char_idx (0-based).  On return offset is the number of characters into the
  /// strand where the char_idx character can be found. In other words:
  ///
  /// int offset;
  /// int s = deque.StrandWithChar(c, &offset);
  /// cout << "Character " << c << " of the knot is: "
  ///      << deque.GetStrand(s)->CharAt(offset) << endl; 
  ///
  /// This is an O(log(m)) operation where m == the number of nodes in the deque.
  int StrandWithChar(size_t char_idx, int* offset) const;

  /// Returns the number of strands in the deque.
  int GetNumStrands() const {
    return deque_.size();
  }

  /// Returns the number of characters to the left of the given strand.
  int LeftCountForStrand(int strand_idx) const;

  /// Return the number of characters in all the strands in the deque.
  virtual size_t GetCharCount() const;

  /// Returns a KnotNodeSubDeque that shares the deque from start_offset to
  /// start_offset + num_nodes. If left_replace or right_replace is not NULL the
  /// left-most (right-most) node will be the given replacement strand instead of
  /// what was in this deque. Note that this creates new nodes but it does not
  /// copy the strands - it just increments their reference counts.
  KnotNodeDeque* GetSubDeque(int start_offset, int num_nodes,
                                Strand* left_replace, Strand* right_replace);

 private:
  typedef std::deque<KnotNode*> NodeDeque;

  /// Shared pointer to the actual deque.
  NodeDeque deque_;
};

#endif
