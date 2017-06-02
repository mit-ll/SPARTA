//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implementation of string algorithms 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 May 2012   omd            Original Version
//*****************************************************************

#include "string-algo.h"

#include <cstring>
#include <limits>
#include <sstream>

using std::string;
using std::vector;

void Split(const string& source, char delimiter, vector<string>* result, 
           int max_results) {
  size_t delim_idx = source.find(delimiter);
  size_t start_idx = 0;
  while (delim_idx != string::npos) {
    if (max_results >= 0 && result->size() >= (size_t)max_results) {
      break;
    }
    result->push_back(source.substr(start_idx, delim_idx - start_idx));
    start_idx = delim_idx + 1;
    delim_idx = source.find(delimiter, start_idx);
  }
  result->push_back(source.substr(start_idx));
}

char* StrDup(const char* src) {
  int str_size = strlen(src);
  char* result = new char[str_size + 1];
  strncpy(result, src, str_size + 1);
  return result;
}

string itoa(int x) {
  // TODO(odain) this may not be the most efficient way to do this. Consider
  // other approaches if this seems slow.
  std::ostringstream out;
  out << x;
  return out.str();
}

void ToUpper(string* str) {
  string::iterator i;
  for (i = str->begin(); i != str->end(); ++i) {
    if (*i >= 'a' && *i <= 'z') {
      *i = *i + ('A' - 'a');
    }
  }
}

void ToLower(std::string* str) {
  string::iterator i;
  for (i = str->begin(); i != str->end(); ++i) {
    if (*i >= 'A' && *i <= 'Z') {
      *i = *i - ('A' - 'a');
    }
  }
}

void Join(const vector<string>& data, const string& delim, string* result) {
  if (data.size() == 0) {
    return;
  }

  int total_size = 0;
  for (size_t i = 0; i < data.size(); ++i) {
    total_size += data[i].size();
  }

  total_size += (data.size() - 1) * delim.size();

  result->reserve(total_size);

  bool need_delim = false;
  for (size_t i = 0; i < data.size(); ++i) {
    if (need_delim) {
      *result += delim;
    }
    need_delim = true;
    *result += data[i];
  }
}

int SafeAtoi(const string& data) {
  char *end_ptr;
  CHECK(data.size() > 0)
      << "Error: can't convert an empty string to an integer.";
  long result = strtol(data.c_str(), &end_ptr, 10);
  CHECK(*end_ptr == '\0')
      << "Error: string was not a valid integer: " << data;
  // strtol will set the result to LONG_MIN or LONG_MAX if the value was outside
  // the acceptable range.
  if (result == LONG_MAX || result == LONG_MIN) {
    CHECK(errno == ERANGE);
    LOG(FATAL) << "Error: abs(" << data << ") too big to convert to int.";
  }
  // We're returning an int which may or may not be the same thing as a long
  // (depends on the platform). Make sure it's safe to do the this.
  CHECK(result >= std::numeric_limits<int>::min())
      << "Error: " << data << " is smaller than can be represented with an int";
  CHECK(result <= std::numeric_limits<int>::max())
      << "Error: " << data << " is larger than can be reprsented with an int.";

  return result;
}

long long SafeAtoll(const string& data) {
  char *end_ptr;
  CHECK(data.size() > 0)
      << "Error: can't convert an empty string to an integer.";
  long long result = strtoll(data.c_str(), &end_ptr, 10);
  CHECK(*end_ptr == '\0')
      << "Error: string was not a valid integer: " << data;
  // strtol will set the result to LONG_MIN or LONG_MAX if the value was outside
  // the acceptable range.
  if (result == LLONG_MAX || result == LLONG_MIN) {
    CHECK(errno == ERANGE);
    LOG(FATAL) << "Error: abs(" << data << ") too big to convert to long long.";
  }

  return result;
}
