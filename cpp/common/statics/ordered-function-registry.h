//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Allows the user to register a set of functions and a set
//                     of dependancies between those functions and have them run
//                     in the prescribed order. Used to run static initializers
//                     and destructors in a prescribed order.
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_STATICS_ORDERED_FUNCTION_REGISTRY_H_
#define CPP_COMMON_STATICS_ORDERED_FUNCTION_REGISTRY_H_

#include <boost/function.hpp>

#include <list>
#include <map>
#include <string>
#include <utility>

class OrderedFunctionRegistry {
 public:
  OrderedFunctionRegistry() {}

  void AddFunction(const std::string& name, boost::function<void ()> function) {
    functions_to_run_.insert(std::make_pair(name, function));
  }

  void OrderConstraint(const std::string& before, const std::string& after);

  void RunFunctions();
 private:
  typedef boost::function<void ()> VoidFunction;

  /// We can't just use std::pair as operator< isn't defined for boost::function
  /// so we create a struct that's essentially just pair<>.
  struct NamedFunction {
    NamedFunction(const std::string& name, VoidFunction function)
        : name_(name), function_(function) {}
    NamedFunction(std::pair<const std::string, VoidFunction> nf_pair)
        : name_(nf_pair.first), function_(nf_pair.second) {}

    bool operator<(const NamedFunction& other) const {
      return name_ < other.name_;
    }
    const std::string name_;
    VoidFunction function_;
  };

  std::map<std::string, VoidFunction> functions_to_run_;
  /// The pairs indicate that ->first must be run before ->second.
  std::list<std::pair<std::string, std::string> > function_order_constraints_;
};

#endif
