//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Simple memory pool for an object's operator::new 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 28 Aug 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_FIXED_SIZE_MEMORY_POOL_H_
#define CPP_COMMON_FIXED_SIZE_MEMORY_POOL_H_

#include <deque>

/// Sometimes we have to allocate and free an object which has a fixed size over
/// and over. Doing that with standard operator new and delete can be expensive
/// as the free stored must be searched for an appropriate sized block. Instead,
/// it is often useful to overload operator new and delete for such objects so
/// they get their memory from a pool of appropriate sized blocks. Since all
/// blocks in the pool are the same size there is no need to search and there
/// isn't any heap fragmentation; this can lead to substantial speedups.
///
/// This class is intended to make overloading operators new and delete easier in
/// such cases. Operator new would get memory by calling GetMemory and operator
/// delete would return the memory to the pool by calling ReturnMemory.
class FixedSizeMemoryPool {
 public:
  FixedSizeMemoryPool(int item_size) : item_size_(item_size) {}
  virtual ~FixedSizeMemoryPool() {
    for (std::deque<void*>::iterator i = memory_pool_.begin();
         i != memory_pool_.end(); ++i) {
      delete[] reinterpret_cast<char*>(*i);
    }
  }

  void* GetMemory() {
    boost::lock_guard<boost::mutex> l(memory_pool_mutex_);
    if (memory_pool_.size() > 0) {
      void* to_return = memory_pool_.back();
      memory_pool_.pop_back();
      return to_return;
    } else {
      return reinterpret_cast<void*>(new char[item_size_]);
    }
  }

  void ReturnMemory(void* mem) {
    boost::lock_guard<boost::mutex> l(memory_pool_mutex_);
    memory_pool_.push_back(mem);
  }

 private:
  int item_size_;
  boost::mutex memory_pool_mutex_;
  std::deque<void*> memory_pool_;
};


#endif
