//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of BufferPool and BPBuffer 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Aug 2012   omd            Original Version
//*****************************************************************

#include "buffer-pool.h"

typedef boost::lock_guard<boost::mutex> MutexGuard;

////////////////////////////////////////////////////////////////////////////////
// BPBuffer
////////////////////////////////////////////////////////////////////////////////

BPBuffer::~BPBuffer() {
  parent_->ReturnBuffer(this);
}


////////////////////////////////////////////////////////////////////////////////
// BufferPool
////////////////////////////////////////////////////////////////////////////////

BufferPool::BufferPool(size_t buffer_size)
  : actual_buffer_pool_(new ActualBufferPool(buffer_size)) {
}

BufferPool::~BufferPool() {
  actual_buffer_pool_->BufferPoolReleased();
}

////////////////////////////////////////////////////////////////////////////////
// ActualBufferPool
////////////////////////////////////////////////////////////////////////////////

ActualBufferPool::~ActualBufferPool() {
  MutexGuard g(data_tex_);
  CHECK(num_outstanding_buffers_ == 0)
      << "ActualBufferPool destructor called with "
      << num_outstanding_buffers_
      << " buffers outstanding.";
 
  std::deque<BPBuffer*>::iterator i;
  for (i = available_buffers_.begin(); i != available_buffers_.end(); ++i) {
    (*i)->FreeMemory();
    // We cast the pointer to a void* before freeing it so that
    // BPBuffer::~BPBuffer doesn't run - if it did it would try to return the
    // memory back to this pool again. Also - the memory was allocated as a
    // void* and the object constructed via placement new so that's not the
    // right way to free it.
    char* memory = reinterpret_cast<char*>(*i);
    delete[] memory;
  }
}

void ActualBufferPool::BufferPoolReleased() {
  data_tex_.lock();
  buffer_pool_released_ = true;
  if (num_outstanding_buffers_ == 0) {
    data_tex_.unlock();
    delete this;
  } else {
    data_tex_.unlock();
  }
}

BPBuffer* ActualBufferPool::GetNewBuffer() {
  // As noted in the destructor, we can't call either "delete buffer" or
  // "::delete buffer" on the BPBuffer objects as that would cause their
  // destructors to run. Instead we allocate via placement new.
  char* memory = new char[sizeof(BPBuffer)];
  BPBuffer* buffer =
      new(reinterpret_cast<void*>(memory)) BPBuffer(buffer_size_, this);
  return buffer;
}

void ActualBufferPool::ReturnBuffer(BPBuffer* buffer) {
  data_tex_.lock();
  --num_outstanding_buffers_;
  DCHECK(num_outstanding_buffers_ >= 0);
  available_buffers_.push_back(buffer);
  if (buffer_pool_released_ && num_outstanding_buffers_ == 0) {
    data_tex_.unlock();
    delete this;
  } else {
    data_tex_.unlock();
  }
}

void ActualBufferPool::GetBuffers(int num_buffers,
                            std::vector<BPBuffer*>* buffers) {
  buffers->reserve(num_buffers);
  buffers->clear();

  MutexGuard g(data_tex_);
  if (available_buffers_.size() < static_cast<size_t>(num_buffers)) {
    LOG(DEBUG) << "User requested " << num_buffers << " but ActualBufferPool "
        << "only had " << available_buffers_.size() << " available."
        << " Allocating " << num_buffers - available_buffers_.size()
        << " new buffers.";
    while (available_buffers_.size() < static_cast<size_t>(num_buffers)) {
      available_buffers_.push_back(GetNewBuffer());
    }
  }

  for (int i = 0; i < num_buffers; ++i) {
    BPBuffer* buffer = available_buffers_.back();
    available_buffers_.pop_back();
    buffers->push_back(buffer);
    ++num_outstanding_buffers_;
  }
}

BPBuffer* ActualBufferPool::GetBuffer() {
  MutexGuard g(data_tex_);
  ++num_outstanding_buffers_;
  if (available_buffers_.size() == 0) {
    LOG(DEBUG) << "User requested a buffer but ActualBufferPool had "
        << "no available buffers. Allocating one.";
    return GetNewBuffer();
  } else {
    BPBuffer* buffer = available_buffers_.back();
    available_buffers_.pop_back();
    return buffer;
  }
}

int ActualBufferPool::AvailableBuffers() const {
  MutexGuard g(data_tex_);
  return available_buffers_.size();
}

int ActualBufferPool::OutstandingBuffers() const {
  MutexGuard g(data_tex_);
  return num_outstanding_buffers_;
}
