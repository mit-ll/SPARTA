//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Typedef's for common types. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_TYPES_H_
#define CPP_COMMON_TYPES_H_

#include <memory>
#include <thread>
#include <string>
#include <mutex>

/// Data to be sent to MySQL must be copied into pseudo-closures and then
/// executed on a thread and the results must make their way from the thread to
/// the results stream. Copying the data each time it moves is expensive and
/// maintaining ownership semantics is difficult so we use a shared pointer to
/// manage this kind of data.
///
/// Note that both raw and line data are held in a string. STL strings can
/// hold an arbitrary array of bytes, include arrays that contain the '\0'
/// character, so this works fine.
typedef std::shared_ptr<std::string> SharedData;
typedef std::lock_guard<std::mutex> MutexGuard;
typedef std::unique_lock<std::mutex> UniqueMutexGuard;

#endif
