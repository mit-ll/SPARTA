//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of Strans subclasses.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Jul 2012   omd            Original Version
//*****************************************************************

#include "strand.h"

#include <limits>

#include "common/check.h"

const size_t Strand::npos = std::numeric_limits<size_t>::max();

////////////////////////////////////////////////////////////////////////////////
// CharStrandBase
////////////////////////////////////////////////////////////////////////////////

CharStrandBase::CharStrandBase(size_t length)
    : start_(0), end_(length) {
}
CharStrandBase::CharStrandBase(size_t start, size_t length)
    : start_(start), end_(start + length) {
}

const char* CharStrandBase::PtrToCharAt(size_t offset) const {
  CHECK(offset < (end_ - start_));
  return &GetArray()[start_ + offset];
}


size_t CharStrandBase::Find(char to_find) const {
  const char* position = reinterpret_cast<const char*>(
      memchr(GetArray() + start_, to_find, end_ - start_));
  if (position == NULL) {
    return npos;
  } else {
    return position - (GetArray() + start_);
  }
}

size_t CharStrandBase::Find(char to_find, size_t start_idx) const {
  CHECK((start_ + start_idx) < end_);
  const char* position = reinterpret_cast<const char*>(
      memchr(GetArray() + start_ + start_idx,
             to_find, end_ - start_ - start_idx));
  if (position == NULL) {
    return npos;
  } else {
    return position - (GetArray() + start_);
  }
}

bool CharStrandBase::EqualRange(
    const char* other, int offset, size_t length) const {
  DCHECK((offset + length) <= Size());
  return memcmp(GetArray() + start_ + offset, other, length) == 0;
}

////////////////////////////////////////////////////////////////////////////////
// CharPtrStrand
////////////////////////////////////////////////////////////////////////////////

Strand* CharPtrStrand::GetSubstrand(int offset, size_t length) const {
  if (length == Strand::npos) {
    length = Size() - offset;
  }
  DCHECK(offset + length <= static_cast<size_t>(Size()));
  return new CharPtrStrand(data_, offset + StartOffset(), length);
}

////////////////////////////////////////////////////////////////////////////////
// OwnedCharPtrStrand
////////////////////////////////////////////////////////////////////////////////

Strand* OwnedCharPtrStrand::GetSubstrand(int offset, size_t length) const {
  if (length == Strand::npos) {
    length = Size() - offset;
  }
  DCHECK(offset + length <= static_cast<size_t>(Size()));
  return new OwnedCharPtrStrand(data_, offset + StartOffset(), length);
}

////////////////////////////////////////////////////////////////////////////////
// StringStrand
////////////////////////////////////////////////////////////////////////////////

Strand* StringStrand::GetSubstrand(int offset, size_t length) const {
  if (length == Strand::npos) {
    length = Size() - offset;
  }
  DCHECK(offset + length <= static_cast<size_t>(Size()));
  return new StringStrand(data_, offset + StartOffset(), length);
}
