//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Unit tests for BufferPool 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Aug 2012   omd            Original Version
//*****************************************************************

#define BOOST_TEST_MODULE BufferPoolTest

#include "test-init.h"

#include "buffer-pool.h"

#include <memory>
#include <vector>

using namespace std;

BOOST_AUTO_TEST_CASE(BufferPoolWorks) {
  const int kBufferSize = 107;
  BufferPool bp(kBufferSize);

  vector<BPBuffer*> buffers;

  const int kNumBuffers = 10;
  bp.GetBuffers(kNumBuffers, &buffers);

  BOOST_REQUIRE_EQUAL(buffers.size(), kNumBuffers);
  BOOST_CHECK_EQUAL(bp.OutstandingBuffers(), kNumBuffers);
  // Write kBufferSize characters to each buffer to make sure they do, in fact,
  // contain valid memory.
  for (int i = 0; i < kNumBuffers; ++i) {
    // Just write 'a' to each character. Doesn't matter what we write here...
    for (int j = 0; j < kBufferSize; ++j) {
      buffers[i]->buffer()[j] = 'a';
    }
  }

  // Free the buffers. They should then all be returned the pool.
  vector<BPBuffer*>::iterator b_it;
  int num_outstanding_buffers = kNumBuffers;
  for (b_it = buffers.begin(); b_it != buffers.end(); ++b_it) {
    delete *b_it;
    --num_outstanding_buffers;
    BOOST_CHECK_EQUAL(bp.OutstandingBuffers(), num_outstanding_buffers);
  }

  // BufferPool might pre-allocate some buffers, but at this point all the
  // buffers were returned should be avaialable so there should be at least
  // kNumBuffers available.
  BOOST_CHECK_GE(bp.AvailableBuffers(), kNumBuffers);
}

// Similar to the above, but make sure the version that returns a single buffer
// works as well.
BOOST_AUTO_TEST_CASE(GetBufferWorks) {
  const int kBufferSize = 803;
  BufferPool bp(kBufferSize);

  std::auto_ptr<BPBuffer> buffer(bp.GetBuffer());
  BOOST_CHECK_EQUAL(bp.OutstandingBuffers(), 1);
  // Write kBufferSize bytes into the buffer to make sure the memory is valid.
  for (int i = 0; i < kBufferSize; ++i) {
    buffer->buffer()[i] = 'a';
  }

  std::auto_ptr<BPBuffer> buffer2(bp.GetBuffer());
  BOOST_CHECK_EQUAL(bp.OutstandingBuffers(), 2);
  // Write kBufferSize bytes into the buffer to make sure the memory is valid.
  for (int i = 0; i < kBufferSize; ++i) {
    buffer2->buffer()[i] = 'a';
  }

  buffer.reset();
  BOOST_CHECK_EQUAL(bp.OutstandingBuffers(), 1);
  buffer2.reset();
  BOOST_CHECK_EQUAL(bp.OutstandingBuffers(), 0);
}

BOOST_AUTO_TEST_CASE(IteratorReturnBuffersWorks) {
  const int kBufferSize = 20;
  const int kNumBuffers = 18;
  BufferPool bp(kBufferSize);

  vector<BPBuffer*> buffers;
  bp.GetBuffers(kNumBuffers, &buffers);

  BOOST_REQUIRE_EQUAL(buffers.size(), kNumBuffers);
  BOOST_CHECK_EQUAL(bp.OutstandingBuffers(), kNumBuffers);

  const int kBuffersToReturnInFirstBatch = 7;
  vector<BPBuffer*>::iterator first_batch_end =
      buffers.begin() + kBuffersToReturnInFirstBatch;

  // Return the 1st kBuffersToReturnInFirstBatch buffers via iterators.
  bp.ReturnBuffers(buffers.begin(), first_batch_end);
  BOOST_CHECK_EQUAL(bp.OutstandingBuffers(),
                    kNumBuffers - kBuffersToReturnInFirstBatch);

  // Return the remaining buffers.
  bp.ReturnBuffers(first_batch_end, buffers.end());
  BOOST_CHECK_EQUAL(bp.OutstandingBuffers(), 0);
}

// Check that we can safely delete the BufferPool object before all the
// BPBuffers are deleted without having segfaults or memory leaks.
BOOST_AUTO_TEST_CASE(BufferPoolLifetimeWorks) {
  const int kBufferSize = 100;
  std::auto_ptr<BufferPool> pool(new BufferPool(kBufferSize));
  
  std::auto_ptr<BPBuffer> b1(pool->GetBuffer());
  std::auto_ptr<BPBuffer> b2(pool->GetBuffer());

  strcpy(b1->buffer(), "Hello");
  BOOST_CHECK_EQUAL(b1->buffer(), "Hello");

  // Return b2 but not b1
  b2.reset();

  // Now free the BufferPool even though b1 is still allocated.
  pool.reset();

  // And make sure b1 is still OK.
  BOOST_CHECK_EQUAL(b1->buffer(), "Hello");

  // Now free b1. It this should not cause an issue.
  b1.reset();
}
