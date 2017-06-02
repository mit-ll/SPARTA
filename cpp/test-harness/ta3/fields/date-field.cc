//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of DateField 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jan 2013   omd            Original Version
//*****************************************************************

#include "date-field.h"

using std::string;

DateField::DateField(
    const string& name, const string& date_start, const string& date_end)
    : FieldBase(name, "Date") {
  struct tm parsed_time;

  memset(&parsed_time, 0, sizeof(struct tm));
  char* res = strptime(date_start.c_str(), "%Y-%m-%d", &parsed_time);
  CHECK(res != nullptr) << "Error converting start date: " << date_start;
  start_t_ = mktime(&parsed_time);

  memset(&parsed_time, 0, sizeof(struct tm));
  res = strptime(date_end.c_str(), "%Y-%m-%d", &parsed_time);
  CHECK(res != nullptr) << "Error converting start date: " << date_end;
  end_t_ = mktime(&parsed_time);
}

// This computes the number of unique dates we could generate. This isn't a
// terribly expensive computation, but it's not cheap either. We might want to
// consider caching thsi result in the future.
int DateField::NumValues() const {
  // mktime doesn't alter the struct tm passed to it but it's not declared that
  // way since it's an ancient C function. Hence the const-cast.
  long int num_secs = end_t_ - start_t_;

  int num_days = num_secs / kNumSecPerDay_;

  return num_days;
}

char* DateField::RandomValue(size_t max_char, char* output) const {
  CHECK(max_char >= MaxLength());


  std::uniform_int_distribution<> dist_(0, NumValues() - 1);
  int num_days_since_start = dist_(rng_);
  
  time_t generated_date_sec = start_t_ + num_days_since_start * kNumSecPerDay_;
  DCHECK(generated_date_sec < end_t_);

  struct tm* gen_date = localtime(&generated_date_sec);
  CHECK(gen_date != nullptr);
  size_t num_output_bytes = strftime(output, max_char, "%Y-%m-%d", gen_date);

  // -1 here because the value returned by strftime does not include the null
  // terminating byte.
  CHECK(num_output_bytes == (MaxLength() - 1));

  return output + num_output_bytes;
}

char* DateField::RandomValueExcluding(
    const std::set<std::string>& exclude, size_t max_char, char* output) const {
  char* end_ptr;
  while (true) {
    end_ptr = RandomValue(max_char, output);
    string generated(output, end_ptr - output);
    if (exclude.find(generated) == exclude.end()) {
      break;
    }
  }
  return end_ptr;
}
