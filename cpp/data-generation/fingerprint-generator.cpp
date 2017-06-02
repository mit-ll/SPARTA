//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of FingerprintGenerator
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 18 June 2012  yang           Original Version
//*****************************************************************
#include <iostream>
#include <fstream>

// Uses assert instead of CHECK so we don't have a dependacy on logging which is
// difficult to use with Python wrappers.
#include <cassert>

#include "fingerprint-generator.h"

using namespace std;

FingerprintGenerator::FingerprintGenerator(int mean, int sigma)
    :nd_(mean, sigma), normrand_(rng_, nd_) {
}

void FingerprintGenerator::SetSeed(int seed) {
  rng_.seed(seed);
}

void FingerprintGenerator::GetRandomBits(vector<int>* array) {
  assert(array != NULL);
  assert(array->size() == 0);

  // num_samples will always be a multiple of 32-bits since we are doing
  // integer division. This will on average produce samples that are 16-bits
  // less than the target mean, which is negligible for 100KB bit arrays.
  int num_samples = normrand_() / sizeof(int);
  if (num_samples <= 0) {
    return;
  }
  array->resize(num_samples);
  for (int i = 0; i < num_samples; ++i) {
    (*array)[i] = rng_();
  }
}

// TODO(odain) This is too much common code. It needs to be refactored!
char* FingerprintGenerator::GetRandomBits(int* length) {
  // num_samples will always be a multiple of 32-bits since we are doing
  // integer division. This will on average produce samples that are 16-bits
  // less than the target mean, which is negligible for 100KB bit arrays.
  int num_samples = normrand_() / sizeof(int);
  if (num_samples <= 0) {
    return NULL;
  }
  // Have to use malloc because Python is going to free it.
  char* results = (char*)malloc(num_samples * sizeof(int));
  char* result_ptr = results;
  for (int i = 0; i < num_samples; ++i) {
    // Push an int int the 4 bytes pointed to by result_ptr
    *(reinterpret_cast<int*>(result_ptr)) = rng_();
    // And advance the pointer by 4 bytes.
    result_ptr += sizeof(int);
  }
  assert(result_ptr == (results + num_samples * sizeof(int)));
  *length = num_samples * sizeof(int);
  return results;
}

void FingerprintGenerator::SaveArray(const std::vector<int>& array, 
                                     string filename) const {   
  assert(filename.size() > 0);
  assert(array.size() > 0);

  ofstream writeFile;
  writeFile.open(filename.c_str(), ios::out | ios::binary);
  if (!array.empty())
    writeFile.write((char*)&array[0], array.size() * sizeof(int));
}
