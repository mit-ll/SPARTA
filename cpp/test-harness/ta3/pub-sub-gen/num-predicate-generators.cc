//*****************************************************************
// Copyright 2013 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            OMD
// Description:        Implmentation of the num predicate generators 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 29 Jan 2013   omd            Original Version
//*****************************************************************

#include "num-predicate-generators.h"

#include <algorithm>
#include "common/check.h"

TruncatedPoissonNumGenerator::TruncatedPoissonNumGenerator(
    int mean, int seed) : rng_(seed), dist_(mean) {
}

int TruncatedPoissonNumGenerator::operator()(int max) {
  int value = dist_(rng_);
  value = std::max(value, 1);
  value = std::min(value, max);
  return value;
}

int TruncatedPoissonNumGenerator::operator()() {
  int value = dist_(rng_);
  value = std::max(value, 1);
  return value;
}

ConstantNumGenerator::ConstantNumGenerator(
    int value) : value_(value) {
}

int ConstantNumGenerator::operator()(int max) {
  DCHECK(value_ <= max);
  return value_;
}

int ConstantNumGenerator::operator()() {
  return value_;
}

CoinTossNumGenerator::CoinTossNumGenerator(
    int heads, int tails, float prob, int seed) : 
  rng_(seed), dist_(0.0, 1.0), 
  heads_(heads), tails_(tails), prob_(prob) {
}

int CoinTossNumGenerator::operator()(int max) {
  DCHECK(heads_ <= max);
  DCHECK(tails_ <= max);
  float value = dist_(rng_);
  if (value <= prob_) {
    return heads_;
  } else {
    return tails_;
  }
}

int CoinTossNumGenerator::operator()() {
  float value = dist_(rng_);
  if (value <= prob_) {
    return heads_;
  } else {
    return tails_;
  }
}
