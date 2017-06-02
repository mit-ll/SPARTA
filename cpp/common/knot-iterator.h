//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        An STL compatible iterator for the Knot class. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 13 Aug 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_KNOT_ITERATOR_H_
#define CPP_COMMON_KNOT_ITERATOR_H_

#include <iterator>

#include "knot-impl/knot-node-deque.h"
#include "knot-impl/strand.h"

class Knot;

/// This is "really" a nested subclass of Knot. It is typedef'd in Knot to
/// Knot::iterator. Always use that instead.
class _KnotIterator_
    : public std::iterator<std::bidirectional_iterator_tag, const char, int> {
 public:
  _KnotIterator_();
  _KnotIterator_(const _KnotIterator_& other);

  const char& operator*() const {
    const char* char_ptr = CurStrand()->PtrToCharAt(char_idx_);
    return *char_ptr;
  }

  const char* operator->() const {
    return &operator*();
  }

  _KnotIterator_& operator++();
  _KnotIterator_ operator++(int _nothing_);

  _KnotIterator_& operator--();
  _KnotIterator_ operator--(int _nothing_);

  bool operator==(const _KnotIterator_& other) const {
    CHECK(knot_ == other.knot_)
        << "Comparing iterators from different Knot's is dangerous. "
        << "See the comments on the knot_ member of _KnotIterator_";
    return (strand_idx_ == other.strand_idx_) &&
        (char_idx_ == other.char_idx_);
  }

  bool operator!=(const _KnotIterator_& other) const {
    return !(*this == other);
  }

  _KnotIterator_& operator=(const _KnotIterator_& other);

  /// Returns the number of characters between two iterators.
  int operator-(const _KnotIterator_& other) const;

 private:
  _KnotIterator_(int strand_idx, int char_idx, const Knot* knot);
  friend class Knot;

  const Strand* CurStrand() const {
    return GetDeque()->GetStrand(strand_idx_);
  }

  /// Returns the total number of characters to the left of this iterator.
  int CumCharCount() const;

  /// The following two methods are used by Knot::Find. Knot is a friend so it
  /// can access these. We don't want Knot using strand_idx_ and char_idx_
  /// directly for encapsulation reasons.
  int CurStrandIdx() const {
    return strand_idx_;
  }

  int CurCharInCurStrand() const {
    return char_idx_;
  }

  const KnotNodeDeque* GetDeque() const;

  /// Make this iterator == end (what's returned by Knot::end().
  void MakeEnd();
  /// This is called if the user calls operator-- on the end() iterator. This
  /// makes it point at the last character in the knot.
  void MoveToEnd() {
    strand_idx_ = GetDeque()->GetNumStrands() - 1;
    char_idx_ = GetDeque()->GetStrand(strand_idx_)->Size() -1;
  }

  /// The current character is given by
  /// deque_->GetStrand(strand_idx_)->CharAt(char_idx). If strand_idx_ and
  /// char_idx_ are both -1 this is the "end" iterator (e.g. what's returned by
  /// Knot::end().
  int strand_idx_;
  int char_idx_;
  /// We really only need access to the KnotNodeDeque, but we want to ensure that
  /// an iterator remains valid after an Append call and Append may do a
  /// copy-on-write on the deque. Thus we maintain a handle to the Knot instead.
  ///
  /// NOTE: This has to be a reference to a valid Knot object. Thus returning a
  /// Knot::iterator from a function that takes a Knot (rather than a Knot& or a
  /// Knot*) is not safe as the iterator will then refer to an object that no
  /// longer exists!
  const Knot* knot_;
};


#endif
