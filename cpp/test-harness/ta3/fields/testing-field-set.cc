//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of classes in testing-field-set.h 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Jan 2013   omd            Original Version
//*****************************************************************

#include "testing-field-set.h"

#include <sstream>

#include "common/string-algo.h"
#include "equi-probable-closed-set-field.h"

using std::string;

FieldBase* EquiProbableFakeFileFactory(
    const std::string& name, const std::string& config) {
  std::stringstream values_file;
  auto values = Split(config, ' ');
  for (auto value : values) {
    values_file << value << "\n";
  }
  return new EquiProbableClosedSetField(name, &values_file);
}
