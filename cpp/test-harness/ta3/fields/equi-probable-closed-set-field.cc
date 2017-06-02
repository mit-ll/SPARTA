//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of EquiProbableClosedSetField 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Jan 2013   omd            Original Version
//*****************************************************************

#include "equi-probable-closed-set-field.h"

#include <algorithm>
#include <cstring>

using std::string;

EquiProbableClosedSetField::EquiProbableClosedSetField(
    const std::string& name, std::istream* values_file)
    : FieldBase(name, "EquiProbableClosedSet"), max_length_(0) {
  while (values_file->good()) {
    string cur_val;
    getline(*values_file, cur_val);
    if (!cur_val.empty()) {
      max_length_ = std::max(max_length_, cur_val.size());
      values_.push_back(cur_val);
    }
  }
  CHECK(values_file->eof()) << "Error reading values for " << name;
  std::sort(values_.begin(), values_.end());
  uniform_dist_.reset(new std::uniform_int_distribution<>(
          0, values_.size() - 1));
}

size_t EquiProbableClosedSetField::RandomIndex() const {
  size_t index = (*uniform_dist_)(rng_);
  DCHECK(index >= 0);
  DCHECK(index < values_.size());
  return index;
}

char* EquiProbableClosedSetField::RandomValue(
    size_t max_char, char* output) const {
  CHECK(max_char >= MaxLength());
  size_t index = RandomIndex();
  
  const string& val = values_[index];
  DCHECK(max_char >= val.size()) << "Error! '" << val << "' is "
      << val.size() << " characters long, but max_char = " << max_char
      << " and MaxLength() = " << MaxLength();
  std::memcpy(output, val.data(), val.size());
  return output + val.size();
}

// TODO(odain) This currently generates values in a loop until it's generated
// one that's not excluded. That's fine if we won't ever have a situation where
// the majority of the values have been excluded. If that happens we'll need to
// code up a smarter algorithm or this could take a long time.
char* EquiProbableClosedSetField::RandomValueExcluding(
    const std::set<std::string>& exclude,
    size_t max_char, char* output) const {
  CHECK(max_char <= MaxLength());
  size_t index = RandomIndex();
  while (exclude.find(values_[index]) != exclude.end()) {
    index = RandomIndex();
  }

  const string& val = values_[index];
  DCHECK(max_char >= val.size());
  std::memcpy(output, val.data(), val.size());
  return output + val.size();
}
