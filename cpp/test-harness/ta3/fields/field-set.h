//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        The set of fields being used in a test. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 22 Jan 2013   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA3_FIELDS_FIELD_SET_H_
#define CPP_TEST_HARNESS_TA3_FIELDS_FIELD_SET_H_

#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "field-base.h"

/// Class that represents a set of fields.
class FieldSet {
 public:
  FieldSet();
  virtual ~FieldSet();

  /// Takes ownership of the field.
  void AddField(std::unique_ptr<FieldBase> field);

  /// The number of fields in the set.
  size_t Size() const {
    return fields_.size();
  }

  /// Returns the i'th field. This retains ownership of the return field.
  const FieldBase* Get(size_t i) const;

  /// Sets the random number generation seed for all fields in the set. Must be
  /// called after all the fields have been added to the set.
  void SetSeed(int seed);

  /// Returns the sum of MaxLength() for all the fields in the set. Note that
  /// this is an O(n) call where n == the number of fields. It might be wise to
  /// cache the return value.
  size_t TotalMaxLength() const;

  /// Reads a file with lines like:
  ///
  /// <name> <factory> <config>
  ///
  /// where <name> is a field name, <factory> is the name of a FieldFactory (as
  /// per SetupFactories()), and <config> is a string that is meaningful to the
  /// factory on that line. Lines starting with '#' are ignored as comments as
  /// are blank lines.
  ///
  /// For each line read the corresponding factory is called and the newly
  /// constructed field is appended to the FieldSet.
  void AppendFromFile(std::istream* fields_file);

 protected:
  /// A FieldFacotory is called with a string indicating the name of the field
  /// (e.g. fname or address) and a configuration string. The meaning and format
  /// of the configuration string is factory specific.
  typedef std::function<FieldBase* (const std::string&, const std::string&)>
      FieldFactory;

  /// Generally adding factories happens in the constructor via a call to
  /// SetupFactories(). However, we sometimes want to add additional factories
  /// for unit testing so this is protected.
  void AddFieldFactory(const std::string& factory_name, FieldFactory factory);
 private:
  /// Called by the constructor to set up field factories.
  virtual void SetupFactories();

  std::vector<FieldBase*> fields_;
  /// Map from factory name to a FieldFactory.
  ///
  /// TODO(odain) This should probably be a static map shared by all instances of
  /// this class. However, I think in pretty much all our applicatons there will
  /// be only a few of these and this is faster to code up...
  std::map<std::string, FieldFactory> factory_map_;
};

#endif
