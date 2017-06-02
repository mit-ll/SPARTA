//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of _KnotIterator_. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 14 Aug 2012   omd            Original Version
//*****************************************************************

#include "knot.h"
#include "knot-iterator.h"

#include "check.h"

_KnotIterator_::_KnotIterator_()
    : strand_idx_(-1), char_idx_(-1), knot_(NULL) {
}

_KnotIterator_::_KnotIterator_(const _KnotIterator_& other)
    : strand_idx_(other.strand_idx_), char_idx_(other.char_idx_),
      knot_(other.knot_) {
}

_KnotIterator_::_KnotIterator_(int strand_idx, int char_idx,
                               const Knot* knot)
    : strand_idx_(strand_idx), char_idx_(char_idx),
      knot_(knot) {
}

_KnotIterator_& _KnotIterator_::operator++() {
  DCHECK(char_idx_ >= 0 && strand_idx_ >= 0);

  ++char_idx_;
  if (char_idx_ >= CurStrand()->Size()) {
    ++strand_idx_;
    if (strand_idx_ >= knot_->knot_deque_->GetNumStrands()) {
      MakeEnd();
    } else {
      char_idx_ = 0;
    }
  }
  return *this;
}

_KnotIterator_ _KnotIterator_::operator++(int _nothing_) {
  _KnotIterator_ return_it(*this);
  ++(*this);
  return return_it;
}

_KnotIterator_& _KnotIterator_::operator--() {
  // If this was the end() iterator make it point to the last character in the
  // knot.
  if (char_idx_ == -1 && strand_idx_ == -1) {
    MoveToEnd();
    return *this;
  }

  DCHECK(char_idx_ >= 0 && strand_idx_ >= 0);

  --char_idx_;
  if (char_idx_ < 0) {
    if (strand_idx_ == 0) {
      LOG(FATAL) << "Called operator-- on an iterator that == begin().";
      // keep the compiler happy - this will never be executed.
      return *this;
    } else {
      --strand_idx_;
      char_idx_ = CurStrand()->Size() - 1;
    }
  }
  return *this;
}

_KnotIterator_ _KnotIterator_::operator--(int _nothing_) {
  _KnotIterator_ return_it(*this);
  --(*this);
  return return_it;
}

int _KnotIterator_::CumCharCount() const {
  if (strand_idx_ == -1) {
    // This is the end() iterator;
    DCHECK(char_idx_ == -1);
    return knot_->Size();
  } else {
    int strand_count = knot_->knot_deque_->LeftCountForStrand(strand_idx_);
    DCHECK(strand_count >= 0);
    DCHECK(strand_count < static_cast<int>(knot_->Size()));
    return strand_count + char_idx_;
  }
}

int _KnotIterator_::operator-(const _KnotIterator_& other) const {
  return this->CumCharCount() - other.CumCharCount(); 
}

void _KnotIterator_::MakeEnd() {
  strand_idx_ = -1;
  char_idx_ = -1;
}

_KnotIterator_& _KnotIterator_::operator=(const _KnotIterator_& other) {
  strand_idx_ = other.strand_idx_;
  char_idx_ = other.char_idx_;
  knot_ = other.knot_;
  return *this;
}

const KnotNodeDeque* _KnotIterator_::GetDeque() const {
  return knot_->knot_deque_.get();
}
