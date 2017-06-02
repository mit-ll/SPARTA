//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        For fields where all values are equally probable and
//                     there are only a finite set of possible values. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 21 Jan 2013   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA3_FIELDS_EQUI_PROBABLE_CLOSED_SET_FIELD_H_
#define CPP_TEST_HARNESS_TA3_FIELDS_EQUI_PROBABLE_CLOSED_SET_FIELD_H_

#include "field-base.h"

#include <iostream>
#include <random>
#include <string>

/// A FieldBase subclass for fields with a finite set of equally probably values.
class EquiProbableClosedSetField : public FieldBase {
 public:
  /// Constructor. name is the name of the field, and values_file is a istream
  /// that contains one potential field value per line.
  EquiProbableClosedSetField(
      const std::string& name, std::istream* values_file);

  virtual ~EquiProbableClosedSetField() {}

  virtual void SetSeed(int seed) {
    rng_.seed(seed);
  }

  virtual char* RandomValue(size_t max_char, char* output) const;
  virtual char* RandomValueExcluding(
      const std::set<std::string>& exclude,
      size_t max_char, char* output) const;

  virtual size_t MaxLength() const {
    return max_length_;
  }

  virtual int NumValues() const {
    return values_.size();
  }

 private:
  size_t RandomIndex() const;

  std::vector<std::string> values_;
  size_t max_length_;
  mutable std::mt19937 rng_;
  std::unique_ptr<std::uniform_int_distribution<> > uniform_dist_;
};

#endif
