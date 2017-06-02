//*****************************************************************
// Copyright 2015 MIT Lincoln Laboratory  
// Project:            SPAR
// Authors:            Yang
// Description:        Implementation of Rotate 
//
// Modifications:
// Date          Name           Modification
// ----          ----           ------------
// 24 Sep 2012  yang            Original Version
//*****************************************************************


#include "rotate.h"

BitArray Rotate::EvaluateImpl() {
    boost::dynamic_bitset<> bits = input()->Evaluate();
    int size = bits.size();
    boost::dynamic_bitset<> rotated_bits(size);
    for (int i = 0; i < size; ++i) {
      rotated_bits[(i+num_rotate_) % size] = bits[i];
    }
    return rotated_bits;
}
