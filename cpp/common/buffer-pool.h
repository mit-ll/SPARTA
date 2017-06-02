//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A pool of char* buffers. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Aug 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_BUFFER_POOL_H_
#define CPP_COMMON_BUFFER_POOL_H_

#include <boost/thread.hpp>
#include <deque>
#include <vector>

#include "check.h"

class ActualBufferPool;

/// A thin wrapper around a char*. The main purpose of this class is that it has
/// a destructor that returns the char* array back to the BufferPool from whence
/// it came. See the comments on that class for details.
///
/// NOTE: Is it *not* safe to subclass this class as it overrides operator
/// delete.
class BPBuffer {
 public:
  /// Construct a BPBuffer to hold size bytes. The allocated memory is *not*
  /// freed by the destructor. It is only freed by call FreeMemory - the
  /// BufferPool's destructor calls that method.
  BPBuffer(int size);
  /// Just returns the memory to the BufferPool. Note that operator delete is
  /// also overloaded to ensure the memory doesn't actually get freed.
  ~BPBuffer();

  /// Overloaded operator delete does *not* free the memory associated with this
  /// object. This object's destructor returns the memory to the BufferPool
  /// instead. BufferPool's destructor explicitly calls the global delete to
  /// actually free the memory.
  void operator delete(void* p) {
  }

  /// Accessors for the wrapped char*
  char* buffer() { return buffer_; }
  const char* buffer() const { return buffer_; }

  void FreeMemory() {
    delete[] buffer_;
  }

 private:
  /// Constructor for a BPBUffer that holds size char's and returns its memory
  /// to parent when delete is called.
  BPBuffer(int size, ActualBufferPool* parent)
      : buffer_(new char[size]), parent_(parent) {
  }
  friend class ActualBufferPool;

  char* buffer_;
  ActualBufferPool* parent_;
};

////////////////////////////////////////////////////////////////////////////////
// ActualBufferPool
////////////////////////////////////////////////////////////////////////////////

class BufferPool;

/// This is what actually manages the BufferPool. Users should ignore this class
/// and use the BufferPool class instead. BPBuffer objects maintain a handle to
/// one of these. This way the BufferPool itself can be freed and the BPBuffer
/// objects still have a valid pointer. This object deletes *itself* when the
/// following 2 conditions are met:
///
/// 1) The BufferPool that owns it has called BufferPoolReleased. This is called
///    by BufferPool::~BufferPool.
/// 2) The count of outstanding BPBuffers has gone to 0.
///
/// When both of those conditions are met this calls "delete this" so there's no
/// memory leak.
///
/// Since users aren't supposed to use this class the methods here are largely
/// uncommented. See the corresponding methods on BufferPool for details.
class ActualBufferPool {
 public:
  /// Destroys the buffer pool. Note that this will crash if there are any
  /// outstanding buffers as this would indicate a memory leak.
  virtual ~ActualBufferPool();

  /// See comments on the class.
  void BufferPoolReleased();

  void GetBuffers(int num_buffers, std::vector<BPBuffer*>* buffers);
  BPBuffer* GetBuffer();

  /// Return the given buffer to the buffer pool.
  void ReturnBuffer(BPBuffer* buffer);
  template<class IteratorT>
  void ReturnBuffers(IteratorT start_it, IteratorT end_it);

  int AvailableBuffers() const;
  int OutstandingBuffers() const;

 private:
  /// Construct a buffer pool that will hold buffer_size buffers. Only BufferPool
  /// should be able to construct one of these.
  ActualBufferPool(size_t buffer_size)
      : buffer_size_(buffer_size), num_outstanding_buffers_(0),
        buffer_pool_released_(false) {}
  friend class BufferPool;

  BPBuffer* GetNewBuffer();

  /// The size of the buffers to be allocated.
  int buffer_size_;
  /// Number of buffers that have not been returned to the buffer pool.
  int num_outstanding_buffers_;
  /// Buffers that can be immediately returned to users.
  std::deque<BPBuffer*> available_buffers_;
  bool buffer_pool_released_;
  /// Protects the above data members.
  mutable boost::mutex data_tex_;
};

////////////////////////////////////////////////////////////////////////////////
// BufferPool
////////////////////////////////////////////////////////////////////////////////

/// This class maintains a pool of char* buffers. When large buffers frequently
/// need to be allocated this can become a performance bottleneck. To avoid this
/// one can use a BufferPool. A BufferPool is constructed with a single parameter
/// that indicates the size of the buffers it should hold. Users may then call
/// GetBuffers() to get a set of buffers of the specified size. GetBuffers
/// returns a vector of BPBuffer. BPBuffers return themselves to the BufferPool
/// (by calling ReturnBuffer) when they are destroyed. Thus, when the buffer is
/// no longer needed it simply gets put back in the pool and can be returned by
/// the next call to GetBuffers(). This should be much faster than searching the
/// free-store for an appropriately sized buffer.
///
/// BufferPool is thread safe.
///
/// Note that in order to make it easy to manage the lifetime of the buffer pool
/// and the buffers that come from it, it *is* safe to delete the BufferPool
/// while there are buffers from the pool still in use. See comments on the
/// private members to see how this works.
class BufferPool {
 public:
  /// Construct a buffer pool that will hold buffer_size buffers.
  BufferPool(size_t buffer_size);
  virtual ~BufferPool();

  /// On return num_buffers will be in the buffers vector.
  void GetBuffers(int num_buffers, std::vector<BPBuffer*>* buffers) {
    actual_buffer_pool_->GetBuffers(num_buffers, buffers);
  }

  /// Get a single buffer
  BPBuffer* GetBuffer() {
    return actual_buffer_pool_->GetBuffer();
  }

  /// Returns the number of buffers that are currently available in the buffer
  /// pool.  Calling GetBuffers to request more than this many buffers will
  /// require BufferPool to allocate the buffers from the free store.
  int AvailableBuffers() const {
    return actual_buffer_pool_->AvailableBuffers();
  }

  /// Returns the number of buffers the BufferPool has made available via
  /// GetBuffers that have not yet been returned via ReturnBuffer. This needs to
  /// return 0 before the destructor is called.
  int OutstandingBuffers() const {
    return actual_buffer_pool_->OutstandingBuffers();
  }

  /// Returns all the BPBuffers between start_it and end_it to the buffer pool.
  /// start_it and end_it may be any kind of iterator (including just regular
  /// pointers) as long as operator* returns a BPBuffer*.
  template<class IteratorT>
  void ReturnBuffers(IteratorT start_it, IteratorT end_it) {
    actual_buffer_pool_->ReturnBuffers(start_it, end_it);
  }

 private:
  /// This frees *itself*. See the comments on the ActualBufferPool class.
  ActualBufferPool* actual_buffer_pool_;
};


////////////////////////////////////////////////////////////////////////////////
// Template method definitions
////////////////////////////////////////////////////////////////////////////////

template<class IteratorT>
void ActualBufferPool::ReturnBuffers(IteratorT start_it, IteratorT end_it) {
  for (IteratorT i = start_it; i != end_it; ++i) {
    ReturnBuffer(*i);
  }
}

#endif
