//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Command to spawn the system under test. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 23 Sep 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_COMMON_SPAWN_SUT_H_
#define CPP_TEST_HARNESS_COMMON_SPAWN_SUT_H_

#include <string>
#include <fstream>
#include <functional>

#include "common/event-loop.h"

class SUTProtocolStack;

/// The pipe_fun argument is a function that is intended to take two pointers to
/// file handles. Upon completion, pipe_fun should set the two pointers to
/// valid file handles, whether by spawning a process or by creating standalone
/// pipes.
void SpawnSUT(
    std::function<int(int*, int*)> pipe_fun,
    const std::string& debug_directory, bool unbuffered,
    EventLoop* event_loop, std::ofstream* stdout_log,
    std::ofstream* stdin_log, SUTProtocolStack* protocol_stack,
    ReadEventLoop::EOFCallback sut_terminated_cb);

#endif
