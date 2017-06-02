//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A Strand (for use with Knot) that holds BPBuffer
//                     objects. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Aug 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_BPBUFFER_STRAND_H_
#define CPP_COMMON_BPBUFFER_STRAND_H_

#include "buffer-pool.h"
#include "fixed-size-memory-pool.h"
#include "knot-impl/strand.h"

typedef boost::shared_ptr<BPBuffer> SharedBPBufferPtr;

/// A Strand, to be used with the Knot class, for holding data from a BufferPool.
/// This requires a different strand class as it must return its buffer to the
/// BufferPool rather than freeing it in its destructor. Note that any user of
/// this calss will also have to allocate and free BPBufferStrand objects
/// repeatedly, and that could be expensive. Since BPBufferStrand is a fixed size
/// (regardless of the size of the buffer itself since this holds only a pointer
/// to the buffer) this overloads operators new and delete so that the memory for
/// this object comes from a FixedSizeMemoryPool.
class BPBufferStrand : public CharStrandBase {
 public:
  /// Construct a strand that holds the 1st length characters in data. This takes
  /// ownership of data.
  BPBufferStrand(BPBuffer* data, size_t length)
      : CharStrandBase(length), data_(data) {
  }
  /// Construct a strand that holds the 1st length characters of data starting at
  /// start. This takes ownership of *all of* data even though only part of it is
  /// used.
  BPBufferStrand(SharedBPBufferPtr data, size_t start, size_t length)
      : CharStrandBase(start, length), data_(data) {
  }

  virtual ~BPBufferStrand() {}

  virtual Strand* GetSubstrand(int offset, size_t length) const;

  virtual Strand* Copy() const {
    return new BPBufferStrand(data_, StartOffset(), Size());
  }

  /// Overload operators new and delete so the memory all comes from a
  /// FixedSizeMemoryPool. We allocate and free a ton of these so using a pool
  /// makes it much more efficient.
  void* operator new(size_t size);
  void operator delete(void* memory);

 protected:
  virtual const char* GetArray() const {
    return data_->buffer();
  }

 private:
  SharedBPBufferPtr data_;
  static FixedSizeMemoryPool memory_pool_;
};

////////////////////////////////////////////////////////////////////////////////
// Inline methods
////////////////////////////////////////////////////////////////////////////////

inline Strand* BPBufferStrand::GetSubstrand(int offset, size_t length) const {
  if (length == Strand::npos) {
    length = Size() - offset;
  }
  DCHECK(offset + length <= static_cast<size_t>(Size()));
  return new BPBufferStrand(data_, offset + StartOffset(), length);
}

inline void* BPBufferStrand::operator new(size_t size) {
  CHECK(size == sizeof(BPBufferStrand));
  return memory_pool_.GetMemory();
}

inline void BPBufferStrand::operator delete(void* memory) {
  memory_pool_.ReturnMemory(memory);
}

#endif
