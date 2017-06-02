//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Collection of routines for handling static (and global)
//                     data. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 May 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_COMMON_STATICS_H_
#define CPP_COMMON_STATICS_H_

#include <functional>
#include <string>

/// Due to the "static initializer ordering fiasco" users should *never*
/// use globals or statics of non-POD type. Instead, users should have pointers
/// to the complex types and then use the functions and macros below to arrange
/// for the objects to be constructed and, optionally, destroyed. The only
/// exception to the non-POD data types is that std::auto_ptr is allowed in order
/// to handle destruction although the AddFinalizer() function and associated
/// macros works as well.

/// IMPORTANT: This should be the 1st line of every main()!!! It takes care of
/// initializing all our static objects. Without it things like OutputHandler and
/// the logging framework will not work!!
void Initialize();

/// In the following there are function/macro pairs. Since you can't call
/// functions at global scope unless you're doing so to initialize a global
/// variable you generally can't directly use the function version and instead
/// must use the hacky macro version. Such is life ;) Note that the functions
/// return a bool just to make the macros work!
#define CONCAT_IMPL(x, y) x##y
#define MACRO_CONCAT(x, y) CONCAT_IMPL(x, y)

/// Make sure the following function is called during initialization. The first
/// parameter gives the function an arbitrary name. If there are initialization
/// order dependancies between this and another function you can call
/// OrderInitializers() using these names to enforce the ordering.
bool AddInitializer(const std::string& name,
                    std::function<void ()> init_function);

#define ADD_INITIALIZER(A, B) \
   static bool MACRO_CONCAT( __init_variable_, __COUNTER__ ) = AddInitializer((A), (B))

/// Make sure the initializer named first runs before the initializer named
/// second.
bool OrderInitializers(const std::string& first,
                       const std::string& second);

#define ORDER_INITIALIZERS(A, B) \
   static bool MACRO_CONCAT( __init_variable_, __COUNTER__ ) = OrderInitializers((A), (B))

/// Like AddInitializer and OrderInitializers but for functions that should run
/// after main() exits. These functions are guaranteed to run exactly once at the
/// end of the program.
bool AddFinalizer(const std::string& name,
                  std::function<void ()> finalize_function);

bool OrderFinalizers(const std::string& first, const std::string& second);

#define ADD_FINALIZER(A, B) \
    static bool MACRO_CONCAT( __init_variable_ , __COUNTER__ ) = \
      AddFinalizer((A), (B))

#endif
