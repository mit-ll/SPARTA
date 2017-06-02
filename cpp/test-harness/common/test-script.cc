//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of TestScript 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 20 Sep 2012   omd            Original Version
//*****************************************************************

#include "test-script.h"

#include <boost/bind.hpp>
#include <boost/thread.hpp>

Future<bool> TestScript::RunInThread() {
  Future<bool> done_future;

  boost::thread thread(
      boost::bind(&TestScript::Run, this, done_future));
  return done_future;
}
