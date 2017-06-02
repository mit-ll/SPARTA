//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A class for iterating over a collection of items in
//                     topological order. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 May 2012   omd            Original Version
//*****************************************************************


#ifndef CPP_COMMON_TOPOLOGICAL_ITERATOR_H_
#define CPP_COMMON_TOPOLOGICAL_ITERATOR_H_

#include <map>
#include <set>
/// Can't use CHECK because this is used by OrderedFunctionRegistry which is used
/// to initilialize the logging framework!
#include <cassert>

/// This is a "use once" Java style iterator that returns items in topological
/// order. To use you first add all the items via calls to Add(). Then you add
/// any ordering constraints via calls to OrderConstraint(). Finally you can
/// generate a valid ordering (there may be more than one) by iterating with
/// HasNext and Next().
///
/// Example:
///
/// ToplologicalIterator<char> topo;
/// topo.Add('A');
/// topo.Add('B');
/// topo.Add('C');
///
/// // B must be generated before C
/// topo.OrderConstraint('B', 'C');
/// /// And B must be generate before A
/// topo.OrderConstraint('B', 'A');
///
/// // This will generate either (B, C, A) or (B, A, C) - either are valid
/// orderings.
///
/// while (topo.HasNext()) {
///   cout << topo.Next();
/// }
///
/// At this point the iterator is useless - it consumes its own data structures
/// in the process of generating. The main use case for this is ordering static
/// and global variable initialization and destructions so this efficency
/// tradeoff makes sense.
template<class T>
class TopologicalIterator {
 public:
  TopologicalIterator() {}
  virtual ~TopologicalIterator() {}

  /// Add an item to the set of items to be generated.
  void Add(T item);
  /// Add a constrinat that says before must be generated before after. Note that
  /// both before and after must have been previously added via calls to Add().
  void OrderConstraint(T before, T after);
  
  /// Java style iterator. Note that iteration is "destructive" - the 1st call to
  /// Next() modifies the underlying data so you can only iterate through things
  /// once!
  bool HasNext() const;
  T Next();

 private:
  std::set<T> ready_;
  std::map<T, std::set<T> > item_to_deps_;
  std::map<T, std::set<T> > dep_to_items_;
};


////////////////////////////////////////////////////////////////////////////////
// Implementation.
////////////////////////////////////////////////////////////////////////////////

template<class T>
void TopologicalIterator<T>::Add(T item) {
  assert(item_to_deps_.find(item) == item_to_deps_.end());
  ready_.insert(item);
}

template<class T>
void TopologicalIterator<T>::OrderConstraint(T before, T after) {
  // before is not ready as it can't be generated until after has been
  // generated.
  ready_.erase(after);
  item_to_deps_[after].insert(before);
  dep_to_items_[before].insert(after);
}

template<class T>
bool TopologicalIterator<T>::HasNext() const {
  assert(ready_.size() > 0 || item_to_deps_.size() == 0);
  return ready_.size() > 0;
}

template<class T>
T TopologicalIterator<T>::Next() {
  assert(ready_.size() > 0);
  // Pull an item out of the set of items that are ready
  typename std::set<T>::iterator i = ready_.begin();
  T value = *i;
  ready_.erase(i);
  // Find all of the items that have a dependancy on this item and remove that
  // dependancy. If that item has no more dependancies then we can add it to the
  // set of items that are ready.
  if (dep_to_items_.find(value) != dep_to_items_.end()) {
    typename std::set<T>::iterator items_that_depend_it;
    std::set<T>& set_of_items_that_depend = dep_to_items_[value];
    for (items_that_depend_it = set_of_items_that_depend.begin();
         items_that_depend_it != set_of_items_that_depend.end();
         ++items_that_depend_it) {
      assert(item_to_deps_.find(*items_that_depend_it) != item_to_deps_.end());
      // Get the set of things that *items_that_depend_it depends on and remove
      // value from that set as it has now been generated.
      std::set<T>& item_dep_set = item_to_deps_[*items_that_depend_it];
      item_dep_set.erase(value);
      // If there are no more dependacies for this item add it to the set of
      // items that are ready to be generated.
      if (item_dep_set.size() == 0) {
        ready_.insert(*items_that_depend_it);
        item_to_deps_.erase(*items_that_depend_it);
      }
    }
  }
  return value;
}


#endif
