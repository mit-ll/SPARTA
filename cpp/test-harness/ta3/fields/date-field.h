//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        A field that holds dates 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jan 2013   omd            Original Version
//*****************************************************************


#ifndef CPP_TEST_HARNESS_TA3_FIELDS_DATE_FIELD_H_
#define CPP_TEST_HARNESS_TA3_FIELDS_DATE_FIELD_H_

#include "field-base.h"

#include <ctime>
#include <random>
#include <string>

class DateField : public FieldBase {
 public:
  /// Constructs a field that will randomly generate dates in [date_start,
  /// date_end). The format of date_start and date_end must be YYYY-MM-DD.
  DateField(const std::string& name,
            const std::string& date_start,
            const std::string& date_end);

  virtual ~DateField() {}

  virtual void SetSeed(int seed) {
    rng_.seed(seed);
  }

  virtual char* RandomValue(size_t max_char, char* output) const;
  virtual char* RandomValueExcluding(
      const std::set<std::string>& exclude,
      size_t max_char, char* output) const;

  virtual size_t MaxLength() const {
    /// The length of YYYY-MM-DD\0. Generally fields don't null terminate their
    /// output, but strftime does so we "lie" here and say we might need 1 more
    /// character than we really do.
    return 11;
  }

  virtual int NumValues() const;

 private:
  time_t start_t_;
  time_t end_t_;
  mutable std::mt19937 rng_;

  static const int kNumSecPerDay_ = 24 * 60 * 60;
};

#endif
