//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Subclass of FieldSet and a field factories handy for unit
//                     testing. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 28 Jan 2013   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA3_FIELDS_TESTING_FIELD_SET_H_
#define CPP_TEST_HARNESS_TA3_FIELDS_TESTING_FIELD_SET_H_

#include <string>

#include "common/string-algo.h"
#include "field-base.h"
#include "field-set.h"

/// A factory that whose config string is assumed to be a space-separated list of
/// values for the field. This will construct a istringstream using this list and
/// pass that to the constructor for the field.
FieldBase* EquiProbableFakeFileFactory(
    const std::string& name, const std::string& config);

class TestingFieldSet : public FieldSet {
 public:
  TestingFieldSet() {
    AddFieldFactory("EQFakeFactory", &EquiProbableFakeFileFactory);
  }
};

#endif
