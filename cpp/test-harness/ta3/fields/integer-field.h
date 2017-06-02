//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A field that generates value from a range of integers. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jan 2013   omd            Original Version
//*****************************************************************

#ifndef CPP_TEST_HARNESS_TA3_FIELDS_INTEGER_FIELD_H_
#define CPP_TEST_HARNESS_TA3_FIELDS_INTEGER_FIELD_H_

#include "field-base.h"

#include <string>
#include <random>

/// A field whose values are all the integers (represented as base 10 strings
/// since all field values are strings) in [start, end). The constructor take a
/// printf-style format string that specifies how the generated values are to be
/// represented.
class IntegerField : public FieldBase {
 public:
  /// Will generate integers in [start, end).
  IntegerField(const std::string& name, const std::string& format_string,
               int start, int end);
  virtual void SetSeed(int seed) {
    rng_.seed(seed);
  }

  virtual char* RandomValue(size_t max_char, char* output) const;
  virtual char* RandomValueExcluding(
      const std::set<std::string>& exclude,
      size_t max_char, char* output) const;

  /// This assumes that either the maximum or the minimum value, when formatted
  /// according to the format string, will have the maximum length. If that's not
  /// correct...
  virtual size_t MaxLength() const {
    return max_length_;
  }

  virtual int NumValues() const {
    return end_ - start_;
  }

  int MaxValue() const {
    return end_;
  }

  int MinValue() const {
    return start_;
  }

 private:
  std::string format_string_;
  int start_;
  int end_;
  int max_length_;

  mutable std::mt19937 rng_;
  mutable std::uniform_int_distribution<> dist_;
};


#endif
