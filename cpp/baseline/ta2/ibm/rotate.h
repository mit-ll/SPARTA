//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        An IBM rotation gate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 17 Sep 2012  yang            Original Version
//*****************************************************************


#ifndef CPP_BASELINE_TA2_IBM_ROTATE_H_
#define CPP_BASELINE_TA2_IBM_ROTATE_H_

#include "unary-gate.h"

// Rotate shifts the bits with wrap around. The rotation occurs in the direction
// from least-significant-bit to most-significant-bit.
class Rotate : public UnaryGate {
 public:

  // Shift the bits in the direction from least-significant-bit to
  // most-significant-bit.
  virtual BitArray EvaluateImpl(); 

  // Rotate overloads the SetConstant method to take in integer input which
  // specifies how many bits the output is rotated by.
  void SetConstant(int c) { num_rotate_ = c; }

 private:

  // Number of bits to rotate in the direction of LSB to MSB.
  int num_rotate_;
};

#endif
