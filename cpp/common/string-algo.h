//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Various string processing algorithms. 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 09 May 2012   omd            Original Version
//*****************************************************************

#ifndef CPP_COMMON_STRING_ALGO_H_
#define CPP_COMMON_STRING_ALGO_H_

#include <string>
#include <vector>

#include "check.h"

/// Split source into at most max_results pieces by delimited. Return those
/// pieces by appending them to result. If max_results == -1, then source will be
/// split at all occurring delimiters.
void Split(const std::string& source, char delimiter,
           std::vector<std::string>* result, int max_results = -1);

/// Overloaded version of the above Split. May be less efficient as the compiler
/// may not be smart enough to avoid copying the entire vector into the result.
inline std::vector<std::string> Split(const std::string& source,
                                      char delimiter, int max_results = -1) {
  std::vector<std::string> result;
  Split(source, delimiter, &result, max_results);
  return result;
}

void Join(const std::vector<std::string>& data, const std::string& delim,
                 std::string* result);

inline std::string Join(
    const std::vector<std::string>& data, const std::string& delim) {
  std::string result;
  Join(data, delim, &result);
  return result;
}

/// Just like strdup in <cstring> but uses operator new[] to allocate the new
/// string instead of malloc. This is sometimes important since operator delete
/// shouldn't be used with memory that was allocated via malloc.
char* StrDup(const char* src);

/// Like the common, but non-standard, itoa function, this returns a string
/// representation of an integer.
std::string itoa(int x);

/// Like atoi or strtol but safe. This converts it's argument to an int and CHECK
/// fails if the passed string does not consist soley of an integer value.
/// TODO(njhwang) deprecate this in favor of ConvertString
int SafeAtoi(const std::string& data);

/// Same as the above, but outputs a long long instead of an int
/// TODO(njhwang) deprecate this in favor of ConvertString
long long SafeAtoll(const std::string& data);

/// Converts a string to all uppercase. The conversion happens in-place.
void ToUpper(std::string* str);

/// Converts a string to all lowercase. The conversion happens in-place.
void ToLower(std::string* str);

/// Converts a string to type T, if possible.
template< typename T >
inline std::string ConvertNumeric(T number) {
  std::ostringstream out;
  out << number;
  return out.str();
}

template< typename T >
inline T ConvertString(const std::string& str) {
  std::istringstream iss(str);
  T obj;

  iss >> std::ws >> obj >> std::ws;

  if (!iss.eof()) {
    LOG(ERROR) << __PRETTY_FUNCTION__;
    LOG(ERROR) << "Error converting string to " << typeid(T).name();
    LOG(FATAL) << "Error: string could not be converted: " << str;
  }

  return obj;
}

#endif
