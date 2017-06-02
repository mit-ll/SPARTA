//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of stuff in statics.h 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 May 2012   omd            Original Version
//*****************************************************************

#include "statics/ordered-function-registry.h"

#include <functional>
#include <cstdlib>

using std::string;

// In order to get a reliable singleton for the finalizer and initializer
// OrderedFunctionRegistry objects we use the static function variable trick.

static OrderedFunctionRegistry* InitializerRegistry() {
  static OrderedFunctionRegistry registry; 
  return &registry;
}

static OrderedFunctionRegistry* FinalizerRegistry() {
  static OrderedFunctionRegistry registry; 
  return &registry;
}

static void RunFinalizers() {
  FinalizerRegistry()->RunFunctions();
}

void Initialize() {
  // Run all the initializer functions.
  InitializerRegistry()->RunFunctions();
  
  // Arrange to have all the finalizers run at program exit.
  atexit(&RunFinalizers);
}

bool AddInitializer(const string& name,
                    std::function<void ()> init_function) {
  InitializerRegistry()->AddFunction(name, init_function);
  return true;
}

bool OrderInitializers(const string& first, const string& second) {
  InitializerRegistry()->OrderConstraint(first, second);
  return true;
}

bool AddFinalizer(const string& name,
                  std::function<void ()> finalize_function) {
  FinalizerRegistry()->AddFunction(name, finalize_function);
  return true;
}

bool OrderFinalizers(const string& first, const string& second) {
  FinalizerRegistry()->OrderConstraint(first, second);
  return true;
}
