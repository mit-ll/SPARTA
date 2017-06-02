//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of Knot. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 06 Aug 2012   omd            Original Version
//*****************************************************************

#include "knot.h"

#include <fcntl.h>
#include <limits>
#include <unistd.h>

#include "check.h"
#include "knot-impl/strand.h"
#include "util.h"

typedef boost::shared_ptr<Strand> SharedStrand;

using namespace std;

Knot::Knot() : knot_deque_(new KnotNodeDeque) {
}

Knot::Knot(const char* data, size_t length)
    : knot_deque_(new KnotNodeDeque) {
  Append(data, length);
}

Knot::Knot(const std::string* data)
    : knot_deque_(new KnotNodeDeque) {
  Append(data);
}

Knot::Knot(SharedKnotDeque knot_deque)
    : knot_deque_(knot_deque) {
}


Knot::~Knot() {
}

void Knot::Clear() {
  knot_deque_.reset(new KnotNodeDeque);
}

void Knot::Append(Strand* strand) {
  // Copy on write. Note that this does not lock a mutex and may therefore make
  // an unnecessary copy. That's safe and probably cheaper than the mutex
  // lock...
  if (knot_deque_.use_count() > 1) {
    LOG(DEBUG) << "Knot::Append caused a copy-on-write";
    knot_deque_.reset(new KnotNodeDeque(*knot_deque_.get()));
    DCHECK(knot_deque_.use_count() == 1);
  }
  knot_deque_->Append(strand);
}

void Knot::Append(const char* data, size_t length) {
  Strand* strand = new CharPtrStrand(data, length);
  Append(strand);
}

void Knot::AppendOwned(const char* data, size_t length) {
  Strand* strand = new OwnedCharPtrStrand(data, length);
  Append(strand);
}

void Knot::Append(const std::string* data) {
  Strand* strand = new StringStrand(data);
  Append(strand);
}

void Knot::Append(const Knot& other) {
  for (int i = 0; i < other.knot_deque_->GetNumStrands(); ++i) {
    Append(other.knot_deque_->GetStrand(i)->Copy());
  }
}

void Knot::ToString(string* output) const {
  output->clear();
  output->reserve(Size());
  for (int i = 0; i < knot_deque_->GetNumStrands(); ++i) {
    *output += knot_deque_->GetStrand(i)->ToString();
  }
}

string Knot::ToString() const {
  string result;
  ToString(&result);
  return result;
}

size_t Knot::Size() const {
  return knot_deque_->GetCharCount();
}

Knot::iterator Knot::Find(char to_find) const {
  return Find(to_find, begin());
}

Knot::iterator Knot::Find(char to_find, iterator start_it) const {
  int strand_idx = start_it.CurStrandIdx();
  int start_char = start_it.CurCharInCurStrand();
  while (strand_idx < knot_deque_->GetNumStrands()) {
    const Strand* s = knot_deque_->GetStrand(strand_idx);
    DCHECK(start_char < s->Size());
    size_t pos_in_strand = s->Find(to_find, start_char);
    if (pos_in_strand != Strand::npos) {
      return iterator(strand_idx,
                      static_cast<int>(pos_in_strand), this);
    }
    ++strand_idx;
    start_char = 0;
  }
  return end();
}

Knot::iterator Knot::LastCharIter() const {
  int strand_idx = knot_deque_->GetNumStrands() - 1;
  DCHECK(strand_idx >= 0);
  int char_idx = knot_deque_->GetStrand(strand_idx)->Size() - 1;
  CHECK(char_idx >= 0);
  return iterator(strand_idx, char_idx, this);
}

Knot::iterator Knot::IteratorForChar(int char_idx) const {
  int char_offset;
  int strand_idx = knot_deque_->StrandWithChar(char_idx, &char_offset);
  return iterator(strand_idx, char_offset, this);
}

Knot Knot::SubKnot(iterator start_it, iterator end_it) const {
  DCHECK(start_it != end());

  if (start_it == end_it) {
    // 0-length sub-knot. Strange, but OK.
    return Knot();
  }

  // end_it is an *exclusive* end. If end_it == end() or 
  // end_it.CurCharInCurStrand() == 0 then we need to fix it up.
  iterator inclusive_end_it = end_it;
  if (inclusive_end_it == end()) {
    inclusive_end_it = LastCharIter(); 
  } else {
     DCHECK(end_it != start_it);
    --inclusive_end_it;
  }
  
  Strand* left_replace = NULL;
  // We need a left replacement strand in 2 situations:
  // 
  // 1) The start and end of the sub-knot are in the same strand and the
  //    sub-knot is not equal to the entire strand.
  // 3) The left-most character is not character 0 and condition 1 is false.
  //
  // Note: If the *exclusive* end is == end() or it points to character 0 of
  // some strand, then the *inclusive* end is the last character in this strand.
  if (start_it.CurStrandIdx() == inclusive_end_it.CurStrandIdx() &&
      (start_it.CurCharInCurStrand() != 0 ||
        (end_it != end() &&
        end_it.CurCharInCurStrand() != 0))) {
    size_t length =
        inclusive_end_it.CurCharInCurStrand() -
        start_it.CurCharInCurStrand() + 1;
    left_replace = start_it.CurStrand()->GetSubstrand(
        start_it.CurCharInCurStrand(), length);
  } else if (start_it.CurCharInCurStrand() != 0) {
    left_replace = start_it.CurStrand()->GetSubstrand(
        start_it.CurCharInCurStrand(), Strand::npos);
  }

  // A right replacement node is needed only if the following conditions are
  // *all* true:
  //
  // 1) The end of the subknot does not include the last character in the
  //    current knot
  // 2) The end of the subknot is not the same strand as the start of the
  // subknot.
  Strand* right_replace = NULL;
  if (start_it.CurStrandIdx() != inclusive_end_it.CurStrandIdx() &&
      end_it != end() && end_it.CurCharInCurStrand() != 0) {
    right_replace = knot_deque_->GetStrand(inclusive_end_it.CurStrandIdx())->
        GetSubstrand(0, end_it.CurCharInCurStrand());
  }

  SharedKnotDeque new_deque(
      knot_deque_->GetSubDeque(
          start_it.CurStrandIdx(),
          inclusive_end_it.CurStrandIdx() - start_it.CurStrandIdx() + 1,
          left_replace, right_replace));

  return Knot(new_deque);
}

void Knot::LeftErase(iterator up_to_iter) {
  DCHECK(up_to_iter != end());

  Strand* left_ghost = NULL;
  if (up_to_iter.CurCharInCurStrand() != 0) {
    left_ghost = up_to_iter.CurStrand()->GetSubstrand(
        up_to_iter.CurCharInCurStrand(), Strand::npos);
  }
  SharedKnotDeque new_deque(knot_deque_->GetSubDeque(
      up_to_iter.CurStrandIdx(),
      knot_deque_->GetNumStrands() - up_to_iter.CurStrandIdx(),
      left_ghost, NULL));
  // Note that right_ref_count_ stays the same.
  knot_deque_ = new_deque;
}

bool Knot::StartsWith(const char* other, size_t length) const {
  DCHECK(length > 0);
  if (length > Size()) {
    return false;
  }
  int still_to_check = length;
  int checked = 0;
  int strand_idx = 0;
  while (still_to_check > 0) {
    const Strand* strand = knot_deque_->GetStrand(strand_idx);
    int to_check = min(strand->Size(), still_to_check);
    if (!strand->EqualRange(other + checked, 0, to_check)) {
      return false;
    }
    still_to_check -= to_check;
    checked += to_check;
    ++strand_idx;
  }
  return true;
}

void Knot::WriteToStream(std::ostream& stream) const {
  for (int i = 0; i < knot_deque_->GetNumStrands(); ++i) {
    knot_deque_->GetStrand(i)->WriteToStream(stream);
  }
}

// TODO(odain): We could use the Linux-specific writev system call on Linux to
// reduce the number of system calls here. The current implementation might be
// particularly slow if there are many small strands as this translates to many
// system calls each of which transfers only a little bit of data.
Knot::iterator Knot::WriteToFileDescriptor(
    int file_descriptor, iterator start_it) const {
  // Make sure the file descriptor is in non-blocking mode.
  DCHECK((fcntl(file_descriptor, F_GETFL) & O_NONBLOCK) != 0);

  int offset_in_strand = start_it.CurCharInCurStrand();

  int strand_idx = start_it.CurStrandIdx();
  int end_strand_idx = knot_deque_->GetNumStrands() - 1;
  for (; strand_idx <= end_strand_idx; ++strand_idx) {
    const Strand* cur_strand = knot_deque_->GetStrand(strand_idx);
    ssize_t written = write(file_descriptor,
                            cur_strand->ToCharPtr() + offset_in_strand,
                            cur_strand->Size() - offset_in_strand);

    if (written == -1) {
      if (errno == EAGAIN || errno == EWOULDBLOCK) {
        return iterator(strand_idx, 0, this);
      } else {
        LOG(FATAL) << "Error: " << ErrorMessageFromErrno(errno);
      }
    } else if (written < (cur_strand->Size() - offset_in_strand)) {
      return iterator(strand_idx, offset_in_strand + written, this);
    }
    offset_in_strand = 0;
  }
  return end();
}

// TODO(odain) as above it may be more efficient to call writev here.
void Knot::BlockingWriteToFileDescriptor(int file_descriptor) const {
  DCHECK((fcntl(file_descriptor, F_GETFL) & O_NONBLOCK) == 0);
  for (int i = 0; i < knot_deque_->GetNumStrands(); ++i) {
    const Strand* cur_strand = knot_deque_->GetStrand(i);
    ssize_t written = write(file_descriptor, cur_strand->ToCharPtr(),
                            cur_strand->Size());
    if (written == -1) {
      LOG(FATAL) << "Error writing Knot to file: "
          << ErrorMessageFromErrno(errno);
    } else {
      CHECK(written == cur_strand->Size());
    }
  }
}
