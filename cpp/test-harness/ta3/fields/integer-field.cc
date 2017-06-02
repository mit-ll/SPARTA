//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of IntegerField 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 31 Jan 2013   omd            Original Version
//*****************************************************************

#include "integer-field.h"

#include <cstring>
#include <stdio.h>

using std::string;

IntegerField::IntegerField(
    const string& name, const string& format_string, int start, int end)
    : FieldBase(name, "Integer"), format_string_(format_string), start_(start),
      end_(end), dist_(start, end - 1) {
  CHECK(end_ > start_);
  
  // Note that asprintf is a GNU-C extension. We could also use boost::format
  // here or just allocate a really big buffer and assume it's big enough.
  char* output;
  int l_end = asprintf(&output, format_string.c_str(), end_ - 1);
  if (l_end == -1) {
    LOG(FATAL) << "Error trying to convert " << end_ - 1
        << " with format string: " << format_string;
  }
  DCHECK(l_end > 0);
  free(output);

  int l_start = asprintf(&output, format_string.c_str(), start);
  if (l_start == -1) {
    LOG(FATAL) << "Error trying to convert " << start_
        << " with format string: " << format_string;
  }
  DCHECK(l_start > 0);
  free(output);
  max_length_ = std::max(l_start, l_end);
}

char* IntegerField::RandomValue(size_t max_char, char* output) const {
  CHECK(max_char >= MaxLength());
  int value = dist_(rng_);
  // The RandomValue method does not append a null terminator but snprintf does.
  // So we need to include space for it and then copy everything except the null
  // terminator to output.
  char buffer[MaxLength() + 1];
  int result_size = snprintf(buffer, MaxLength() + 1,
                             format_string_.c_str(), value);
  memcpy(output, buffer, result_size);
  return output + result_size;
}

char* IntegerField::RandomValueExcluding(
    const std::set<std::string>& exclude, size_t max_char, char* output) const {
  while (true) {
    char* end_char = RandomValue(max_char, output);
    if (exclude.find(string(output, end_char - output)) == exclude.end()) {
      return end_char;
    }
  }
}


